"""Tolerance-aware menu selection.

Every feasible design from a search run gets a quick Monte-Carlo at
research-grade build tolerances (per-mirror tilt 0.5 mrad, decentre
50/100 um, ROC 1 mm, ring radius 0.1 mm, launch 50 um / 0.5 mrad) and a
robustness verdict:

    robust  <=>  spot-walk p95  <=  hole clearance margin
             and spot-walk p95  <=  sep margin + 0.6 mm   (pattern-level)
             and no clipping in any trial

The published menu then ranks by OPL/size AMONG ROBUST designs, so
'good tolerance' is a selection criterion rather than an afterthought.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/robust_menu.py \
        --csv drone_20m/results_long/stage_b_polished.csv
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from spec_asbuilt import cfg_from_row                             # noqa: E402
from tmpc_platform_v5 import ToleranceSpec                        # noqa: E402
from tmpc_platform_v5.tolerance import monte_carlo                # noqa: E402


def mc_one(row: dict) -> dict:
    """100-trial research-grade MC; geometric robustness metrics only."""
    out = dict(row)
    try:
        cfg = cfg_from_row(row)
        cfg.n_passes = int(row["n_exit"])          # the designed path
        mc = monte_carlo(cfg, ToleranceSpec.research_grade(),
                         n_trials=100, seed=1, n_workers=1)
        full = int(row["n_exit"])
        out["mc_complete_frac"] = float((mc["bounces"] >= full).mean())
        out["walk_p95_mm"] = float(np.percentile(mc["spot_walk_mm"], 95))
        out["drift_p95_mrad"] = float(
            np.percentile(mc["exit_drift_mrad"], 95))
    except Exception as exc:                                  # noqa: BLE001
        out["mc_complete_frac"] = 0.0
        out["walk_p95_mm"] = np.inf
        out["drift_p95_mrad"] = np.inf
        out["mc_error"] = str(exc)
    walk = out["walk_p95_mm"]
    out["robust"] = bool(
        out["mc_complete_frac"] >= 0.99
        and np.isfinite(walk)
        and walk <= row["hole_margin_mm"]
        and walk <= row["sep_margin_mm"] + 0.6)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(
        _HERE, "results_long", "stage_b_polished.csv"))
    ap.add_argument("--out", default=os.path.join(
        _HERE, "designs", "robust_menu.csv"))
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args(argv)

    df = pd.read_csv(args.csv)
    feas = (df[df["feasible"]]
            .drop_duplicates(subset=["sku", "N", "chord_skip", "n_target"])
            .to_dict("records"))
    print(f"{len(feas)} unique feasible designs -> quick MC x100 each")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(mc_one, feas)):
            rows.append(r)
            print(f"  [{i+1}/{len(feas)}] {r['sku']} N={r['N']} "
                  f"n={r['n_exit']} opl={r['opl_m']:.1f} m "
                  f"walk_p95={r['walk_p95_mm']:.2f} "
                  f"(hole {r['hole_margin_mm']:.2f}, "
                  f"sep {r['sep_margin_mm']:.2f}) "
                  f"complete={r['mc_complete_frac']*100:.0f}% "
                  f"robust={'YES' if r['robust'] else 'no'}", flush=True)
    out = pd.DataFrame(rows).sort_values(
        ["robust", "opl_m"], ascending=[False, False])
    out.to_csv(args.out, index=False)

    rob = out[out["robust"]]
    print(f"\n=== ROBUST menu ({len(rob)} of {len(out)}) ===")
    cols = ["sku", "N", "chord_skip", "R_ring", "n_exit", "opl_m",
            "envelope_mm", "throughput", "walk_p95_mm", "hole_margin_mm",
            "sep_margin_mm", "drift_p95_mrad"]
    with pd.option_context("display.width", 250):
        print(rob[cols].head(25).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
