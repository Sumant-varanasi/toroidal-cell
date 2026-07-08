"""Mixed-SKU pass 2: separation-aware re-optimization.

Pass 1 (mixed_sku_explore.py) maps WHERE alternating-ROC rings close
re-entrantly (exit miss ~0, positive hole clearance) but its objective
ignores spot separation, so most closures land with overlapping
constellations (sep_margin -0.4..-0.9 mm). This pass takes every
cleanly-closed pass-1 candidate and re-optimizes the same six launch
parameters with the worst-pair separation in the objective — the exact
analogue of the amplitude-ratio tuning the uniform search does.

Run from _CURRENT/ (after pass 1 writes designs/mixed_sku_results.csv):
    ../.venv/Scripts/python.exe drone_20m/mixed_sku_pass2.py --workers 6
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.optimize import minimize

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from mixed_sku_explore import (HOLE_MARGIN, HOLE_R, RADIAL_ALLOWANCE,  # noqa: E402
                               ENVELOPE_MAX, REFL, SKU, hole_visits,
                               make_cfg)
from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints            # noqa: E402

SEP_WANT = 0.30          # worst-pair margin beyond touching [mm]
MISS_TOL = 0.05


def sep_and_clear(cfg, perts, n_exit):
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < n_exit:
        return None, None, None
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    clear = np.inf
    for u, v, order in foot.get(0, np.empty((0, 3))):
        j = int(order)
        if j == 0 or j >= n_exit - 1:
            continue
        d = float(np.hypot(u - hole[0], v - hole[1]))
        wj = float(w_eff[min(j, len(w_eff) - 1)])
        clear = min(clear, d - (HOLE_R + wj))
    sep = np.inf
    for m, arr in foot.items():
        if len(arr) < 2:
            continue
        uv = arr[:, :2]
        ws = w_eff[np.clip(arr[:, 2].astype(int), 0, len(w_eff) - 1)]
        for i in range(len(uv)):
            for jj in range(i + 1, len(uv)):
                d = float(np.hypot(*(uv[i] - uv[jj])))
                sep = min(sep, d - (float(ws[i]) + float(ws[jj])))
    return float(sep), float(clear), float(w_eff.max())


def reopt(row):
    N, s = int(row["N"]), int(row["s"])
    ra, rb = float(row["roc_a"]), float(row["roc_b"])
    n_exit = int(row["n_exit"])
    n_pass = n_exit + N + 4

    def objective(x):
        r, at, asag, oz, w0, wf = x
        if not (28.0 <= r <= 77.5 and 0.2 <= w0 <= 0.6):
            return 1e6
        cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf, n_pass)
        _, visits = hole_visits(cfg, perts)
        vv = [v for v in visits if abs(v[0] - n_exit) <= 1]
        if not vv:
            return 1e5
        j, miss, _ = vv[0]
        pen = 50.0 * miss
        for jj, m2, w2 in visits:
            if 0 < jj < j and m2 < HOLE_R + w2 + HOLE_MARGIN:
                pen += 10.0 * (HOLE_R + w2 + HOLE_MARGIN - m2)
        if miss < 0.3:      # only pay for separation once nearly closed
            cfg2, perts2 = make_cfg(N, s, ra, rb, r, at, asag, oz, w0,
                                    wf, n_exit)
            sep, clear, _ = sep_and_clear(cfg2, perts2, n_exit)
            if sep is not None:
                pen += 10.0 * max(0.0, SEP_WANT - sep)
                pen += 10.0 * max(0.0, -clear)
        return pen

    x0 = np.array([row["r_ring"], row["ang_t"], row["ang_s"],
                   row["off_z"], row["w0"], row["waist_frac"]])
    best = minimize(objective, x0, method="Nelder-Mead",
                    options=dict(maxiter=220, xatol=2e-5, fatol=1e-4))
    r, at, asag, oz, w0, wf = best.x
    cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf,
                          n_exit + N + 4)
    _, visits = hole_visits(cfg, perts)
    vv = [v for v in visits if abs(v[0] - n_exit) <= 1]
    miss = vv[0][1] if vv else np.inf
    cfg2, perts2 = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf, n_exit)
    sep, clear, w_max = sep_and_clear(cfg2, perts2, n_exit)
    res = simulate_tmpc(cfg2, perturbations=perts2)
    env = 2 * (r + RADIAL_ALLOWANCE)
    out = dict(N=N, s=s, roc_a=ra, roc_b=rb, k=int(row.get("k", 0)),
               n_exit=n_exit, r_ring=float(r), ang_t=float(at),
               ang_s=float(asag), off_z=float(oz), w0=float(w0),
               waist_frac=float(wf), exit_miss=float(miss),
               sep_margin=sep, hole_clear=clear, w_max=w_max,
               envelope_mm=float(env), opl_m=res.opl / 1000.0,
               throughput=REFL ** max(0, n_exit - 1),
               sku_a=SKU.get(ra, str(ra)), sku_b=SKU.get(rb, str(rb)))
    out["feasible"] = bool(miss < MISS_TOL and (sep or -1) > 0.0
                           and (clear or -1) > 0.0
                           and env <= ENVELOPE_MAX and w_max < 11.4)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--top", type=int, default=16)
    args = ap.parse_args()
    df = pd.read_csv(os.path.join(_HERE, "designs",
                                  "mixed_sku_results.csv"))
    cand = df[(df["feasible"] == False)                       # noqa: E712
              & (df["exit_miss"] < 0.1)
              & (df["hole_clear"] > 0.0)
              & (df["sep_margin"] > -1.2)].copy()
    cand = cand.sort_values("opl_m", ascending=False).head(args.top)
    print(f"pass 2 on {len(cand)} cleanly-closed candidates")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(reopt, cand.to_dict("records"))):
            rows.append(r)
            tag = "FEASIBLE" if r["feasible"] else "--"
            print(f"  [{i+1}/{len(cand)}] N={r['N']} "
                  f"{r['roc_a']:.0f}/{r['roc_b']:.0f} n={r['n_exit']} "
                  f"opl={r['opl_m']:.1f} m env={r['envelope_mm']:.0f} "
                  f"miss={r['exit_miss']:.3f} sep={r['sep_margin']:.2f} "
                  f"clear={r['hole_clear']:.2f} {tag}", flush=True)
    out = os.path.join(_HERE, "designs", "mixed_sku_pass2.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
