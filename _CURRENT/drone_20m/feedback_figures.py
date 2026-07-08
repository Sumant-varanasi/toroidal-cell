"""Paper figure set for the professor-feedback round (2026-07-08).

Writes into drone_20m/designs/figures/:

  drone_24m_h2_{cell3d,constellations,experiment}[_paper].png
  drone_27m_{cell3d,constellations,experiment}[_paper].png
  overlap_coupling.png        graded spot-overlap criterion, all pairs
  volume_pvr_comparison.png   OPL vs gas volume vs published cells
  construction_tolerance.png  MC completion per manufacturing process
  trigas_matrix.png           robustness matrix CH4/NH3/H2 (flight build)
  cad_tmpc_{14cm,20m,29m}.png shaded housing renders from the STLs

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/feedback_figures.py [--skip-3d]
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from paper_figures import whiten, png                              # noqa: E402
from spec_asbuilt import cfg_from_row                              # noqa: E402
from tmpc_platform_v5 import simulate_tmpc                         # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints             # noqa: E402
from tmpc_platform_v5.presets import get_preset                    # noqa: E402
from tmpc_platform_v5 import viz3d, render                         # noqa: E402

FIG = os.path.join(_HERE, "designs", "figures")
os.makedirs(FIG, exist_ok=True)

NEW_PRESETS = ("drone_24m_h2", "drone_27m")


# ---------------------------------------------------------------------------
# 1. 3-D path / constellation / experiment renders for the new designs
# ---------------------------------------------------------------------------
def new_design_3d():
    for preset in NEW_PRESETS:
        cfg = get_preset(preset)
        res = simulate_tmpc(cfg)
        print(f"[{preset}] {res.opl*1e-3:.2f} m, {res.bounces} bounces")
        cell = viz3d.build_cell_figure(res, cfg, label=preset)
        png(cell, os.path.join(FIG, f"{preset}_cell3d.png"))
        png(whiten(cell), os.path.join(FIG, f"{preset}_cell3d_paper.png"))
        const = viz3d.build_constellations(
            cfg, res.spot_pattern, res.mirror_sequence, "raytrace")
        png(const, os.path.join(FIG, f"{preset}_constellations.png"),
            width=1200, height=980)
        png(whiten(const),
            os.path.join(FIG, f"{preset}_constellations_paper.png"),
            width=1200, height=980)
        _, exp = render.render_experiment(
            res, cfg, os.path.join(FIG, f"{preset}_experiment.html"),
            family="one_inch", return_fig=True)
        png(exp, os.path.join(FIG, f"{preset}_experiment.png"))
        png(whiten(exp), os.path.join(FIG, f"{preset}_experiment_paper.png"))


# ---------------------------------------------------------------------------
# 2. graded spot-overlap criterion figure
# ---------------------------------------------------------------------------
MENU_LABELS = {
    ("CM254-750-M01", 12, 204): ("29.0 m  Ø183", "#c44536"),
    ("CM254-200-M01", 16, 176): ("24.8 m  Ø180", "#e07a5f"),
    ("CM254-500-M01", 12, 204): ("20.7 m  Ø141", "#2a9d8f"),
    ("CM254-150-M01", 16, 144): ("20.4 m  Ø180", "#1f77b4"),
    ("CM254-150-M01", 13, 143): ("16.6 m  Ø160", "#8a5fbf"),
    ("CM254-150-M01", 10, 190): ("14.9 m  Ø133", "#b08968"),
    ("CM254-250-M01", 12, 132): ("13.6 m  Ø143", "#6c757d"),
}
H2_KEY = ("CM254-200-M01", 16, 176, 69.01)


def load_menu_rows():
    rows, seen = [], set()
    for f, lam in (("robust_menu.csv", 1654.0),
                   ("robust_menu_flight.csv", 1654.0),
                   ("robust_menu_h2_flight.csv", 2121.8)):
        p = os.path.join(_HERE, "designs", f)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        d = d[d["robust"] | d["robust_trim"]]
        for _, r in d.iterrows():
            key = (r["sku"], int(r["N"]), int(r["n_exit"]),
                   round(float(r["R_ring"]), 0))
            if key in seen:
                continue
            seen.add(key)
            row = r.to_dict()
            row["lambda_nm"] = lam
            k3 = key[:3]
            if abs(key[3] - 69.01) < 0.05 and k3 == H2_KEY[:3]:
                row["_label"], row["_color"] = "23.8 m  Ø174 (H2)", "#264653"
            elif k3 in MENU_LABELS:
                row["_label"], row["_color"] = MENU_LABELS[k3]
            else:
                continue
            rows.append(row)
    return rows


def pair_cloud(row):
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    cfg.wavelength = row["lambda_nm"] * 1e-6
    res = simulate_tmpc(cfg)
    n = res.bounces
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    w_hit = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    foot = mirror_footprints(hits, mseq, cfg)
    d_over_w, eta = [], []
    for m, arr in foot.items():
        if len(arr) < 2:
            continue
        uv = arr[:, :2]
        ws = w_hit[np.clip(arr[:, 2].astype(int), 0, len(w_hit) - 1)]
        for i in range(len(uv)):
            for j in range(i + 1, len(uv)):
                d = float(np.hypot(*(uv[i] - uv[j])))
                wi, wj = float(ws[i]), float(ws[j])
                s2 = wi * wi + wj * wj
                d_over_w.append(d / (0.5 * (wi + wj)))
                eta.append((2 * wi * wj / s2) * np.exp(-d * d / s2))
    return np.asarray(d_over_w), np.asarray(eta)


def overlap_coupling():
    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=200)
    x = np.linspace(0.05, 8, 400)
    ax.plot(x, np.exp(-x * x / 2.0), color="#999999", lw=1.2, ls="--",
            label=r"equal-$w$ curve  $\eta=e^{-d^2/2w^2}$")
    for row in load_menu_rows():
        dw, eta = pair_cloud(row)
        ax.scatter(dw, eta, s=8, alpha=0.25, color=row["_color"],
                   edgecolors="none", zorder=2)
        i = int(np.argmax(eta))
        ax.scatter([dw[i]], [eta[i]], s=90, marker="*",
                   color=row["_color"], edgecolor="#222222",
                   linewidth=0.5, zorder=4, label=row["_label"])
    ax.axvspan(0, 2.0, color="#c44536", alpha=0.08)
    ax.text(1.0, 3e-11, "spots touch\n($d<2w$)", ha="center", fontsize=8,
            color="#c44536")
    ax.axhline(1e-2, color="#c44536", lw=0.9, ls=":")
    ax.text(0.15, 1.6e-2, "continuous-fold toroids: mask territory",
            ha="left", fontsize=7.5, color="#c44536")
    ax.axvline(3.45, color="#4a4e69", lw=0.9, ls=":")
    ax.text(3.5, 2e-11, "IRcell-S segment edge (2C·w, C=6.9)",
            rotation=90, va="bottom", fontsize=7, color="#4a4e69")
    ax.set_yscale("log")
    ax.set_xlim(0, 8)
    ax.set_ylim(1e-12, 1.5)
    ax.set_xlabel(r"spot-pair separation  $d/\bar{w}$")
    ax.set_ylabel(r"Gaussian field coupling  $\eta$")
    ax.set_title("Graded spot-overlap criterion — every same-mirror pair, "
                 "every design")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=7.2, loc="upper right", ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "overlap_coupling.png"))
    plt.close(fig)
    print("  -> overlap_coupling.png")


# ---------------------------------------------------------------------------
# 3. volume / PVR literature comparison
# ---------------------------------------------------------------------------
LIT = [
    # name, volume mL, OPL m, marker note
    ("IRcell-4M (2016)", 38, 3.49),
    ("IRcell-S4 (2020)", 31, 4.03),
    ("IRcell-S15 (2020)", 128, 15.12),
    ("Graf 2018 prototype", 140, 9.89),
    ("Tuzson 2013 toroidal", 40, 4.1),
    ("Chang 2020 (2-layer)", 63, 8.3),
    ("Chang 2020 (3-layer)", 94, 10.0),
]


LIT_OFF = {
    "IRcell-4M (2016)": (6, -11, "left"),
    "IRcell-S4 (2020)": (-6, 8, "right"),
    "IRcell-S15 (2020)": (8, -10, "left"),
    "Graf 2018 prototype": (8, -3, "left"),
    "Tuzson 2013 toroidal": (6, 7, "left"),
    "Chang 2020 (2-layer)": (6, -11, "left"),
    "Chang 2020 (3-layer)": (-6, 8, "right"),
}
OUR_OFF = {
    "29.0": (8, 2, "left"), "25.7": (8, 4, "left"),
    "24.8": (8, -8, "left"),
    "23.8": (-9, -13, "right"), "20.7": (-9, 5, "right"),
    "20.4": (8, -5, "left"), "16.6": (8, -11, "left"),
    "15.3": (8, 6, "left"),
    "14.9": (-9, 7, "right"), "13.6": (8, -10, "left"),
    "9.1": (-10, 7, "right"), "9.2": (8, -12, "left"),
    "7.5": (8, -4, "left"),
}


def volume_pvr():
    cm = pd.read_csv(os.path.join(_HERE, "designs", "cell_metrics.csv"))
    cm["_rr"] = cm["R_ring_mm"].round(0)
    cm = cm.drop_duplicates(subset=["sku", "N", "n_exit", "_rr"])
    fig, ax = plt.subplots(figsize=(7.4, 5.0), dpi=200)
    # constant-PVR guides, labelled where they cross the top of the axes
    v = np.array([15, 900])
    for pvr in (25, 50, 100, 200):
        ax.plot(v, pvr * v / 1000.0, color="#dddddd", lw=0.9, zorder=1)
        x_top = 31_000.0 / pvr
        if 28 <= x_top <= 650:
            ax.text(x_top, 30.4, f"{pvr} m/L", fontsize=7,
                    color="#aaaaaa", ha="center")
    for name, vol, opl in LIT:
        dx, dy, ha = LIT_OFF.get(name, (6, -3, "left"))
        ax.scatter(vol, opl, s=55, color="#8d99ae", edgecolor="#444444",
                   linewidth=0.6, zorder=3)
        ax.annotate(name, (vol, opl), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7.3, color="#555555", ha=ha)
    for _, r in cm.iterrows():
        lab = f"{r['opl_m']:.1f} m Ø{r['envelope_mm']:.0f}"
        h2 = abs(r.get("lambda_nm", 1654.0) - 2121.8) < 1
        dx, dy, ha = OUR_OFF.get(f"{r['opl_m']:.1f}"[:4], (7, 3, "left"))
        ax.scatter(r["v_min_ml"], r["opl_m"], s=130, marker="*",
                   color="#2a9d8f" if h2 else "#1f77b4",
                   edgecolor="#0b3948", linewidth=0.6, zorder=4)
        ax.annotate(lab + (" (H2)" if h2 else ""),
                    (r["v_min_ml"], r["opl_m"]),
                    textcoords="offset points", xytext=(dx, dy),
                    fontsize=7.3, color="#0b3948", ha=ha)
    ax.scatter([], [], s=55, color="#8d99ae", edgecolor="#444444",
               label="published circular/toroidal cells")
    ax.scatter([], [], s=130, marker="*", color="#1f77b4",
               edgecolor="#0b3948", label="this work (beam-limited chamber)")
    ax.set_xscale("log")
    ax.set_xlim(20, 700)
    ax.set_ylim(0, 32)
    ax.set_xlabel("gas sample volume [mL]")
    ax.set_ylabel("optical path length [m]")
    ax.set_title("Path vs sample volume — TMPC menu against the "
                 "toroidal/circular literature")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "volume_pvr_comparison.png"))
    plt.close(fig)
    print("  -> volume_pvr_comparison.png")


# ---------------------------------------------------------------------------
# 4. construction-tolerance bars
# ---------------------------------------------------------------------------
def construction_bars():
    df = pd.read_csv(os.path.join(_HERE, "designs",
                                  "construction_tolerance.csv"))
    extra = os.path.join(_HERE, "designs", "construction_tolerance_15m.csv")
    if os.path.exists(extra):
        df = pd.concat([df, pd.read_csv(extra)], ignore_index=True)
    procs = ["CNC precision (flight)", "CNC standard",
             "printed + machined seats", "SLA (tough resin)",
             "MJF/SLS (PA12)", "FDM (PLA/PETG)"]
    designs = list(df["design"].unique())
    fig, axes = plt.subplots(1, len(designs),
                             figsize=(2.8 * len(designs) + 3.0, 4.2),
                             dpi=200, sharey=True)
    for ax, des in zip(axes, designs):
        sub = df[df["design"] == des].set_index("process").loc[procs]
        cols = []
        for _, r in sub.iterrows():
            if r["survives"]:
                cols.append("#2a9d8f")
            elif (r["complete_frac"] >= 0.99 and r["sep_ok"]
                  and r["hole_ok"]):
                cols.append("#e9c46a")
            else:
                cols.append("#c44536")
        y = np.arange(len(procs))[::-1]
        ax.barh(y, sub["complete_frac"] * 100, color=cols,
                edgecolor="#333333", linewidth=0.5, height=0.62)
        for yi, (_, r) in zip(y, sub.iterrows()):
            ax.text(min(r["complete_frac"] * 100 + 2, 98), yi,
                    f"{r['complete_frac']*100:.0f}%", va="center",
                    fontsize=7.5,
                    ha="left" if r["complete_frac"] < 0.9 else "right",
                    color="#222222")
        ax.set_yticks(y)
        ax.set_yticklabels(procs, fontsize=8)
        ax.set_xlim(0, 105)
        ax.set_xlabel("full-path completion [%]", fontsize=8)
        ax.set_title(des, fontsize=9.5)
        ax.grid(alpha=0.3, axis="x")
    handles = [Rectangle((0, 0), 1, 1, color=c) for c in
               ("#2a9d8f", "#e9c46a", "#c44536")]
    fig.legend(handles, ["survives as-built (no realignment)",
                         "completes — needs the standard one-time trim",
                         "fails"], loc="lower center", ncol=3, fontsize=8,
               frameon=False)
    fig.suptitle("Construction tolerance: 100-trial exact-trace Monte-Carlo "
                 "per manufacturing process", fontsize=11)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(FIG, "construction_tolerance.png"))
    plt.close(fig)
    print("  -> construction_tolerance.png")


# ---------------------------------------------------------------------------
# 5. tri-gas robustness matrix
# ---------------------------------------------------------------------------
def trigas_matrix():
    rows = [
        ("29.0 m  Ø183  (drone_29m)", True, True, False),
        ("25.7 m  Ø185  (hardened)", True, True, True),
        ("24.8 m  Ø180  (drone_25m)", True, True, False),
        ("23.8 m  Ø174  (drone_24m_h2)", True, True, True),
        ("20.7 m  Ø141  (drone_14cm)", True, True, True),
        ("20.4 m  Ø180  (drone_20m)", True, True, True),
        ("16.6 m  Ø160", True, True, True),
        ("15.3 m  Ø175  (sparse, 89.5 %)", True, True, True),
        ("14.9 m  Ø133", True, True, True),
        ("13.6 m  Ø143", True, True, True),
    ]
    gases = ("CH4\n1653.7 nm", "NH3\n1512.2 nm", "H2\n2121.8 nm")
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=200)
    for i, (lab, *ok) in enumerate(rows):
        for j, o in enumerate(ok):
            c = "#2a9d8f" if o else "#c44536"
            ax.add_patch(Rectangle((j, len(rows) - 1 - i), 0.94, 0.94,
                                   facecolor=c, alpha=0.85,
                                   edgecolor="white", linewidth=2))
            ax.text(j + 0.47, len(rows) - 1 - i + 0.47,
                    "robust" if o else "—", ha="center", va="center",
                    fontsize=8.5, color="white", fontweight="bold")
    ax.set_xlim(0, 3)
    ax.set_ylim(0, len(rows))
    ax.set_xticks([0.47, 1.47, 2.47])
    ax.set_xticklabels(gases, fontsize=9)
    ax.set_yticks([len(rows) - 1 - i + 0.47 for i in range(len(rows))])
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Tri-gas menu — Monte-Carlo robust as-built at the "
                 "flight-grade build\n(spot sizes scale as √λ; "
                 "H2 is the qualifying case)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "trigas_matrix.png"))
    plt.close(fig)
    print("  -> trigas_matrix.png")


# ---------------------------------------------------------------------------
# 6. CAD renders from the STLs
# ---------------------------------------------------------------------------
def cad_renders():
    import plotly.graph_objects as go
    import trimesh
    cad = os.path.join(_HERE, "designs", "cad")
    for tag in ("tmpc_14cm", "tmpc_20m", "tmpc_29m"):
        parts = [("ring_body", 0.0, "#b8bcc2"),
                 ("base", -14.0, "#8d99ae"),
                 ("lid", 22.0, "#8d99ae")]
        traces = []
        for nm, dz, col in parts:
            p = os.path.join(cad, f"{tag}_{nm}.stl")
            if not os.path.exists(p):
                continue
            m = trimesh.load_mesh(p)
            v, f = m.vertices, m.faces
            traces.append(go.Mesh3d(
                x=v[:, 0], y=v[:, 1], z=v[:, 2] + dz,
                i=f[:, 0], j=f[:, 1], k=f[:, 2],
                color=col, opacity=1.0, flatshading=True,
                lighting=dict(ambient=0.45, diffuse=0.8, specular=0.25,
                              roughness=0.6, fresnel=0.1),
                lightposition=dict(x=250, y=120, z=400), name=nm))
        fig = go.Figure(traces)
        ax = dict(visible=False)
        fig.update_layout(
            scene=dict(xaxis=ax, yaxis=ax, zaxis=ax, aspectmode="data",
                       camera=dict(eye=dict(x=1.35, y=1.1, z=0.75))),
            paper_bgcolor="white", margin=dict(l=0, r=0, t=28, b=0),
            title=dict(text=f"{tag} housing (exploded) — generated from the "
                            "verified design row", font=dict(size=14,
                                                             color="#1a1a1a")))
        png(fig, os.path.join(FIG, f"cad_{tag}.png"), width=1100, height=800)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-3d", action="store_true")
    a = ap.parse_args()
    if not a.skip_3d:
        new_design_3d()
    overlap_coupling()
    volume_pvr()
    construction_bars()
    trigas_matrix()
    cad_renders()
    print("done")
