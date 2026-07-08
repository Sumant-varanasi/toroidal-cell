"""Margin-aware mixed-SKU search: separation demanded from the start.

The pass-1/pass-2 sequence showed alternating-ROC rings close exactly
but crowd their constellations; bolting separation onto converged
closures rescued only one design. This run puts the separation target
in the objective from the first Nelder-Mead step, over the pair/N
combos that produced the cleanest closures, at moderate k where the
crowding was mildest.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mixed_sku_native.py --workers 6
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
                               ENVELOPE_MAX, REFL, SKU,
                               analytic_candidates, hole_visits, make_cfg)
from mixed_sku_pass2 import sep_and_clear                          # noqa: E402

SEP_WANT = 0.45
K_KEEP = tuple(range(9, 24, 2))          # moderate k only

COMBOS = [
    (12, 5, 500.0, 750.0), (12, 5, 150.0, 200.0), (12, 5, 1000.0, 1500.0),
    (14, 5, 200.0, 250.0), (14, 5, 150.0, 200.0), (14, 5, 500.0, 750.0),
    (16, 7, 150.0, 200.0), (16, 7, 200.0, 500.0), (16, 7, 500.0, 750.0),
    (16, 7, 250.0, 500.0),
]


def refine_native(cand):
    N, s = cand["N"], cand["s"]
    ra, rb = cand["roc_a"], cand["roc_b"]
    n_exit = cand["n_exit"]
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
        if miss < 0.5:
            cfg2, perts2 = make_cfg(N, s, ra, rb, r, at, asag, oz, w0,
                                    wf, n_exit)
            sep, clear, _ = sep_and_clear(cfg2, perts2, n_exit)
            if sep is not None:
                pen += 12.0 * max(0.0, SEP_WANT - sep)
                pen += 12.0 * max(0.0, HOLE_MARGIN - clear)
        return pen

    best = None
    for at0, as0, w00 in ((0.020, 0.020, 0.30), (0.045, 0.030, 0.40)):
        x0 = np.array([cand["r_ring"], at0, as0, 0.0, w00, 0.55])
        res = minimize(objective, x0, method="Nelder-Mead",
                       options=dict(maxiter=240, xatol=2e-5, fatol=1e-4))
        if best is None or res.fun < best.fun:
            best = res
        if best.fun < 0.05:
            break
    r, at, asag, oz, w0, wf = best.x
    cfg2, perts2 = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf, n_exit)
    from tmpc_platform_v5 import simulate_tmpc
    res2 = simulate_tmpc(cfg2, perturbations=perts2)
    _, visits = hole_visits(*make_cfg(N, s, ra, rb, r, at, asag, oz, w0,
                                      wf, n_pass))
    vv = [v for v in visits if abs(v[0] - n_exit) <= 1]
    miss = vv[0][1] if vv else np.inf
    sep, clear, w_max = sep_and_clear(cfg2, perts2, n_exit)
    env = 2 * (r + RADIAL_ALLOWANCE)
    out = dict(N=N, s=s, roc_a=ra, roc_b=rb, k=cand["k"], n_exit=n_exit,
               r_ring=float(r), exit_miss=float(miss),
               sep_margin=sep, hole_clear=clear,
               envelope_mm=float(env), opl_m=res2.opl / 1000.0,
               throughput=REFL ** max(0, n_exit - 1),
               sku_a=SKU.get(ra, str(ra)), sku_b=SKU.get(rb, str(rb)))
    out["feasible"] = bool(miss < 0.05 and (sep or -1) > 0.0
                           and (clear or -1) > 0.0 and env <= ENVELOPE_MAX)
    return out


def explore(combo):
    N = combo[0]
    r_lo = max(28.0, (12.7 + 1.0) / (2 * np.sin(np.pi / N)) + 0.2)
    try:
        cands = [c for c in analytic_candidates(combo, r_lo, 77.5)
                 if c["k"] in K_KEEP][:4]
        return [refine_native(c) for c in cands]
    except Exception as exc:                                   # noqa: BLE001
        return [dict(N=combo[0], s=combo[1], roc_a=combo[2],
                     roc_b=combo[3], feasible=False, k=0, n_exit=0,
                     reason=f"error: {exc}")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    print(f"{len(COMBOS)} combos, k in {K_KEEP[0]}..{K_KEEP[-1]}, "
          f"sep target {SEP_WANT} mm in-objective")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, out in enumerate(ex.map(explore, COMBOS)):
            for r in out:
                rows.append(r)
                tag = "FEASIBLE" if r.get("feasible") else "--"
                print(f"  [{i+1}/{len(COMBOS)}] N={r['N']} "
                      f"{r['roc_a']:.0f}/{r['roc_b']:.0f} k={r.get('k',0)} "
                      f"opl={r.get('opl_m', 0):.1f} m "
                      f"env={r.get('envelope_mm', 0):.0f} "
                      f"miss={r.get('exit_miss', 9):.3f} "
                      f"sep={r.get('sep_margin', -9) if r.get('sep_margin') is not None else -9:.2f} "
                      f"{tag}", flush=True)
    df = pd.DataFrame(rows)
    out_csv = os.path.join(_HERE, "designs", "mixed_sku_native.csv")
    df.to_csv(out_csv, index=False)
    feas = df[df.get("feasible", False) == True] if len(df) else df  # noqa: E712
    print(f"\n{len(feas)} feasible margin-aware mixed designs -> {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
