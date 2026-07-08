"""Tri-gas re-verification of the robust design menu.

The cell geometry (closure, spot positions, OPL, throughput) is set by ray
geometry and is wavelength-independent; only the Gaussian mode scales.  The
cavity eigen-q satisfies q = (Aq+B)/(Cq+D), which fixes the Rayleigh range
z_R independent of wavelength, so every spot radius scales as sqrt(lambda)
with unchanged waist positions.  Re-verifying a design at a new gas line
therefore means: scale the launch waist w0 by sqrt(lambda_new/lambda_ref),
keep the launch geometry, re-run the full exact-trace check matrix, and
re-run the Monte-Carlo robustness verdict (spot separation, hole clearance
and hole exit all get harder at longer wavelength).

Target lines (professor, 2026-07-08):
    NH3  1512.2 nm   (nu1+nu3)         -- easier than CH4 (smaller spots)
    CH4  1653.7 nm   (2nu3 R(4))       -- the design wavelength
    H2   2121.8 nm   ((1-0) S(1) quadrupole) -- hardest: spots +13.3 %

Run from _CURRENT/ (once per wavelength; env must be set before import):
    ../.venv/Scripts/python.exe drone_20m/multigas_verify.py --wavelength-nm 2121.8
    ../.venv/Scripts/python.exe drone_20m/multigas_verify.py --wavelength-nm 1512.2
"""
from __future__ import annotations

import argparse
import os
import sys

# --- wavelength must be pinned in the environment BEFORE importing the
#     search module (module-level constant, inherited by spawned workers) ---
_ap = argparse.ArgumentParser()
_ap.add_argument("--wavelength-nm", type=float, required=True)
_ap.add_argument("--workers", type=int, default=2)
_ap.add_argument("--n-trials", type=int, default=100)
_ap.add_argument("--out", default=None)
ARGS = _ap.parse_args()
LAMBDA_MM = ARGS.wavelength_nm * 1e-6
LAMBDA_REF_MM = 1.654e-3
os.environ["TMPC_WAVELENGTH_MM"] = repr(LAMBDA_MM)

import numpy as np                                                # noqa: E402
import pandas as pd                                               # noqa: E402
from concurrent.futures import ProcessPoolExecutor               # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from search_drone20m import evaluate                              # noqa: E402
from spec_asbuilt import cfg_from_row                             # noqa: E402
from tmpc_platform_v5 import ToleranceSpec                        # noqa: E402
from tmpc_platform_v5.tolerance import monte_carlo                # noqa: E402

SCALE = float(np.sqrt(LAMBDA_MM / LAMBDA_REF_MM))

EVAL_KEYS = ("family", "sku", "roc", "N", "chord_skip", "R_ring", "n_target",
             "mode_s", "input_offset_z", "input_angle", "input_angle_sag",
             "w0_waist", "waist_frac", "envelope_max", "opl_min")


def load_menu() -> list[dict]:
    rows = []
    for f in ("robust_menu.csv", "robust_menu_flight.csv"):
        p = os.path.join(_HERE, "designs", f)
        if os.path.exists(p):
            d = pd.read_csv(p)
            d = d[d["robust"] | d["robust_trim"]]
            d["menu_grade"] = "research" if "flight" not in f else "flight"
            rows.append(d)
    df = pd.concat(rows).drop_duplicates(
        subset=["sku", "N", "chord_skip", "n_exit"], keep="first")
    return df.to_dict("records")


