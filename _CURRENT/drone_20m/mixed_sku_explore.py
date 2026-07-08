"""Mixed-SKU ring exploration: alternating two catalog ROCs in one ring.

All published chord-skip designs (and our whole menu) use ONE mirror SKU
for the full ring. With even N and odd skip s, the beam alternates
A,B,A,B... between two mirror types on every bounce, so a two-SKU ring is
a legal re-entrant system with a genuinely new closure knob: the
transverse round-trip phase depends on BOTH radii, letting (N, s, k)
combinations close on ring radii (and envelopes) that no single catalog
ROC can reach.

Method:
  Stage 1  ANALYTIC prescreen (the brute trace-scan fails: the closure
           acceptance window in R_ring is ~5 um wide at high bounce
           count). The alternating cell's transverse phase per two
           bounces follows from the 2x2 unit cell
              M = M(f_B) P(L) M(f_A) P(L),   cos(theta2) = tr(M)/2
           per plane (f_t = R cos(aoi)/2, f_s = R/(2 cos(aoi))).
           Closure at n = k*N bounces requires (n/2)*theta2 = 0 (mod pi)
           in both planes; R_ring is scanned analytically at 10 um.
  Stage 2  exact-trace Nelder-Mead refine at each analytic root
           (R_ring, launch angles, offset, waist, waist position),
           then the full check matrix.

Per-mirror ROC enters through MirrorPerturbation.dR_t/dR_s, which the
ray tracer honours exactly and (2026-07-08 physics patch) the astigmatic
beam-width propagation honours per bounce as well.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mixed_sku_explore.py --workers 2
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

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc            # noqa: E402
from tmpc_platform_v5.physics import (MirrorPerturbation,         # noqa: E402
                                      mirror_footprints)

WAVELENGTH = 1.654e-3
HOLE_R = 1.3
REFL = 0.999
RADIAL_ALLOWANCE = 18.0
ENVELOPE_MAX = 190.0
SEP_MARGIN = 0.30
HOLE_MARGIN = 0.30
K_SET = tuple(range(5, 34, 2))       # spots per mirror (odd, like uniform)
PHASE_TOL_T = 0.35
PHASE_TOL_S = 0.30
R_STEP = 0.010                        # analytic scan step [mm]

COMBOS = []
for N, s in ((12, 5), (14, 5), (16, 7)):
    for ra, rb in ((100.0, 150.0), (150.0, 200.0), (200.0, 250.0),
                   (250.0, 500.0), (500.0, 750.0), (750.0, 1000.0),
                   (1000.0, 1500.0), (200.0, 500.0), (500.0, 1000.0)):
        COMBOS.append((N, s, ra, rb))

SKU = {100.0: "CM254-050-M01", 150.0: "CM254-075-M01",
       200.0: "CM254-100-M01", 250.0: "CM254-125-M01",
       500.0: "CM254-250-M01", 750.0: "CM254-375-M01",
       1000.0: "CM254-500-M01", 1500.0: "CM254-750-M01"}


# ---------------------------------------------------------------------------
# Stage 1: analytic unit-cell phases
# ---------------------------------------------------------------------------
def theta2_arr(L: np.ndarray, fa: float, fb: float) -> np.ndarray:
    """Phase advance over two bounces of the alternating cell (vectorized).

    M = M(fb) @ P(L) @ M(fa) @ P(L); returns arccos(tr/2) with NaN where
    the cell is unstable.
    """
    a21 = -1.0 / fa
    a22 = 1.0 - L / fa
    # B = P(L) @ M(fa) @ P(L):  [[1+L*a21, L+L*a22], [a21, a22]]
    b11 = 1.0 + L * a21
    b12 = L + L * a22
    b22 = a22
    # C = M(fb) @ B:  tr = c11 + c22 = b11 + (-b12/fb + b22)
    tr = b11 + (-b12 / fb + b22)
    th = np.full_like(np.asarray(L, dtype=float), np.nan)
    m = np.abs(tr) < 2.0
    th[m] = np.arccos(tr[m] / 2.0)
    return th


def circ_dist_pi_arr(phi: np.ndarray) -> np.ndarray:
    return np.abs(((phi + np.pi / 2) % np.pi) - np.pi / 2)


def analytic_candidates(combo, r_lo, r_hi):
    """Vectorized 2 um analytic scan; per-k acceptance runs -> best root
    per run; k-diverse candidate list.

    The scan must resolve the accumulated phase: d(n/2*theta2)/dR is
    ~n/2 * 1e-3 rad/um, so at k=33 (n~400-530) a 10 um step aliases; at
    2 um the phase moves <~0.5 rad per step for every k in K_SET.
    """
    N, s, ra, rb = combo
    aoi = np.pi / 2 - np.pi * s / N
    rs = np.arange(r_lo, r_hi + 1e-9, 0.002)
    L = 2.0 * rs * np.sin(np.pi * s / N)
    th_t = theta2_arr(L, ra * np.cos(aoi) / 2.0, rb * np.cos(aoi) / 2.0)
    th_s = theta2_arr(L, ra / (2.0 * np.cos(aoi)),
                      rb / (2.0 * np.cos(aoi)))
    ok = ~(np.isnan(th_t) | np.isnan(th_s))
    cands = []
    for k in K_SET:
        n = k * N
        res_t = circ_dist_pi_arr(n / 2.0 * th_t)
        res_s = circ_dist_pi_arr(n / 2.0 * th_s)
        acc = ok & (res_t < PHASE_TOL_T) & (res_s < PHASE_TOL_S)
        if not acc.any():
            continue
        # connected acceptance runs -> argmin of combined residual
        idx = np.flatnonzero(acc)
        splits = np.flatnonzero(np.diff(idx) > 1)
        runs = np.split(idx, splits + 1)
        scored = []
        for run in runs:
            comb = res_t[run] + res_s[run]
            i = run[int(np.argmin(comb))]
            scored.append((float(res_t[i] + res_s[i]), i))
        scored.sort()
        for scr, i in scored[:2]:            # best two runs per k
            cands.append(dict(N=N, s=s, roc_a=ra, roc_b=rb,
                              r_ring=float(rs[i]), k=k, n_exit=n,
                              res_t=float(res_t[i]),
                              res_s=float(res_s[i]),
                              opl_est=float(n * L[i] / 1000.0)))
    # k-diverse: at most 2 per k already; rank by OPL, cap total
    cands.sort(key=lambda c: -c["opl_est"])
    return cands[:10]


# ---------------------------------------------------------------------------
# Stage 2: exact-trace refinement
# ---------------------------------------------------------------------------
def make_cfg(N, s, ra, rb, r_ring, ang_t, ang_s, off_z, w0, waist_frac,
             n_passes):
    chord = 2.0 * r_ring * np.sin(np.pi * s / N)
    cfg = TMPCConfig(
        N=N, R_ring=r_ring, H=40.0, R_t=ra, R_s=ra,
        mirror_aperture=11.4, chord_skip=s, n_passes=n_passes,
        wavelength=WAVELENGTH, w0=w0, M2=1.0,
        input_waist_offset=float(np.clip(waist_frac, 0.0, 1.5)) * chord / 2,
        input_offset_z=off_z, input_angle=ang_t, input_angle_sag=ang_s,
        reflectivity=REFL, hole_radius=HOLE_R)
    perts = [MirrorPerturbation(dR_t=(rb - ra) if (q % 2) else 0.0,
                                dR_s=(rb - ra) if (q % 2) else 0.0)
             for q in range(N)]
    return cfg, perts


def hole_visits(cfg, perts):
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < cfg.N + 1:
        return res, []
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    if 0 not in foot:
        return res, []
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    out = []
    for u, v, order in foot[0]:
        j = int(order)
        miss = float(np.hypot(u - hole[0], v - hole[1]))
        wj = float(w_eff[min(j, len(w_eff) - 1)])
        out.append((j, miss, wj))
    return res, sorted(out)


def refine(cand):
    N, s = cand["N"], cand["s"]
    ra, rb = cand["roc_a"], cand["roc_b"]
    n_exit = cand["n_exit"] - 1          # bounce index of the k*N-th visit
    n_pass = cand["n_exit"] + N + 4

    def objective(x):
        r, at, asag, oz, w0, wf = x
        if not (28.0 <= r <= 77.5 and 0.2 <= w0 <= 0.6):
            return 1e6
        cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf, n_pass)
        _, visits = hole_visits(cfg, perts)
        vv = [v for v in visits if abs(v[0] - n_exit) <= 1]
        if not vv:
            return 1e5
        j, miss, wj = vv[0]
        pen = 0.0
        for jj, m2, w2 in visits:
            if jj < j and m2 < HOLE_R + w2 + HOLE_MARGIN:
                pen += 10.0 * (HOLE_R + w2 + HOLE_MARGIN - m2)
        return miss + pen

    x0 = np.array([cand["r_ring"], 0.030, 0.030, 0.0, 0.35, 0.55])
    best = minimize(objective, x0, method="Nelder-Mead",
                    options=dict(maxiter=140, xatol=2e-5, fatol=1e-4))
    r, at, asag, oz, w0, wf = best.x
    out = dict(cand, r_ring=float(r), ang_t=float(at), ang_s=float(asag),
               off_z=float(oz), w0=float(w0), waist_frac=float(wf),
               exit_miss=float(best.fun),
               sku_a=SKU.get(ra, str(ra)), sku_b=SKU.get(rb, str(rb)))
    if best.fun > 0.6:
        out.update(feasible=False, reason=f"no closure (miss {best.fun:.2f})")
        return out

    # full check matrix at the refined point
    cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf,
                          n_exit)
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < n_exit:
        out.update(feasible=False, reason="path incomplete")
        return out
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, oz])
    clear = np.inf
    for u, v, order in foot.get(0, np.empty((0, 3))):
        j = int(order)
        if j >= n_exit - 1:
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
    env = 2 * (r + RADIAL_ALLOWANCE)
    out.update(opl_m=res.opl / 1000.0, hole_clear=float(clear),
               sep_margin=float(sep), w_max=float(w_eff.max()),
               envelope_mm=float(env),
               throughput=REFL ** max(0, n_exit - 1))
    out["feasible"] = bool(out["exit_miss"] < 0.05 and clear > 0.0
                           and sep > 0.0 and env <= ENVELOPE_MAX
                           and float(w_eff.max()) < 11.4)
    out["reason"] = ("ok" if out["feasible"] else
                     f"miss={out['exit_miss']:.3f} clear={clear:.2f} "
                     f"sep={sep:.2f} env={env:.0f}")
    return out


def explore_one(combo):
    N = combo[0]
    r_lo = max(28.0, (12.7 + 1.0) / (2 * np.sin(np.pi / N)) + 0.2)
    r_hi = (ENVELOPE_MAX - 2 * RADIAL_ALLOWANCE) / 2.0
    try:
        cands = analytic_candidates(combo, r_lo, r_hi)
        return [refine(c) for c in cands]
    except Exception as exc:                                   # noqa: BLE001
        return [dict(N=combo[0], s=combo[1], roc_a=combo[2],
                     roc_b=combo[3], feasible=False,
                     reason=f"error: {exc}")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    print(f"{len(COMBOS)} (N, s, ROC_A, ROC_B) combos, analytic prescreen "
          f"at {R_STEP*1e3:.0f} um, k in {K_SET[0]}..{K_SET[-1]}")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, out in enumerate(ex.map(explore_one, COMBOS)):
            for r in out:
                rows.append(r)
                tag = "FEASIBLE" if r.get("feasible") else "--"
                print(f"  [{i+1}/{len(COMBOS)}] N={r['N']} s={r['s']} "
                      f"{r['roc_a']:.0f}/{r['roc_b']:.0f} "
                      f"k={r.get('k', 0)} n={r.get('n_exit', 0)} "
                      f"opl={r.get('opl_m', r.get('opl_est', 0)):.1f} m "
                      f"env={r.get('envelope_mm', 0):.0f} "
                      f"{tag} ({r.get('reason', '')})", flush=True)
    df = pd.DataFrame(rows)
    out_csv = os.path.join(_HERE, "designs", "mixed_sku_results.csv")
    df.to_csv(out_csv, index=False)
    feas = (df[df["feasible"] == True]                        # noqa: E712
            if "feasible" in df else df.iloc[0:0])
    print(f"\n{len(feas)} feasible mixed-SKU designs -> {out_csv}")
    if len(feas):
        cols = ["N", "s", "roc_a", "roc_b", "n_exit", "opl_m",
                "envelope_mm", "throughput", "sep_margin", "hole_clear"]
        with pd.option_context("display.width", 220):
            print(feas.sort_values("opl_m", ascending=False)[cols]
                  .head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
