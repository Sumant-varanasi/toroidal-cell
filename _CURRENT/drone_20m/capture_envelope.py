"""Input-drift capture envelope per design (Benoy acceptance model, 2026-07-08).

The professor's "final algorithm": a design is good if, for an input
spot-position drift or input angle drift, the beam still exits the exit
hole with decent clearance. This script measures exactly that, per
design and per launch degree of freedom, by bisection:

    max |delta| on each of {offset_t, offset_z, angle_t, angle_s}
    such that (a) the full path completes with no clipping,
              (b) every pre-exit visit to mirror 0 clears the hole,
              (c) the exit spot leaves the hole with clearance >= 0
                  (beam edge inside the hole rim).

Outputs designs/capture_envelope.csv: the +/- capture per DOF, the
radial position capture P_cap = min|offset captures|, angle capture
Th_cap = min|angle captures| (mrad), plus pass/fail against the
alignment-residual + drone-drift demand of the prof's framework
(easy regime + Al-flexure drone vector, and medium regime + hybrid
plastic/Al-cartridge vector).

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/capture_envelope.py
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc               # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints               # noqa: E402

DESIGNS = [
    ("D190_26m_trigas", "design_spec_D190_26m.json"),
    ("D160_27m", "design_spec_D160_27m.json"),
    ("D180_24m_H2", "design_spec_D180_24m_H2.json"),
    ("D180_15m_sparse", "design_spec_D180_15m_sparse.json"),
    ("D130_9m_halfinch", "design_spec_D130_9m_halfinch.json"),
    ("D190_19m_2inch", "design_spec_D190_19m_2inch.json"),
    ("D190_29m_max", "design_D190_29m.json"),
    ("D150_14cm_flight", "design_D150_14cm.json"),
    ("D180_22m", "design_D180_22m.json"),
]

DOFS = [("input_offset_t", 0.02, 3.0, "mm"),
        ("input_offset_z", 0.02, 3.0, "mm"),
        ("input_angle", 2e-4, 3e-2, "rad"),
        ("input_angle_sag", 2e-4, 3e-2, "rad")]

# Demand vectors from the prof's framework (per-axis maxima, position mm
# / angle mrad): alignment residual regime + drone operational drift of
# the input chain for the named architecture. Conservative arithmetic
# sum, as his worst-case convention.
DEMANDS = {
    # monolithic launch (easy regime 0.02/0.05) + Al-flexure drone drift
    # (0.05 mm / 0.15 mrad)
    "al_flexure": (0.02 + 0.05, 0.05 + 0.15),
    # shimmed/dowel launch (medium 0.05/0.15) + hybrid plastic body +
    # Al cartridge drone drift (0.12 mm / 0.40 mrad)
    "hybrid_plastic": (0.05 + 0.12, 0.15 + 0.40),
}


def load_cfg(fn: str):
    with open(os.path.join(_HERE, "designs", fn), "r", encoding="utf-8") as f:
        spec = json.load(f)
    cfg = TMPCConfig(**spec["cfg"])
    n_exit = int(spec["metrics"]["n_exit"])
    cfg.n_passes = n_exit + 2          # allow the exit visit to register
    return cfg, n_exit, spec


def trial_ok(cfg: TMPCConfig, n_exit: int) -> tuple[bool, float]:
    """Trace once; return (passes acceptance, exit clearance mm)."""
    res = simulate_tmpc(cfg)
    n = res.bounces
    if n < n_exit:                     # clipped / lost before the exit
        return False, -np.inf
    foot = mirror_footprints(res.spot_pattern[:n], res.mirror_sequence[:n],
                             cfg)
    if 0 not in foot:
        return False, -np.inf
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    exit_clear = -np.inf
    for u, v, o in foot[0]:
        j = int(o)
        d = float(np.hypot(u - hole[0], v - hole[1]))
        w = float(w_eff[min(j, len(w_eff) - 1)])
        if j == 0:
            continue                   # entrance
        if abs(j - n_exit) <= 1:       # the exit visit
            exit_clear = cfg.hole_radius - (d + w)
        elif j < n_exit and d < cfg.hole_radius + w:
            return False, -np.inf      # early leak into the hole
    return bool(exit_clear >= 0.0), float(exit_clear)


def capture_one_dof(base_cfg_kw: dict, n_exit: int, dof: str,
                    step0: float, cap: float, sign: float) -> float:
    """Doubling bracket + bisection for the capture limit on one DOF."""
    def ok(delta: float) -> bool:
        kw = dict(base_cfg_kw)
        kw[dof] = kw.get(dof, 0.0) + sign * delta
        cfg = TMPCConfig(**kw)
        cfg.n_passes = n_exit + 2
        return trial_ok(cfg, n_exit)[0]

    lo, hi = 0.0, step0
    while ok(hi):
        lo = hi
        hi *= 2.0
        if hi > cap:
            return cap                 # capture beyond the sweep cap
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo


def sweep_design(item):
    name, fn = item
    cfg, n_exit, spec = load_cfg(fn)
    kw = dict(spec["cfg"])
    ok0, clear0 = trial_ok(cfg, n_exit)
    row = dict(design=name, sku=spec.get("sku", ""),
               opl_m=spec["metrics"].get("opl_m", np.nan),
               n_exit=n_exit, hole_r=cfg.hole_radius,
               nominal_ok=ok0, nominal_exit_clear_mm=clear0)
    if not ok0:
        return row
    for dof, step0, cap, unit in DOFS:
        for sgn, tag in ((+1.0, "pos"), (-1.0, "neg")):
            val = capture_one_dof(kw, n_exit, dof, step0, cap, sgn)
            if unit == "rad":
                val *= 1e3             # -> mrad
            row[f"{dof}_{tag}"] = val
    row["P_cap_mm"] = min(row["input_offset_t_pos"],
                          row["input_offset_t_neg"],
                          row["input_offset_z_pos"],
                          row["input_offset_z_neg"])
    row["Th_cap_mrad"] = min(row["input_angle_pos"], row["input_angle_neg"],
                             row["input_angle_sag_pos"],
                             row["input_angle_sag_neg"])
    for arch, (p_dem, th_dem) in DEMANDS.items():
        row[f"pass_{arch}"] = bool(row["P_cap_mm"] >= p_dem
                                   and row["Th_cap_mrad"] >= th_dem)
        row[f"margin_{arch}_pos"] = row["P_cap_mm"] / p_dem
        row[f"margin_{arch}_ang"] = row["Th_cap_mrad"] / th_dem
    return row


def main() -> int:
    print(f"{len(DESIGNS)} designs, 4 DOFs x 2 signs, bisection to "
          f"~1e-3 resolution")
    rows = []
    with ProcessPoolExecutor(max_workers=min(9, len(DESIGNS))) as ex:
        for row in ex.map(sweep_design, DESIGNS):
            rows.append(row)
            if not row.get("nominal_ok"):
                print(f"  {row['design']}: NOMINAL FAILS acceptance "
                      f"(clear={row['nominal_exit_clear_mm']:.3f}) — check")
                continue
            print(f"  {row['design']:<18} opl={row['opl_m']:5.1f} m  "
                  f"P_cap={row['P_cap_mm']:.3f} mm  "
                  f"Th_cap={row['Th_cap_mrad']:.3f} mrad  "
                  f"alflex={'PASS' if row['pass_al_flexure'] else 'fail'}  "
                  f"hybrid={'PASS' if row['pass_hybrid_plastic'] else 'fail'}",
                  flush=True)
    out = os.path.join(_HERE, "designs", "capture_envelope.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
