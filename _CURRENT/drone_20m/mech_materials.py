"""Construction-tolerance and materials study (professor, 2026-07-08).

Answers, with numbers from our own Monte-Carlo machinery plus parametric
mass/stiffness models:

  * weight of the assembly in Al 6061, Ti-6Al-4V, invar, PA12 (MJF/SLS),
    PLA (FDM), tough SLA resin, CF-PA12;
  * first vibration mode of the lid (edge-clamped circular plate) per
    material vs the multirotor excitation band;
  * thermal ring window scaled by CTE (measured Al windows from
    investigations.md: drone_20m +-26 K, drone_25m +-20 K, drone_16cm
    +-8 K), plus PA12 moisture swelling converted to an equivalent
    ring-radius error;
  * CONSTRUCTION-TOLERANCE Monte-Carlo: per manufacturing process we map
    published dimensional capability onto our ToleranceSpec (seat
    flatness/25.4 mm -> mirror tilt sigma; positional accuracy ->
    decentre; radial accuracy -> R_ring) and run the exact-trace MC.
    Verdict: does the full path complete, do spots stay separated, does
    the beam still exit the 1.3 mm hole -- as built, per process.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mech_materials.py [--workers 2]
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

# ---------------------------------------------------------------------------
# materials:  E [GPa], rho [g/cc], CTE [ppm/K], notes
# ---------------------------------------------------------------------------
MATERIALS = {
    "Al 6061 (CNC)":      dict(E=68.9, rho=2.70, cte=23.6),
    "Ti-6Al-4V":          dict(E=113.8, rho=4.43, cte=8.6),
    "Invar 36 (ring)":    dict(E=141.0, rho=8.05, cte=1.2),
    "Mg AZ31B":           dict(E=45.0, rho=1.78, cte=26.0),
    "PA12 (MJF/SLS)":     dict(E=1.8, rho=1.01, cte=100.0),
    "PA12-CF (MJF)":      dict(E=3.8, rho=1.06, cte=60.0),
    "PLA (FDM)":          dict(E=3.5, rho=1.24, cte=68.0),
    "Tough resin (SLA)":  dict(E=2.8, rho=1.18, cte=75.0),
}

# measured aluminium thermal windows (investigations.md, ring trim frozen)
AL_WINDOW_K = {"drone_20m": 26.0, "drone_25m": 20.0, "drone_16cm": 8.0}

# manufacturing capability -> ToleranceSpec mapping
#   tilt sigma  = seat flatness error / 25.4 mm seat  [mrad]
#   lateral/axial from positional accuracy; R_ring from radial accuracy
PROCESS_GRADES = {
    # process:      tilt[mrad] lat[mm] ax[mm] Rring[mm]  cost USD (one-off,
    #                                                     180 mm disc class)
    "CNC precision (flight)": dict(tilt=0.1, lat=0.010, ax=0.020,
                                   rring=0.020, cost="600-1200"),
    "CNC standard":           dict(tilt=0.5, lat=0.050, ax=0.100,
                                   rring=0.100, cost="250-600"),
    "SLA (tough resin)":      dict(tilt=1.5, lat=0.080, ax=0.100,
                                   rring=0.150, cost="60-150"),
    "MJF/SLS (PA12)":         dict(tilt=2.5, lat=0.150, ax=0.200,
                                   rring=0.250, cost="80-200"),
    "FDM (PLA/PETG)":         dict(tilt=4.0, lat=0.200, ax=0.300,
                                   rring=0.300, cost="20-60"),
    "printed + machined seats": dict(tilt=0.3, lat=0.050, ax=0.080,
                                     rring=0.100, cost="150-350"),
}

MIRROR_G = 20.0
OPTICS_G = 80.0
PLATE_T = 4.0            # base/lid [mm]
WALL_H = 30.6            # ring wall height: mirror 25.4 + seal 5.2 [mm]


def housing_mass_g(envelope_mm: float, r_ring_mm: float, n_mirrors: int,
                   rho: float) -> float:
    r_od = envelope_mm / 2.0
    v_plates = 2.0 * np.pi * r_od ** 2 * PLATE_T
    v_wall = np.pi * (r_od ** 2 - r_ring_mm ** 2) * WALL_H
    v_mm3 = v_plates + v_wall
    return float(v_mm3 * 1e-3 * rho + n_mirrors * MIRROR_G + OPTICS_G)


def lid_first_mode_hz(envelope_mm: float, mat: dict,
                      t_mm: float = PLATE_T) -> float:
    """Edge-clamped circular plate fundamental: f = (10.22/2pi) t/a^2 *
    sqrt(E / (12 (1-nu^2) rho))."""
    a = envelope_mm / 2.0 * 1e-3
    t = t_mm * 1e-3
    E = mat["E"] * 1e9
    rho = mat["rho"] * 1e3
    nu = 0.33
    return float(10.22 / (2 * np.pi) * t / a ** 2
                 * np.sqrt(E / (12 * (1 - nu ** 2) * rho)))


def spec_for(p: dict) -> ToleranceSpec:
    return ToleranceSpec(
        sigma_tilt=p["tilt"], sigma_d_lateral=p["lat"],
        sigma_d_axial=p["ax"], sigma_dR=1.0, sigma_R_ring=p["rring"],
        sigma_input_pos=0.05, sigma_input_tilt=0.5)


def mc_task(task: dict) -> dict:
    row, proc, p = task["row"], task["proc"], task["p"]
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    w_pair = float(row["min_sep_mm"]) - float(row["sep_margin_mm"])
    out = {"design": task["name"], "process": proc, "cost_usd": p["cost"],
           "tilt_mrad": p["tilt"], "rring_mm": p["rring"]}
    try:
        mc = monte_carlo(cfg, spec_for(p), n_trials=100, seed=1, n_workers=1)
        full = int(row["n_exit"])
        out["complete_frac"] = float((mc["bounces"] >= full).mean())
        out["min_sep_p05_mm"] = float(np.percentile(mc["min_spot_sep_mm"], 5))
        out["hole_clear_p05_mm"] = float(
            np.nanpercentile(mc["hole_clear_mm"], 5))
        out["walk_p95_mm"] = float(np.percentile(mc["spot_walk_mm"], 95))
        out["sep_ok"] = bool(out["min_sep_p05_mm"] >= w_pair)
        out["hole_ok"] = bool(out["hole_clear_p05_mm"] >= 0.0)
        out["exit_ok"] = bool(out["walk_p95_mm"]
                              + float(row["w_hole_mm"]) < 1.3)
        out["survives"] = bool(out["complete_frac"] >= 0.99
                               and out["sep_ok"] and out["hole_ok"]
                               and out["exit_ok"])
    except Exception as exc:                                   # noqa: BLE001
        out.update(complete_frac=0.0, survives=False, mc_error=str(exc))
    return out


def load_designs() -> dict:
    """Headline standard-build design + compact flight star."""
    picks = {}
    for f, want in (("robust_menu.csv",
                     [("CM254-150-M01", 16, 144, "drone_20m (20.4 m)")]),
                    ("robust_menu_flight.csv",
                     [("CM254-500-M01", 12, 204, "drone_14cm (20.7 m)"),
                      ("CM254-750-M01", 12, 204, "drone_29m (29.0 m)")])):
        p = os.path.join(_HERE, "designs", f)
        d = pd.read_csv(p)
        for sku, n_mir, n_exit, name in want:
            m = d[(d["sku"] == sku) & (d["N"] == n_mir)
                  & (d["n_exit"] == n_exit)]
            if len(m):
                picks[name] = m.iloc[0].to_dict()
    return picks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    designs = load_designs()

    # ---- mass + stiffness + thermal table --------------------------------
    mat_rows = []
    for name, row in designs.items():
        env, rr, n_mir = (float(row["envelope_mm"]), float(row["R_ring"]),
                          int(row["N"]))
        base_key = ("drone_20m" if "20m" in name.replace(" ", "")
                    else "drone_25m" if "29m" in name else "drone_16cm")
        wk_al = AL_WINDOW_K.get(base_key)
        for mat, mp in MATERIALS.items():
            wk = (wk_al * 23.6 / mp["cte"]) if wk_al else np.nan
            # PA12 moisture swelling 0.10-0.25 % linear (50 % RH .. sat)
            swell_um = (rr * 1e3 * 0.0015 if "PA12" in mat and
                        "CF" not in mat else
                        rr * 1e3 * 0.0008 if "PA12" in mat else 0.0)
            mat_rows.append({
                "design": name, "material": mat,
                "mass_g": round(housing_mass_g(env, rr, n_mir, mp["rho"])),
                "lid_f1_hz": round(lid_first_mode_hz(env, mp)),
                "thermal_window_K": (round(wk, 1) if np.isfinite(wk)
                                     else np.nan),
                "moisture_dRring_um": round(swell_um, 0),
            })
    mat_df = pd.DataFrame(mat_rows)
    mat_df.to_csv(os.path.join(_HERE, "designs",
                               "materials_table.csv"), index=False)
    with pd.option_context("display.width", 200):
        print(mat_df.to_string(index=False))

    # ---- construction-tolerance MC ---------------------------------------
    tasks = [{"row": row, "name": name, "proc": proc, "p": p}
             for name, row in designs.items()
             for proc, p in PROCESS_GRADES.items()]
    print(f"\nconstruction-tolerance MC: {len(tasks)} runs x100 trials")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(mc_task, tasks)):
            rows.append(r)
            print(f"  [{i+1}/{len(tasks)}] {r['design']:22s} "
                  f"{r['process']:26s} complete="
                  f"{r.get('complete_frac', 0)*100:5.0f}%  "
                  f"survives={r.get('survives', False)}", flush=True)
    mc_df = pd.DataFrame(rows)
    mc_df.to_csv(os.path.join(_HERE, "designs",
                              "construction_tolerance.csv"), index=False)
    print("\nwrote designs/materials_table.csv, "
          "designs/construction_tolerance.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
