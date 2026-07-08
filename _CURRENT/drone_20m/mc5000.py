"""5000-trial drone-yield Monte Carlo per the prof's composed-vector model.

Benoy 2026-07-08 framework: in-use tolerance = alignment residual R_align
plus operational drift D_op (thermal + vibration + pressure + cycling,
already composed in his per-mount drone tables). His COMSOL protocol
demands Monte-Carlo yield > 99.9 % for drone/product designs, sampled
uniformly within the maximum-drift envelope — 400-trial runs cannot
resolve that, so this runs 5000 trials per design per architecture.

Architectures (per-axis maxima, uniform sampling, applied independently
per mirror; launch chain gets the R_align + input-chain drift box):

  al_flexure  : easy regime launch (0.02 mm / 0.05 mrad) + drone Al
                isostatic flexure mirror drift 0.05/0.05/0.08 mm,
                0.15 mrad  -> launch box 0.07 mm / 0.20 mrad
  hybrid      : medium regime launch (0.05 / 0.15) + drone hybrid
                plastic-body + Al-cartridge drift 0.12/0.12/0.18 mm,
                0.40 mrad  -> launch box 0.17 mm / 0.55 mrad

Pass per trial: full path completes, every pre-exit pass clears the
hole, exit spot leaves wholly inside the hole rim, and no two spots on
any mirror physically overlap. Reports point yield and 95 % Wilson
lower bound; drone criterion met when LB >= 0.999.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mc5000.py --workers 12
"""
from __future__ import annotations

import argparse
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
from tmpc_platform_v5.physics import (MirrorPerturbation,            # noqa: E402
                                      mirror_footprints)

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

# (mirror dx=dy [mm], mirror dz [mm], mirror tilt x=y [mrad],
#  launch pos box [mm], launch angle box [mrad])
ARCH = {
    "al_flexure": (0.050, 0.080, 0.15, 0.07, 0.20),
    "hybrid":     (0.120, 0.180, 0.40, 0.17, 0.55),
}
N_TRIALS = 5000
CHUNK = 250


def load_spec(fn):
    with open(os.path.join(_HERE, "designs", fn), "r", encoding="utf-8") as f:
        spec = json.load(f)
    return spec["cfg"], int(spec["metrics"]["n_exit"])


def trial(cfg_kw, n_exit, arch, rng):
    dxy, dz, tilt_mrad, lpos, lang = ARCH[arch]
    kw = dict(cfg_kw)
    kw["input_offset_t"] = kw.get("input_offset_t", 0.0) + rng.uniform(
        -lpos, lpos)
    kw["input_offset_z"] = kw.get("input_offset_z", 0.0) + rng.uniform(
        -lpos, lpos)
    kw["input_angle"] = kw.get("input_angle", 0.0) + rng.uniform(
        -lang, lang) * 1e-3
    kw["input_angle_sag"] = kw.get("input_angle_sag", 0.0) + rng.uniform(
        -lang, lang) * 1e-3
    cfg = TMPCConfig(**kw)
    cfg.n_passes = n_exit + 2
    tilt = tilt_mrad * 1e-3
    perts = [MirrorPerturbation(
        d_tan=rng.uniform(-dxy, dxy), d_sag=rng.uniform(-dxy, dxy),
        d_ax=rng.uniform(-dz, dz),
        tilt_tan=rng.uniform(-tilt, tilt), tilt_sag=rng.uniform(-tilt, tilt))
        for _ in range(cfg.N)]
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < n_exit:
        return "incomplete", -np.inf
    foot = mirror_footprints(res.spot_pattern[:n], res.mirror_sequence[:n],
                             cfg)
    if 0 not in foot:
        return "incomplete", -np.inf
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg_kw.get("input_offset_z", 0.0)])
    exit_clear = -np.inf
    for u, v, o in foot[0]:
        j = int(o)
        if j == 0:
            continue
        d = float(np.hypot(u - hole[0], v - hole[1]))
        w = float(w_eff[min(j, len(w_eff) - 1)])
        if abs(j - n_exit) <= 1:
            exit_clear = cfg.hole_radius - (d + w)
        elif j < n_exit and d < cfg.hole_radius + w:
            return "early_leak", exit_clear
    if exit_clear < 0.0:
        return "exit_miss", exit_clear
    for m, arr in foot.items():
        # separation applies to genuine pattern spots only: the entrance
        # (order 0) and the exit visit coincide at the hole by design
        # (re-entrance), and orders past n_exit are trace overshoot.
        keep = (arr[:, 2] >= 1) & (arr[:, 2] <= n_exit - 1)
        arr = arr[keep]
        if len(arr) < 2:
            continue
        uv = arr[:, :2]
        ws = w_eff[np.clip(arr[:, 2].astype(int), 0, len(w_eff) - 1)]
        dmat = np.hypot(uv[:, None, 0] - uv[None, :, 0],
                        uv[:, None, 1] - uv[None, :, 1])
        need = ws[:, None] + ws[None, :]
        np.fill_diagonal(dmat, np.inf)
        if (dmat < need).any():
            return "overlap", exit_clear
    return "pass", exit_clear


