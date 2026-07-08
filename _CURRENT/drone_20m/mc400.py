"""400-trial paper-grade Monte-Carlo for the round's headline designs.

The 100-trial robust_menu verdicts select the menu; the paper quotes
400-trial statistics (like drone_20m and drone_24m_h2 already have).
This runs flight-grade MC x400 on the three new stars and prints the
paper numbers.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mc400.py
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

PICKS = [
    ("25.7 m tri-gas (spec_D190_26m)", "robust_menu_hardened_flight.csv",
     "CM254-200-M01", 16, 176, 74.5, {}),
    ("15.3 m sparse (spec_D180_15m)", "robust_menu_hardened_flight.csv",
     "CM254-100-M01", 16, 112, 69.6, {}),
    ("9.1 m half-inch mini (spec_D130_9m)",
     "robust_menu_minihole_flight.csv", "CM127-050-M01", 14, 98, 51.6,
     {"TMPC_W0": "0.8", "TMPC_HOLE_R": "0.8"}),
]


def run_one(pick):
    name, menu, sku, n_mir, n_exit, rr, env = pick
    for k, v in env.items():
        os.environ[k] = v
    from spec_asbuilt import cfg_from_row
    from tmpc_platform_v5 import ToleranceSpec
    from tmpc_platform_v5.tolerance import monte_carlo
    d = pd.read_csv(os.path.join(_HERE, "designs", menu))
    m = d[(d["sku"] == sku) & (d["N"] == n_mir) & (d["n_exit"] == n_exit)
          & ((d["R_ring"] - rr).abs() < 0.5)]
    row = m.iloc[0].to_dict()
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    mc = monte_carlo(cfg, ToleranceSpec.flight_grade(), n_trials=400,
                     seed=7, n_workers=1)
    full = int(row["n_exit"])
    out = {
        "design": name,
        "complete_frac": float((mc["bounces"] >= full).mean()),
        "opl_mean_m": float(np.mean(mc["opl_m"])),
        "opl_std_m": float(np.std(mc["opl_m"])),
        "throughput_mean": float(np.mean(mc["throughput"])),
        "walk_p95_mm": float(np.percentile(mc["spot_walk_mm"], 95)),
        "min_sep_p05_mm": float(np.percentile(mc["min_spot_sep_mm"], 5)),
        "hole_clear_p05_mm": float(np.nanpercentile(mc["hole_clear_mm"],
                                                    5)),
        "drift_p95_mrad": float(np.percentile(mc["exit_drift_mrad"], 95)),
    }
    return out


def main() -> int:
    rows = []
    # one pick per single-use pool: the module-level HOLE_R/W0 constants
    # are frozen at first import per process, so env-varying picks must
    # not share workers
    for pick in PICKS:
        with ProcessPoolExecutor(max_workers=1) as ex:
            r = list(ex.map(run_one, [pick]))[0]
            rows.append(r)
            print(f"{r['design']:38s} complete={r['complete_frac']*100:5.1f}%"
                  f" walk_p95={r['walk_p95_mm']:.2f} "
                  f"sep_p05={r['min_sep_p05_mm']:.2f} "
                  f"holeclr_p05={r['hole_clear_p05_mm']:.2f} "
                  f"drift_p95={r['drift_p95_mrad']:.1f} mrad", flush=True)
    out = os.path.join(_HERE, "designs", "mc400_new_designs.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
