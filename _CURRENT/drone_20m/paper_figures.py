"""Publication-style (white) figures for the paper.

Writes into drone_20m/designs/figures/:
    <preset>_cell3d_paper.png         white-theme 3-D beam path
    <preset>_constellations_paper.png white-theme spot constellations
    <preset>_experiment_paper.png     white-theme as-built render
    menu_pareto.png                   OPL vs envelope map of verified designs
    throughput_vs_R.png               T(R) = R^(n-1) curves for the presets

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/paper_figures.py
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.presets import get_preset                   # noqa: E402
from tmpc_platform_v5 import viz3d, render                        # noqa: E402

FIG = os.path.join(_HERE, "designs", "figures")
os.makedirs(FIG, exist_ok=True)

PRESETS = ("drone_20m", "drone_25m", "drone_22m", "drone_16cm")


DARK = "#1a1a1a"
LIGHTS = {"#eaeaea", "#ccc", "#cccccc", "white", "#ffffff", "#fff",
          "#dddddd", "#ddd"}


def whiten(fig):
    """Restyle a dark plotly figure for print (title, colorbars,
    annotations and trace fonts carry explicit light colors)."""
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=DARK),
        title_font=dict(color=DARK),
        legend=dict(bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#cccccc", borderwidth=1,
                    font=dict(color=DARK)),
    )
    if fig.layout.scene:
        ax = dict(backgroundcolor="white", gridcolor="#d8d8d8",
                  zerolinecolor="#bbbbbb",
                  color=DARK, showbackground=True)
        fig.update_scenes(bgcolor="white",
                          xaxis=ax, yaxis=ax, zaxis=ax)
    for a in (fig.layout.annotations or ()):
        if a.font and (a.font.color in LIGHTS or a.font.color is None):
            a.font.color = DARK
    for tr in fig.data:
        tf = getattr(tr, "textfont", None)
        if tf is not None and (tf.color in LIGHTS or tf.color is None):
            try:
                tr.textfont.color = DARK
            except Exception:
                pass
        mk = getattr(tr, "marker", None)
        cb = getattr(mk, "colorbar", None) if mk is not None else None
        if cb is not None and cb.title is not None:
            cb.tickfont = dict(color=DARK)
            cb.title.font = dict(color=DARK)
    # 2-D axes (constellation subplots)
    fig.update_xaxes(color=DARK, gridcolor="#e0e0e0",
                     zerolinecolor="#cccccc")
    fig.update_yaxes(color=DARK, gridcolor="#e0e0e0",
                     zerolinecolor="#cccccc")
    return fig


def png(fig, path, width=1200, height=860):
    fig.write_image(path, width=width, height=height, scale=2)
    print("  ->", os.path.basename(path))


def white_3d():
    for preset in PRESETS:
        cfg = get_preset(preset)
        res = simulate_tmpc(cfg)
        print(f"[{preset}] {res.opl*1e-3:.2f} m")
        cell = whiten(viz3d.build_cell_figure(res, cfg, label=preset))
        png(cell, os.path.join(FIG, f"{preset}_cell3d_paper.png"))
        const = whiten(viz3d.build_constellations(
            cfg, res.spot_pattern, res.mirror_sequence, "raytrace"))
        png(const, os.path.join(FIG, f"{preset}_constellations_paper.png"),
            width=1200, height=980)
        _, exp = render.render_experiment(
            res, cfg, os.path.join(FIG, f"_tmp_{preset}.html"),
            family="one_inch", return_fig=True)
        png(whiten(exp), os.path.join(FIG, f"{preset}_experiment_paper.png"))
        try:
            os.remove(os.path.join(FIG, f"_tmp_{preset}.html"))
        except OSError:
            pass


def menu_pareto(csvs):
    frames = []
    for c in csvs:
        if os.path.exists(c):
            frames.append(pd.read_csv(c))
    df = pd.concat(frames, ignore_index=True)
    df = df[df["feasible"]].copy()
    df["n_refl"] = df["n_exit"] - 1
    df["T999"] = 0.999 ** df["n_refl"]
    df = df.sort_values("opl_m", ascending=False).drop_duplicates(
        subset=["sku", "N", "chord_skip", "n_target"])
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=200)
    sc = ax.scatter(df["envelope_mm"], df["opl_m"],
                    c=df["T999"] * 100, s=70, cmap="viridis",
                    edgecolor="#333333", linewidth=0.6, zorder=3)
    # frontier: max OPL per envelope
    d = df.sort_values("envelope_mm")
    best, bx, by = -1, [], []
    for _, r in d.iterrows():
        if r["opl_m"] > best:
            best = r["opl_m"]
            bx.append(r["envelope_mm"]); by.append(r["opl_m"])
    ax.step(bx, by, where="post", color="#c44536", lw=1.4,
            alpha=0.8, zorder=2, label="Pareto frontier")
    for _, r in df.iterrows():
        if r["opl_m"] >= 20 or r["envelope_mm"] <= 145:
            ax.annotate(f"{int(r['N'])}×{r['sku'].split('-')[1]}",
                        (r["envelope_mm"], r["opl_m"]),
                        textcoords="offset points", xytext=(6, 5),
                        fontsize=7.5, color="#333333")
    ax.axhline(10, color="#888888", ls="--", lw=1)
    ax.text(133, 10.4, "published toroidal record (~10 m demonstrated)",
            fontsize=8, color="#666666")
    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label("transmission at R = 0.999 [%]")
    ax.set_xlabel("assembly envelope diameter [mm]")
    ax.set_ylabel("verified optical path length [m]")
    ax.set_title("Verified design menu — catalogue 1\" mirrors, N = 8–16")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "menu_pareto.png"))
    plt.close(fig)
    print("  -> menu_pareto.png", f"({len(df)} designs)")


def throughput_vs_R():
    fig, ax = plt.subplots(figsize=(7.0, 4.2), dpi=200)
    R = np.linspace(0.965, 0.9995, 400)
    styles = {"drone_20m": ("#1f77b4", "-"), "drone_25m": ("#c44536", "-"),
              "drone_22m": ("#8a5fbf", "-"), "drone_16cm": ("#2a9d8f", "-")}
    for preset in PRESETS:
        cfg = get_preset(preset)
        n_refl = cfg.n_passes - 1
        col, ls = styles[preset]
        ax.plot(R, 100 * R ** n_refl, color=col, ls=ls, lw=2,
                label=f"{preset}  (R^{n_refl})")
    for rv, lab in ((0.97, "catalog gold (conservative)"),
                    (0.985, "protected gold (typ.)"),
                    (0.999, "enhanced / dielectric")):
        ax.axvline(rv, color="#999999", lw=0.9, ls=":")
        ax.text(rv, 92, f" {lab}", rotation=90, va="top", ha="right",
                fontsize=7.5, color="#666666")
    ax.set_xlabel("mirror reflectivity R at 1654 nm")
    ax.set_ylabel("cell transmission T = R$^{n-1}$ [%]")
    ax.set_title("Coating choice sets the photon budget (hole losses ≈ 0)")
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "throughput_vs_R.png"))
    plt.close(fig)
    print("  -> throughput_vs_R.png")


if __name__ == "__main__":
    white_3d()
    menu_pareto([
        os.path.join(_HERE, "designs", "verified_designs.csv"),
        os.path.join(_HERE, "results_deep", "stage_b_polished.csv"),
    ])
    throughput_vs_R()
    print("done")
