"""Mixed-SKU ring exploration: alternating two catalog ROCs in one ring.

All published chord-skip designs (and our whole menu) use ONE mirror SKU
for the full ring. With even N and odd skip s, the beam alternates
A,B,A,B... between two mirror types on every bounce, so a two-SKU ring is
a legal re-entrant system with a genuinely new closure knob: the
transverse round-trip phase depends on BOTH radii, letting (N, s, k)
combinations close on ring radii (and envelopes) that no single catalog
ROC can reach.

Method (exact tracer only -- no analytic prescreen exists for mixed
rings):
  Stage 1  coarse discovery: for each (N, s, ROC_A, ROC_B) and a small
           set of launch templates, scan R_ring at 50 um; at every
           mirror-0 revisit (every N chords) record the transverse miss
           from the hole; keep (R_ring, n_exit) pairs with miss < 1 mm.
  Stage 2  refine: Nelder-Mead over (R_ring, launch angles, offset,
           waist, waist position) minimising the exit miss at the found
           n_exit, with soft penalties for hole-leak clearance, spot
           separation and envelope; then a full check matrix.

Per-mirror ROC is applied through MirrorPerturbation.dR_t/dR_s, which the
ray tracer honours exactly and (after the 2026-07-08 physics patch) the
astigmatic beam-width propagation honours per bounce as well.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mixed_sku_explore.py --workers 2
"""
from __future__ import annotations

import argparse
import itertools
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
EXIT_TOL_COARSE = 1.0
SEP_MARGIN = 0.30
HOLE_MARGIN = 0.30
N_PASS_MAX = 460          # trace depth for discovery (>= k=28 on N=16)

COMBOS = []
for N, s in ((12, 5), (14, 5), (16, 7)):
    for ra, rb in ((100.0, 150.0), (150.0, 200.0), (200.0, 250.0),
                   (250.0, 500.0), (500.0, 750.0), (750.0, 1000.0),
                   (1000.0, 1500.0), (200.0, 500.0), (500.0, 1000.0)):
        COMBOS.append((N, s, ra, rb))

LAUNCH_TEMPLATES = ((0.025, 0.025), (0.045, 0.025),
                    (0.025, 0.045), (0.045, 0.045))

SKU = {100.0: "CM254-050-M01", 150.0: "CM254-075-M01",
       200.0: "CM254-100-M01", 250.0: "CM254-125-M01",
       500.0: "CM254-250-M01", 750.0: "CM254-375-M01",
       1000.0: "CM254-500-M01", 1500.0: "CM254-750-M01"}


def make_cfg(N, s, ra, rb, r_ring, ang_t, ang_s, off_z, w0, waist_frac):
    chord = 2.0 * r_ring * np.sin(np.pi * s / N)
    cfg = TMPCConfig(
        N=N, R_ring=r_ring, H=40.0, R_t=ra, R_s=ra,
        mirror_aperture=11.4, chord_skip=s, n_passes=N_PASS_MAX,
        wavelength=WAVELENGTH, w0=w0, M2=1.0,
        input_waist_offset=float(np.clip(waist_frac, 0.0, 1.5)) * chord / 2,
        input_offset_z=off_z, input_angle=ang_t, input_angle_sag=ang_s,
        reflectivity=REFL, hole_radius=HOLE_R)
    perts = [MirrorPerturbation(dR_t=(rb - ra) if (q % 2) else 0.0,
                                dR_s=(rb - ra) if (q % 2) else 0.0)
             for q in range(N)]
    return cfg, perts


def hole_visits(cfg, perts):
    """Trace and return (res, list of (bounce_j, miss_mm, w_j), foot)."""
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < cfg.N + 1:
        return res, [], None
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    if 0 not in foot:
        return res, [], foot
    arr = foot[0]
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    out = []
    for u, v, order in arr:
        j = int(order)
        miss = float(np.hypot(u - hole[0], v - hole[1]))
        wj = float(w_eff[min(j, len(w_eff) - 1)])
        out.append((j, miss, wj))
    return res, sorted(out), foot


def coarse_scan(combo):
    N, s, ra, rb = combo
    r_lo = max(28.0, (12.7 + 1.0) / (2 * np.sin(np.pi / N)) + 0.2)
    r_hi = (ENVELOPE_MAX - 2 * RADIAL_ALLOWANCE) / 2.0
    cands = []
    for ang_t, ang_s in LAUNCH_TEMPLATES:
        for r in np.arange(r_lo, r_hi + 1e-9, 0.05):
            cfg, perts = make_cfg(N, s, ra, rb, r, ang_t, ang_s,
                                  0.0, 0.35, 0.55)
            _, visits, _ = hole_visits(cfg, perts)
            for j, miss, wj in visits:
                if j < 3 * N:              # too short to be interesting
                    continue
                if miss < EXIT_TOL_COARSE:
                    cands.append(dict(N=N, s=s, roc_a=ra, roc_b=rb,
                                      r_ring=r, ang_t=ang_t, ang_s=ang_s,
                                      n_exit=j, miss=miss))
    # keep the best (smallest miss) per n_exit family
    best = {}
    for c in cands:
        key = (c["n_exit"],)
        if key not in best or c["miss"] < best[key]["miss"]:
            best[key] = c
    return sorted(best.values(), key=lambda c: -c["n_exit"])[:6]


