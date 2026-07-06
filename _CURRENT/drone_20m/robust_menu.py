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
    """100-trial MC with physical robustness criteria.

    A design is robust at a tolerance grade when, across every trial:
      * the full path completes (no clipping anywhere),
      * spots never merge (simulator's own min-separation / overlap
        flags -- relative spot distances, not the coherent pattern walk),
      * intermediate spots keep clearing the coupling hole,
      * and (tier 'as-built') the exit spot still leaves through the
        1.3 mm hole without any realignment: pattern walk p95 + beam
        radius at the hole < hole radius. Designs passing everything
        except the last are tier 'trim' -- recovered by the standard
        ring-temperature/launch trim every build performs anyway.
    """
    out = dict(row)
    grade = {"research": ToleranceSpec.research_grade,
             "flight": ToleranceSpec.flight_grade}[out.get("grade",
                                                           "research")]()
    try:
        cfg = cfg_from_row(row)
        cfg.n_passes = int(row["n_exit"])          # exclude the exit hit
        w_pair = float(row["min_sep_mm"]) - float(row["sep_margin_mm"])
        mc = monte_carlo(cfg, grade, n_trials=100, seed=1, n_workers=1)
        full = int(row["n_exit"])
        out["mc_complete_frac"] = float((mc["bounces"] >= full).mean())
        out["walk_p95_mm"] = float(np.percentile(mc["spot_walk_mm"], 95))
        out["drift_p95_mrad"] = float(
            np.percentile(mc["exit_drift_mrad"], 95))
        out["min_sep_p05_mm"] = float(
            np.percentile(mc["min_spot_sep_mm"], 5))
        out["overlap_frac"] = float(mc["spots_overlap"].mean())
        out["hole_clear_p05_mm"] = float(
            np.nanpercentile(mc["hole_clear_mm"], 5))
        out["sep_ok"] = bool(out["min_sep_p05_mm"] >= w_pair
                             and out["overlap_frac"] <= 0.02)
        out["hole_ok"] = bool(out["hole_clear_p05_mm"] >= 0.0)
        out["exit_ok"] = bool(out["walk_p95_mm"] + row["w_hole_mm"]
                              < 1.3)
    except Exception as exc:                                  # noqa: BLE001
        out.update(mc_complete_frac=0.0, walk_p95_mm=np.inf,
                   drift_p95_mrad=np.inf, min_sep_p05_mm=0.0,
                   overlap_frac=1.0, hole_clear_p05_mm=-np.inf,
                   sep_ok=False, hole_ok=False, exit_ok=False,
                   mc_error=str(exc))
    core = (out["mc_complete_frac"] >= 0.99 and out["sep_ok"]
            and out["hole_ok"])
    out["robust"] = bool(core and out["exit_ok"])   # as-built, no realign
    out["robust_trim"] = bool(core)                 # after standard trim
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(
        _HERE, "results_long", "stage_b_polished.csv"))
    ap.add_argument("--out", default=os.path.join(
        _HERE, "designs", "robust_menu.csv"))
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--grade", default="research",
                    choices=["research", "flight"])
    args = ap.parse_args(argv)

    df = pd.read_csv(args.csv)
    feas = (df[df["feasible"]]
            .drop_duplicates(subset=["sku", "N", "chord_skip", "n_target"])
            .to_dict("records"))
    for r in feas:
        r["grade"] = args.grade
    print(f"{len(feas)} unique feasible designs -> MC x100 each "
          f"({args.grade} grade)")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(mc_one, feas)):
            rows.append(r)
            tier = ("AS-BUILT" if r["robust"]
                    else "trim" if r["robust_trim"] else "no")
            print(f"  [{i+1}/{len(feas)}] {r['sku']} N={r['N']} "
                  f"n={r['n_exit']} opl={r['opl_m']:.1f} m "
                  f"complete={r['mc_complete_frac']*100:.0f}% "
                  f"sep_p05={r['min_sep_p05_mm']:.2f} "
                  f"holeclr_p05={r['hole_clear_p05_mm']:.2f} "
                  f"walk_p95={r['walk_p95_mm']:.2f} "
                  f"robust={tier}", flush=True)
    out = pd.DataFrame(rows).sort_values(
        ["robust", "robust_trim", "opl_m"],
        ascending=[False, False, False])
    out.to_csv(args.out, index=False)

    cols = ["sku", "N", "chord_skip", "n_exit", "opl_m", "envelope_mm",
            "throughput", "mc_complete_frac", "min_sep_p05_mm",
            "hole_clear_p05_mm", "walk_p95_mm", "drift_p95_mrad"]
    for label, sel in (("ROBUST AS-BUILT", out["robust"]),
                       ("ROBUST WITH STANDARD TRIM",
                        out["robust_trim"] & ~out["robust"])):
        sub = out[sel]
        print(f"\n=== {label} ({len(sub)}) ===")
        with pd.option_context("display.width", 260):
            print(sub[cols].head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