def run_chunk(args):
    cfg_kw, n_exit, arch, seed0, n = args
    rng = np.random.default_rng(seed0)
    counts = {"pass": 0, "incomplete": 0, "early_leak": 0,
              "exit_miss": 0, "overlap": 0}
    clears = []
    for _ in range(n):
        tag, c = trial(cfg_kw, n_exit, arch, rng)
        counts[tag] += 1
        if np.isfinite(c):
            clears.append(c)
    return counts, clears


def wilson_lb(k_pass, n, z=1.959964):
    if n == 0:
        return 0.0
    p = k_pass / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    rad = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - rad) / denom


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--trials", type=int, default=N_TRIALS)
    args = ap.parse_args()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for name, fn in DESIGNS:
            cfg_kw, n_exit = load_spec(fn)
            for arch in ARCH:
                seeds = range(0, args.trials, CHUNK)
                jobs = [(cfg_kw, n_exit, arch, 1000 + s, min(
                    CHUNK, args.trials - s)) for s in seeds]
                counts = {"pass": 0, "incomplete": 0, "early_leak": 0,
                          "exit_miss": 0, "overlap": 0}
                clears = []
                for c, cl in ex.map(run_chunk, jobs):
                    for k in counts:
                        counts[k] += c[k]
                    clears.extend(cl)
                n = sum(counts.values())
                y = counts["pass"] / n
                lb = wilson_lb(counts["pass"], n)
                rows.append(dict(
                    design=name, arch=arch, n_trials=n, n_pass=counts["pass"],
                    yield_pct=100 * y, wilson_lb_pct=100 * lb,
                    meets_999_point=bool(y >= 0.999),
                    meets_999_ci=bool(lb >= 0.999),
                    fail_incomplete=counts["incomplete"],
                    fail_early_leak=counts["early_leak"],
                    fail_exit_miss=counts["exit_miss"],
                    fail_overlap=counts["overlap"],
                    exit_clear_p05=float(np.percentile(clears, 5))
                    if clears else np.nan,
                ))
                r = rows[-1]
                print(f"{name:<18} {arch:<11} yield={r['yield_pct']:7.3f}% "
                      f"LB={r['wilson_lb_pct']:7.3f}% "
                      f"fails: inc={r['fail_incomplete']} "
                      f"leak={r['fail_early_leak']} "
                      f"exit={r['fail_exit_miss']} "
                      f"ovl={r['fail_overlap']} "
                      f"{'MEETS-99.9' if r['meets_999_ci'] else '--'}",
                      flush=True)
    out = os.path.join(_HERE, "designs", "mc5000_drone_yield.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
