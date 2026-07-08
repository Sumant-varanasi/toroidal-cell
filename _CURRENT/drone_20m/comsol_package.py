"""COMSOL mirror-only validation package for the toroidal N-mirror ring.

Ports Benoy's COMSOL Ray-Tracing Validation Protocol (2026-07-08,
mirror-only, no cell body) to the chord-skip ring geometry:

  1. per design, a geometry CSV with every mirror's centre, optical-axis
     normal, sagittal axis, ROC and clear aperture, plus the exact launch
     ray (entry point + unit direction) and the expected pass count /
     path length — everything a COMSOL Geometrical Optics model needs,
     in the platform's native coordinates (ring centre = origin, ring
     plane = z = 0, mirror k at angle 2*pi*k/N);
  2. a perturbation-envelope CSV (alignment regimes + per-architecture
     drone operational-drift vectors) for the parametric sweeps;
  3. a native execution of protocol step 7 (worst-case per-DOF extremes,
     all mirrors coherently at +max then -max, and each launch DOF at
     its box edge) written in the protocol's run-log format, so the
     COMSOL runs have a reference result to reproduce.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/comsol_package.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc               # noqa: E402
from tmpc_platform_v5.physics import (MirrorPerturbation,            # noqa: E402
                                      build_mirror_ring,
                                      _entrance_ray, mirror_footprints)

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

# per-axis maxima: mirror dxy/dz [mm], mirror tilt [mrad],
# launch pos box [mm], launch angle box [mrad]
ARCH = {
    "al_flexure": (0.050, 0.080, 0.15, 0.07, 0.20),
    "hybrid":     (0.120, 0.180, 0.40, 0.17, 0.55),
}
REGIMES = {  # alignment residual vectors (protocol Table III analogue)
    "easy":   (0.02, 0.03, 0.05),
    "medium": (0.05, 0.07, 0.15),
    "hard":   (0.12, 0.18, 0.40),
}


def load_spec(fn):
    with open(os.path.join(_HERE, "designs", fn), "r", encoding="utf-8") as f:
        spec = json.load(f)
    return spec["cfg"], int(spec["metrics"]["n_exit"]), spec["metrics"]


def geometry_rows(name, cfg_kw, n_exit, met):
    cfg = TMPCConfig(**cfg_kw)
    cfg.n_passes = n_exit + 1
    mirrors = build_mirror_ring(cfg)
    ray = _entrance_ray(cfg, mirrors)
    rows = []
    for k, m in enumerate(mirrors):
        rows.append(dict(
            design=name, item=f"mirror_{k}",
            x_mm=m.center[0], y_mm=m.center[1], z_mm=m.center[2],
            nx=m.normal[0], ny=m.normal[1], nz=m.normal[2],
            sagx=m.sag_axis[0], sagy=m.sag_axis[1], sagz=m.sag_axis[2],
            roc_mm=m.R_t, aperture_r_mm=m.aperture,
            hole_r_mm=cfg.hole_radius if k == 0 else 0.0))
    rows.append(dict(
        design=name, item="launch_ray",
        x_mm=ray.origin[0], y_mm=ray.origin[1], z_mm=ray.origin[2],
        nx=ray.direction[0], ny=ray.direction[1], nz=ray.direction[2],
        sagx=cfg.w0, sagy=cfg.wavelength, sagz=float(n_exit),
        roc_mm=met.get("opl_m", np.nan), aperture_r_mm=np.nan,
        hole_r_mm=cfg.hole_radius))
    return rows


def eval_case(cfg_kw, n_exit, perts=None, launch=None):
    kw = dict(cfg_kw)
    if launch:
        for k, v in launch.items():
            kw[k] = kw.get(k, 0.0) + v
    cfg = TMPCConfig(**kw)
    cfg.n_passes = n_exit + 2
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    out = dict(pass_count=int(min(n, n_exit)), path_m=res.opl / 1000.0,
               edge_clear_mm=np.nan, hole_clear_mm=np.nan,
               exit_clear_mm=np.nan)
    if n < n_exit:
        out["result"] = "FAIL(incomplete)"
        return out
    foot = mirror_footprints(res.spot_pattern[:n], res.mirror_sequence[:n],
                             cfg)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg_kw.get("input_offset_z", 0.0)])
    edge, holec, exitc = np.inf, np.inf, -np.inf
    for m, arr in foot.items():
        uv = arr[:, :2]
        ws = w_eff[np.clip(arr[:, 2].astype(int), 0, len(w_eff) - 1)]
        edge = min(edge, float(
            (cfg.mirror_aperture - np.hypot(uv[:, 0], uv[:, 1]) - ws).min()))
        if m == 0:
            for u, v, o in arr:
                j = int(o)
                if j == 0:
                    continue
                d = float(np.hypot(u - hole[0], v - hole[1]))
                w = float(w_eff[min(j, len(w_eff) - 1)])
                if abs(j - n_exit) <= 1:
                    exitc = cfg.hole_radius - (d + w)
                elif j < n_exit:
                    holec = min(holec, d - cfg.hole_radius - w)
    out.update(edge_clear_mm=edge, hole_clear_mm=holec, exit_clear_mm=exitc)
    ok = edge > 0 and holec > 0 and exitc >= 0
    out["result"] = "PASS" if ok else "FAIL(clearance)"
    return out


def runlog_rows(name, cfg_kw, n_exit):
    rows = []

    def add(run_id, env, vector, perts=None, launch=None):
        r = eval_case(cfg_kw, n_exit, perts, launch)
        rows.append(dict(run_id=run_id, environment=env, design=name,
                         perturbation=vector, **r))

    add(f"{name}-NOM", "nominal", "none")
    for arch, (dxy, dz, tilt, lpos, lang) in ARCH.items():
        tilt_r = tilt * 1e-3
        mirror_dofs = [("dtan", dict(d_tan=dxy)), ("dsag", dict(d_sag=dxy)),
                       ("dax", dict(d_ax=dz)),
                       ("tiltt", dict(tilt_tan=tilt_r)),
                       ("tilts", dict(tilt_sag=tilt_r))]
        for dof, kw1 in mirror_dofs:
            for sgn in (+1, -1):
                perts = [MirrorPerturbation(
                    **{k: sgn * v for k, v in kw1.items()})] * int(
                        cfg_kw["N"])
                add(f"{name}-{arch}-M{dof}{'+' if sgn > 0 else '-'}",
                    f"drone/{arch}", f"all mirrors {dof}={sgn:+d}max",
                    perts=perts)
        launch_dofs = [("offt", "input_offset_t", lpos),
                       ("offz", "input_offset_z", lpos),
                       ("angt", "input_angle", lang * 1e-3),
                       ("angs", "input_angle_sag", lang * 1e-3)]
        for dof, key, mag in launch_dofs:
            for sgn in (+1, -1):
                add(f"{name}-{arch}-L{dof}{'+' if sgn > 0 else '-'}",
                    f"drone/{arch}", f"launch {key}={sgn:+d}max",
                    launch={key: sgn * mag})
    return rows


def main() -> int:
    out_dir = os.path.join(_HERE, "designs", "comsol")
    os.makedirs(out_dir, exist_ok=True)

    geom, runlog = [], []
    for name, fn in DESIGNS:
        cfg_kw, n_exit, met = load_spec(fn)
        g = geometry_rows(name, cfg_kw, n_exit, met)
        geom.extend(g)
        pd.DataFrame(g).to_csv(os.path.join(
            out_dir, f"comsol_geom_{name}.csv"), index=False)
        rr = runlog_rows(name, cfg_kw, n_exit)
        runlog.extend(rr)
        n_pass = sum(1 for r in rr if r["result"] == "PASS")
        print(f"{name:<18} geometry rows={len(g) - 1}+launch  "
              f"worst-case runs: {n_pass}/{len(rr)} PASS", flush=True)

    pd.DataFrame(geom).to_csv(os.path.join(out_dir, "comsol_geom_all.csv"),
                              index=False)
    pd.DataFrame(runlog).to_csv(os.path.join(
        out_dir, "comsol_runlog_native.csv"), index=False)

    pert_rows = []
    for reg, (p, pz, a) in REGIMES.items():
        pert_rows.append(dict(kind="alignment_residual", name=reg,
                              dx_mm=p, dy_mm=p, dz_mm=pz,
                              dtheta_mrad=a))
    for arch, (dxy, dz, tilt, lpos, lang) in ARCH.items():
        pert_rows.append(dict(kind="drone_mirror_drift", name=arch,
                              dx_mm=dxy, dy_mm=dxy, dz_mm=dz,
                              dtheta_mrad=tilt))
        pert_rows.append(dict(kind="drone_launch_box", name=arch,
                              dx_mm=lpos, dy_mm=lpos, dz_mm=lpos,
                              dtheta_mrad=lang))
    pd.DataFrame(pert_rows).to_csv(os.path.join(
        out_dir, "comsol_perturbations.csv"), index=False)

    print(f"\nwrote {out_dir}: geom per design + all, perturbations, "
          f"native run log ({len(runlog)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