def check_matrix(cfg, perts, n_exit):
    """Full physical checks with the exit at bounce n_exit."""
    cfg2, _ = make_cfg(cfg.N, cfg.chord_skip, cfg.R_t, cfg.R_t,
                       cfg.R_ring, cfg.input_angle, cfg.input_angle_sag,
                       cfg.input_offset_z, cfg.w0, 0.0)
    cfg2.input_waist_offset = cfg.input_waist_offset
    cfg2.n_passes = n_exit
    res = simulate_tmpc(cfg2, perturbations=perts)
    n = res.bounces
    if n < n_exit:
        return None
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg2)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg2.input_offset_z])
    # hole-leak clearance over intermediate mirror-0 visits
    clear = np.inf
    for u, v, order in foot.get(0, np.empty((0, 3))):
        j = int(order)
        if j >= n_exit - 1:
            continue
        d = float(np.hypot(u - hole[0], v - hole[1]))
        wj = float(w_eff[min(j, len(w_eff) - 1)])
        clear = min(clear, d - (HOLE_R + wj))
    # worst same-mirror pair separation margin
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
    return dict(res=res, hole_clear=clear, sep_margin=sep,
                w_max=float(w_eff.max()), opl_m=res.opl / 1000.0,
                aperture_margin=cfg2.mirror_aperture - float(w_eff.max()))


def refine(cand):
    N, s = cand["N"], cand["s"]
    ra, rb = cand["roc_a"], cand["roc_b"]
    n_exit = cand["n_exit"]

    def objective(x):
        r, at, asag, oz, w0, wf = x
        if not (28.0 <= r <= 77.5 and 0.2 <= w0 <= 0.6):
            return 1e6
        cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf)
        _, visits, _ = hole_visits(cfg, perts)
        vv = [v for v in visits if v[0] == n_exit]
        if not vv:
            return 1e5
        j, miss, wj = vv[0]
        pen = 0.0
        for jj, m2, w2 in visits:
            if jj < n_exit and m2 < HOLE_R + w2 + HOLE_MARGIN:
                pen += 10.0 * (HOLE_R + w2 + HOLE_MARGIN - m2)
        return miss + pen

    x0 = np.array([cand["r_ring"], cand["ang_t"], cand["ang_s"],
                   0.0, 0.35, 0.55])
    best = minimize(objective, x0, method="Nelder-Mead",
                    options=dict(maxiter=400, xatol=1e-4, fatol=1e-4))
    r, at, asag, oz, w0, wf = best.x
    cfg, perts = make_cfg(N, s, ra, rb, r, at, asag, oz, w0, wf)
    chk = check_matrix(cfg, perts, n_exit)
    out = dict(cand, r_ring=float(r), ang_t=float(at), ang_s=float(asag),
               off_z=float(oz), w0=float(w0), waist_frac=float(wf),
               exit_miss=float(best.fun))
    if chk is None:
        out.update(feasible=False, reason="path incomplete")
        return out
    env = 2 * (r + RADIAL_ALLOWANCE)
    out.update(opl_m=chk["opl_m"], hole_clear=chk["hole_clear"],
               sep_margin=chk["sep_margin"], w_max=chk["w_max"],
               envelope_mm=env,
               throughput=REFL ** max(0, n_exit - 1),
               sku_a=SKU.get(ra, str(ra)), sku_b=SKU.get(rb, str(rb)))
    out["feasible"] = bool(best.fun < 0.05 and chk["hole_clear"] > 0.0
                           and chk["sep_margin"] > 0.0
                           and env <= ENVELOPE_MAX
                           and chk["aperture_margin"] > 0.0)
    out["reason"] = ("ok" if out["feasible"] else
                     f"miss={best.fun:.3f} clear={chk['hole_clear']:.2f} "
                     f"sep={chk['sep_margin']:.2f} env={env:.0f}")
    return out


def explore_one(combo):
    try:
        cands = coarse_scan(combo)
        return [refine(c) for c in cands]
    except Exception as exc:                                   # noqa: BLE001
        return [dict(N=combo[0], s=combo[1], roc_a=combo[2],
                     roc_b=combo[3], feasible=False,
                     reason=f"error: {exc}")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    print(f"{len(COMBOS)} (N, s, ROC_A, ROC_B) combos, "
          f"{len(LAUNCH_TEMPLATES)} launch templates each")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, out in enumerate(ex.map(explore_one, COMBOS)):
            for r in out:
                rows.append(r)
                tag = "FEASIBLE" if r.get("feasible") else "--"
                print(f"  [{i+1}/{len(COMBOS)}] N={r['N']} s={r['s']} "
                      f"{r['roc_a']:.0f}/{r['roc_b']:.0f} "
                      f"n={r.get('n_exit', 0)} "
                      f"opl={r.get('opl_m', 0):.1f} m "
                      f"env={r.get('envelope_mm', 0):.0f} "
                      f"{tag} ({r.get('reason', '')})", flush=True)
    df = pd.DataFrame(rows)
    out_csv = os.path.join(_HERE, "designs", "mixed_sku_results.csv")
    df.to_csv(out_csv, index=False)
    feas = df[df["feasible"] == True] if "feasible" in df else df.iloc[0:0]  # noqa: E712
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