def verify_one(task: dict) -> dict:
    row, grade_name = task["row"], task["grade"]
    out = {"sku": row["sku"], "N": int(row["N"]),
           "chord_skip": int(row["chord_skip"]),
           "n_exit": int(row["n_exit"]), "opl_m": float(row["opl_m"]),
           "envelope_mm": float(row["envelope_mm"]),
           "wavelength_nm": ARGS.wavelength_nm, "grade": grade_name}
    try:
        p = {k: row[k] for k in EVAL_KEYS if k in row}
        p["w0_waist"] = float(np.clip(row["w0_waist"] * SCALE, 0.20, 1.3))
        if "M2" in row and not pd.isna(row["M2"]):
            p["M2"] = float(row["M2"])
        r = evaluate(p)
        out.update(feasible_nominal=bool(r["feasible"]),
                   reason=r.get("reason", ""),
                   w_hole_mm=float(r["w_hole_mm"]),
                   w_max_mm=float(r["w_max_mm"]),
                   min_sep_mm=float(r["min_sep_mm"]),
                   sep_margin_mm=float(r["sep_margin_mm"]),
                   hole_margin_mm=float(r["hole_margin_mm"]),
                   ap_margin_mm=float(r["ap_margin_mm"]),
                   exit_miss_mm=float(r["exit_miss_mm"]),
                   throughput=float(r["throughput"]))
        # Monte-Carlo at the requested build grade
        p_full = dict(row); p_full.update(p)
        cfg = cfg_from_row(p_full)
        cfg.wavelength = LAMBDA_MM
        cfg.n_passes = int(row["n_exit"])
        grade = {"research": ToleranceSpec.research_grade,
                 "flight": ToleranceSpec.flight_grade}[grade_name]()
        mc = monte_carlo(cfg, grade, n_trials=ARGS.n_trials, seed=1,
                         n_workers=1)
        full = int(row["n_exit"])
        w_pair = out["min_sep_mm"] - out["sep_margin_mm"]
        out["mc_complete_frac"] = float((mc["bounces"] >= full).mean())
        out["walk_p95_mm"] = float(np.percentile(mc["spot_walk_mm"], 95))
        out["min_sep_p05_mm"] = float(np.percentile(mc["min_spot_sep_mm"], 5))
        out["overlap_frac"] = float(mc["spots_overlap"].mean())
        out["hole_clear_p05_mm"] = float(
            np.nanpercentile(mc["hole_clear_mm"], 5))
        out["sep_ok"] = bool(out["min_sep_p05_mm"] >= w_pair
                             and out["overlap_frac"] <= 0.02)
        out["hole_ok"] = bool(out["hole_clear_p05_mm"] >= 0.0)
        out["exit_ok"] = bool(out["walk_p95_mm"] + out["w_hole_mm"] < 1.3)
        core = (out["mc_complete_frac"] >= 0.99 and out["sep_ok"]
                and out["hole_ok"])
        out["robust"] = bool(core and out["exit_ok"])
        out["robust_trim"] = bool(core)
    except Exception as exc:                                   # noqa: BLE001
        out.update(feasible_nominal=False, reason=f"error: {exc}",
                   robust=False, robust_trim=False)
    return out


def main() -> int:
    menu = load_menu()
    tasks = [{"row": r, "grade": g}
             for r in menu for g in ("flight", "research")]
    print(f"lambda = {ARGS.wavelength_nm} nm  (w scale x{SCALE:.4f})  "
          f"{len(menu)} designs x 2 grades")
    rows = []
    with ProcessPoolExecutor(max_workers=ARGS.workers) as ex:
        for i, r in enumerate(ex.map(verify_one, tasks)):
            rows.append(r)
            tier = ("AS-BUILT" if r.get("robust")
                    else "trim" if r.get("robust_trim") else "no")
            print(f"  [{i+1}/{len(tasks)}] {r['sku']} N={r['N']} "
                  f"n={r['n_exit']} {r['grade']:8s} "
                  f"nom={'OK' if r.get('feasible_nominal') else 'FAIL'} "
                  f"sep_p05={r.get('min_sep_p05_mm', float('nan')):.2f} "
                  f"holeclr_p05={r.get('hole_clear_p05_mm', float('nan')):.2f} "
                  f"walk_p95={r.get('walk_p95_mm', float('nan')):.2f} "
                  f"robust={tier}", flush=True)
    out_path = ARGS.out or os.path.join(
        _HERE, "designs", f"multigas_{ARGS.wavelength_nm:.1f}nm.csv")
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
