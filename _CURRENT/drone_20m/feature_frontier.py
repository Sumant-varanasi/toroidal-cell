"""Feature-frontier ranking across every feasible design ever found.

The professor's criteria are now several: OPL, envelope, throughput,
tolerance tier, gas volume / PVR, spot-overlap (fringe) margin, tri-gas
reach, and build cost class. This script sweeps every stage_b_polished
CSV in the project, dedupes, tags robustness tiers from the MC menus,
exact-traces the pareto-relevant subset for honest volume/overlap
numbers, and writes the champions-per-feature table.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/feature_frontier.py
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from spec_asbuilt import cfg_from_row                             # noqa: E402
from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints            # noqa: E402

MIRROR_DIA = {"one_inch": 25.4, "half_inch": 12.7}
SEAL_CLEAR = 2.6
RES_GLOBS = ("results*", )


def load_all() -> pd.DataFrame:
    frames = []
    for g in RES_GLOBS:
        for d in glob.glob(os.path.join(_HERE, g)):
            p = os.path.join(d, "stage_b_polished.csv")
            if os.path.exists(p):
                df = pd.read_csv(p)
                df["source"] = os.path.basename(d)
                df["lambda_nm"] = 2121.8 if "h2" in d.lower() else 1654.0
                frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["feasible"] == True].copy()                    # noqa: E712
    df["_rr"] = df["R_ring"].round(1)
    df = (df.sort_values("throughput", ascending=False)
            .drop_duplicates(subset=["sku", "N", "chord_skip", "n_exit",
                                     "_rr"]))
    return df


def tier_map() -> dict:
    tiers = {}
    for f, tier in (("robust_menu.csv", "standard-lab"),
                    ("robust_menu_v9deep.csv", "standard-lab"),
                    ("robust_menu_flight.csv", "flight"),
                    ("robust_menu_v9deep_flight.csv", "flight"),
                    ("robust_menu_h2_flight.csv", "flight@H2"),
                    ("robust_menu_halfinch_flight.csv", "flight"),
                    ("robust_menu_halfinch.csv", "standard-lab"),
                    ("robust_menu_hardened.csv", "standard-lab"),
                    ("robust_menu_hardened_flight.csv", "flight"),
                    ("robust_menu_minihole_flight.csv", "flight"),
                    ("robust_menu_minihole.csv", "standard-lab")):
        p = os.path.join(_HERE, "designs", f)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        for _, r in d[d["robust"]].iterrows():
            key = (r["sku"], int(r["N"]), int(r["n_exit"]),
                   round(float(r["R_ring"]), 1))
            order = {"standard-lab": 0, "flight": 1, "flight@H2": 1}
            cur = tiers.get(key)
            if cur is None or order[tier] < order[cur]:
                tiers[key] = tier
    return tiers


def exact_metrics(row: dict) -> dict:
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    cfg.wavelength = float(row.get("lambda_nm", 1654.0)) * 1e-6
    res = simulate_tmpc(cfg)
    n = res.bounces
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    w_hit = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    foot = mirror_footprints(hits, mseq, cfg)
    eta = 0.0
    dw = np.inf
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
                e = (2 * wi * wj / s2) * np.exp(-d * d / s2)
                if e > eta:
                    eta = e
                    dw = d / (0.5 * (wi + wj))
    fam = row.get("family", "one_inch")
    z = hits[:, 2]
    h_beam = float(z.max() - z.min()) + 2 * (3 * float(w_hit.max()) + 1.0)
    v_min = float(np.pi * (cfg.R_ring / 10.0) ** 2 * h_beam / 10.0)
    h_full = (MIRROR_DIA.get(fam, 25.4) + 2 * SEAL_CLEAR) / 10.0
    v_full = float(np.pi * (cfg.R_ring / 10.0) ** 2 * h_full)
    return dict(overlap_amp=eta, worst_dw=dw, v_min_ml=v_min,
                v_full_ml=v_full,
                pvr_min=float(row["opl_m"] / (v_min / 1000.0)))


def main() -> int:
    df = load_all()
    tiers = tier_map()
    df["tier"] = [tiers.get((r["sku"], int(r["N"]), int(r["n_exit"]),
                             round(float(r["R_ring"]), 1)), "active/nominal")
                  for _, r in df.iterrows()]
    print(f"{len(df)} unique feasible designs "
          f"({(df['tier'] != 'active/nominal').sum()} MC-robust)")

    # exact metrics for the interesting subset: all robust + pareto shell
    take = df[df["tier"] != "active/nominal"].copy()
    shell = df.sort_values("opl_m", ascending=False).groupby(
        df["envelope_mm"].round(-1)).head(2)
    subset = (pd.concat([take, shell])
              .drop_duplicates(subset=["sku", "N", "chord_skip",
                                       "n_exit", "_rr"]))
    print(f"exact-tracing {len(subset)} designs for volume/overlap...")
    ex = []
    for _, r in subset.iterrows():
        try:
            ex.append(dict(r, **exact_metrics(r.to_dict())))
        except Exception as e:                                 # noqa: BLE001
            print("  skip", r["sku"], int(r["N"]), int(r["n_exit"]), e)
    xdf = pd.DataFrame(ex)
    out_csv = os.path.join(_HERE, "designs", "feature_frontier.csv")
    xdf.to_csv(out_csv, index=False)

    def champ(frame, col, best="max", note=""):
        f = frame if len(frame) else xdf
        r = (f.loc[f[col].idxmax()] if best == "max"
             else f.loc[f[col].idxmin()])
        return (f"| **{note or col}** | {r['sku']} ×{int(r['N'])} "
                f"(skip {int(r['chord_skip'])}, n={int(r['n_exit'])}) | "
                f"{r['opl_m']:.2f} m | Ø{r['envelope_mm']:.0f} | "
                f"{r['throughput']*100:.1f} % | {r['v_min_ml']:.0f} mL | "
                f"{r['pvr_min']:.0f} m/L | {r['worst_dw']:.2f} | "
                f"{r['tier']} |")

    rob = xdf[xdf["tier"] != "active/nominal"]
    lines = [
        "# Feature frontier — champions per criterion",
        "",
        "*(auto-generated by `feature_frontier.py`; exact-trace metrics; "
        "robust = 100-trial MC as-built at the stated tier)*",
        "",
        "| feature | design | OPL | envelope | T@0.999 | V_min | PVR | "
        "worst pair d/w̄ | tier |",
        "|---|---|---|---|---|---|---|---|---|",
        champ(rob, "opl_m", "max", "longest path (robust)"),
        champ(rob, "envelope_mm", "min", "smallest envelope (robust)"),
        champ(rob, "throughput", "max", "highest throughput (robust)"),
        champ(rob, "v_min_ml", "min", "lowest gas volume (robust)"),
        champ(rob, "pvr_min", "max", "best path-per-volume (robust)"),
        champ(rob, "worst_dw", "max", "largest fringe margin (robust)"),
        champ(xdf, "opl_m", "max", "longest path (any, active tier)"),
        champ(xdf, "pvr_min", "max", "best PVR (any)"),
        "",
        "## Top 20 robust designs (by OPL)",
        "",
        "| design | OPL | envelope | T@0.999 | V_min | PVR | d/w̄ | tier |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in rob.sort_values("opl_m", ascending=False).head(20).iterrows():
        lines.append(
            f"| {r['sku']} ×{int(r['N'])} n={int(r['n_exit'])} | "
            f"{r['opl_m']:.2f} m | Ø{r['envelope_mm']:.0f} | "
            f"{r['throughput']*100:.1f} % | {r['v_min_ml']:.0f} mL | "
            f"{r['pvr_min']:.0f} m/L | {r['worst_dw']:.2f} | {r['tier']} |")
    md = os.path.join(_HERE, "designs", "feature_frontier.md")
    with open(md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out_csv} and {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
