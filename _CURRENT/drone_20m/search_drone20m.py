"""Drone 20 m TMPC design search.

Goal (2026-07-02 brief): ~20 m optical path length in a cell whose total
assembly diameter stays safely under 190 mm, using only cheap Thorlabs
protected-gold concave mirrors (CM127 half-inch or CM254 one-inch series),
with entrance-hole radius = input beam waist radius = 1.3 mm.

Two stages:

Stage A -- analytic prescreen (no ray tracing). Enumerates
    family x catalog ROC x N x chord_skip x R_ring and keeps combinations
    that simultaneously satisfy
      * mirror packing on the ring (adjacent substrates cannot overlap),
      * assembly envelope 2*(R_ring + RADIAL_ALLOWANCE) <= 190 mm,
      * per-plane astigmatic stability (|cos theta| < 1 in both planes),
      * re-entrance phase closure: after n = k*N bounces the tangential AND
        sagittal ray phases n*theta must both return near a multiple of
        2*pi, so the beam lands back on the entrance hole and exits,
      * estimated OPL = n * chord in the 19.6 - 32 m window.

Stage B -- exact verification. For each surviving candidate the real 3-D
    ray tracer (tmpc_platform_v5.simulate_tmpc) is run over a small grid of
    launch offsets/angles, then the best seeds are polished with
    Nelder-Mead over (R_ring, input_offset_z, input_angle) -- the
    parameters a machined housing can actually realise -- against the
    catalog-locked ROC. Every physical check is enforced on the traced
    path:
      * ray survives (no geometric clipping),
      * beam edge (1/e^2) stays inside the clear aperture at every bounce,
      * beam exits through the entrance hole (first hole re-visit within
        EXIT_TOL) at >= 19.5 m OPL,
      * every intermediate mirror-0 spot clears the hole by its own beam
        radius (no early leakage),
      * distinct spots never overlap (separation >= sum of beam radii),
      * per-plane stability from the simulator,
      * throughput budget: R^n_reflections x hole truncation in AND out.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/search_drone20m.py --workers 10

Outputs CSVs under drone_20m/results/.
All lengths mm, angles rad unless suffixed _deg.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from math import gcd
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))          # _CURRENT/ on sys.path

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc            # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints            # noqa: E402
from tmpc_platform_v5.samplers import FAMILIES, REFLECTIVITY_1654NM  # noqa: E402

# ---------------------------------------------------------------------------
# Fixed design constants (from the 2026-07-02 brief)
# ---------------------------------------------------------------------------
W0 = 1.3                 # input beam waist radius [mm] (user-fixed)
HOLE_R = 1.3             # entrance/exit hole radius [mm] (user-fixed)
WAVELENGTH = 1.654e-3    # CH4 line [mm]
M2 = 1.0                 # design-nominal beam quality
REFL = REFLECTIVITY_1654NM               # 0.97, protected gold @ 1654 nm
TRUNC = 1.0 - np.exp(-2.0)               # Gaussian power through r = w hole

ENVELOPE_MAX = 190.0     # hard assembly-diameter cap [mm]
RADIAL_ALLOWANCE = 18.0  # mirror substrate (~6.4) + housing wall + margin [mm]
PACK_GAP = 1.0           # minimum web between adjacent mirror substrates [mm]

OPL_MIN_M = 19.5         # accept window on verified OPL
OPL_EST_LO_M = 19.6      # Stage A estimate window
OPL_EST_HI_M = 32.0
N_BOUNCE_MAX = 300       # cap on bounces before forced exit
EXIT_TOL = 0.5           # spot-centre distance counting as "through the hole"
MISS_EST_TOL = 1.2       # Stage A estimated hole miss to keep a candidate [mm]
AMP_EST = 4.0            # assumed transverse pattern amplitude for miss est.

R_RING_MAX = (ENVELOPE_MAX - 2.0 * RADIAL_ALLOWANCE) / 2.0        # 77 mm
R_RING_MIN = 25.0
N_RANGE = range(7, 41)


# ---------------------------------------------------------------------------
# Stage A -- analytic prescreen
# ---------------------------------------------------------------------------
def _circ_dist(phase: np.ndarray) -> np.ndarray:
    """Distance of a phase [rad] from the nearest multiple of 2*pi."""
    return np.abs((phase + np.pi) % (2.0 * np.pi) - np.pi)


def stage_a() -> pd.DataFrame:
    rows: List[Dict] = []
    r_grid = np.arange(R_RING_MIN, R_RING_MAX + 1e-9, 0.25)
    for family, fam in FAMILIES.items():
        diam = fam["diameter_mm"]
        for sku, _f, roc in fam["catalog"]:
            for N in N_RANGE:
                # packing: adjacent mirror centres 2R sin(pi/N) >= diam + gap
                pack_ok = 2.0 * r_grid * np.sin(np.pi / N) >= diam + PACK_GAP
                if not pack_ok.any():
                    continue
                k_max = N_BOUNCE_MAX // N
                if k_max < 1:
                    continue
                for s in range(2, N // 2 + 1):
                    if gcd(N, s) != 1:
                        continue
                    L = 2.0 * r_grid * np.sin(np.pi * s / N)
                    ci = np.sin(np.pi * s / N)      # cos(AOI), AOI = pi/2 - pi s/N
                    ct = 1.0 - L / (roc * ci)       # tangential unit-cell cos
                    cs = 1.0 - L * ci / roc         # sagittal unit-cell cos
                    stable = (np.abs(ct) < 1.0 - 1e-4) & (np.abs(cs) < 1.0 - 1e-4)
                    ok = pack_ok & stable
                    if not ok.any():
                        continue
                    th_t = np.arccos(np.clip(ct, -1, 1))
                    th_s = np.arccos(np.clip(cs, -1, 1))
                    ks = np.arange(1, k_max + 1)
                    n = ks[:, None] * N                            # (K, R)
                    miss = AMP_EST * np.maximum(_circ_dist(n * th_t[None, :]),
                                                _circ_dist(n * th_s[None, :]))
                    closes = miss < MISS_EST_TOL                   # (K, R)
                    any_close = closes.any(axis=0)
                    ok &= any_close
                    if not ok.any():
                        continue
                    first_k = np.argmax(closes, axis=0)            # index into ks
                    n_exit = (first_k + 1) * N
                    opl_m = n_exit * L * 1e-3
                    ok &= (opl_m >= OPL_EST_LO_M) & (opl_m <= OPL_EST_HI_M)
                    if not ok.any():
                        continue
                    idxs = np.where(ok)[0]
                    # keep the few best R_ring per (sku, N, s, k) by miss
                    miss_first = miss[first_k[idxs], idxs]
                    for kk in np.unique(n_exit[idxs]):
                        sel = idxs[n_exit[idxs] == kk]
                        best = sel[np.argsort(miss_first[n_exit[idxs] == kk])[:3]]
                        for i in best:
                            n_i = int(n_exit[i])
                            rows.append(dict(
                                family=family, sku=sku, roc=float(roc),
                                N=N, chord_skip=s, R_ring=float(r_grid[i]),
                                chord_mm=float(L[i]),
                                aoi_deg=float(np.degrees(np.pi / 2 - np.pi * s / N)),
                                n_exit=n_i, spots_per_mirror=n_i // N,
                                opl_est_m=float(opl_m[i]),
                                miss_est_mm=float(miss[first_k[i], i]),
                                throughput_est=float(
                                    TRUNC ** 2 * REFL ** (n_i - 1)),
                                envelope_mm=float(2 * (r_grid[i]
                                                       + RADIAL_ALLOWANCE)),
                            ))
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["throughput_est", "miss_est_mm"],
                            ascending=[False, True]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Stage B -- exact trace + full physical checks
# ---------------------------------------------------------------------------
def evaluate(p: Dict) -> Dict:
    """Trace one candidate and run every physical check.

    p needs: family, sku, roc, N, chord_skip, R_ring, n_target,
             input_offset_z, input_angle.
    """
    fam = FAMILIES[p["family"]]
    ap = fam["clear_aperture_radius_mm"]
    out = dict(p)
    out.update(feasible=False, reason="", opl_m=0.0, n_exit=0,
               throughput=0.0, exit_miss_mm=np.inf, hole_margin_mm=-np.inf,
               ap_margin_mm=-np.inf, sep_margin_mm=-np.inf, min_sep_mm=0.0,
               w_max_mm=0.0, H_req_mm=0.0, stab_tan=np.nan, stab_sag=np.nan,
               aoi_deg=np.nan)
    n_passes = min(int(p["n_target"]) + 2 * int(p["N"]), 2 * N_BOUNCE_MAX)
    try:
        cfg = TMPCConfig(
            N=int(p["N"]), R_ring=float(p["R_ring"]), H=40.0,
            R_t=float(p["roc"]), R_s=float(p["roc"]),
            mirror_aperture=ap, chord_skip=int(p["chord_skip"]),
            n_passes=n_passes, wavelength=WAVELENGTH, w0=W0, M2=M2,
            input_offset_z=float(p["input_offset_z"]),
            input_angle=float(p["input_angle"]),
            reflectivity=REFL, hole_radius=HOLE_R)
        res = simulate_tmpc(cfg)
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"sim error: {exc}"
        return out

    n_b = res.bounces
    if n_b < int(p["n_target"]) + 1:
        out["reason"] = f"ray died at bounce {n_b} (clipped)"
        return out

    hits = res.spot_pattern[:n_b]
    w_eff = np.maximum(res.w_tangential, res.w_sagittal)[:n_b + 1]
    foot = mirror_footprints(hits, res.mirror_sequence[:n_b], cfg)

    # --- exit through the entrance hole: first mirror-0 re-visit ---
    m0 = foot[0]                       # (u, v, order)
    if len(m0) < 2:
        out["reason"] = "no mirror-0 revisit"
        return out
    order = m0[:, 2].astype(int)
    hole_uv = m0[order == 0][0, :2]
    dists = np.linalg.norm(m0[:, :2] - hole_uv, axis=1)
    revisits = np.argsort(order)
    exit_row = None
    for r in revisits:
        if order[r] == 0:
            continue
        if dists[r] < EXIT_TOL:
            exit_row = r
            break
    if exit_row is None:
        out["reason"] = "never returns to hole"
        # still report the closest approach at the target bounce for polish
        tgt = m0[order == int(p["n_target"])]
        if len(tgt):
            out["exit_miss_mm"] = float(
                np.linalg.norm(tgt[0, :2] - hole_uv))
        return out
    exit_idx = int(order[exit_row])
    out["exit_miss_mm"] = float(dists[exit_row])
    out["n_exit"] = exit_idx

    # --- OPL inside the cell (hole -> hole) ---
    opl = float(np.sum(np.linalg.norm(np.diff(hits[:exit_idx + 1], axis=0),
                                      axis=1)))
    out["opl_m"] = opl * 1e-3

    # --- hole clearance for intermediate mirror-0 spots ---
    mid = (order > 0) & (order < exit_idx)
    if mid.any():
        clear = dists[mid] - (HOLE_R + w_eff[order[mid]])
        out["hole_margin_mm"] = float(np.min(clear))
    else:
        out["hole_margin_mm"] = np.inf

    # --- aperture margin (beam 1/e^2 edge inside clear aperture) ---
    ap_margin = np.inf
    sep_margin = np.inf
    min_sep = np.inf
    for kmir in range(cfg.N):
        fk = foot[kmir]
        if not len(fk):
            continue
        okk = fk[:, 2].astype(int) <= exit_idx
        uv = fk[okk, :2]
        oo = fk[okk, 2].astype(int)
        r_edge = np.linalg.norm(uv, axis=1) + w_eff[oo]
        ap_margin = min(ap_margin, float(np.min(ap - r_edge)))
        # spot separation among spots BEFORE the exit pass
        pre = oo < exit_idx
        uvp, oop = uv[pre], oo[pre]
        for i in range(len(uvp)):
            for j in range(i + 1, len(uvp)):
                d = float(np.linalg.norm(uvp[i] - uvp[j]))
                if d < 1e-3:            # coincident revisit, not two spots
                    continue
                min_sep = min(min_sep, d)
                sep_margin = min(sep_margin,
                                 d - float(w_eff[oop[i]] + w_eff[oop[j]]))
    out["ap_margin_mm"] = ap_margin
    out["sep_margin_mm"] = sep_margin if np.isfinite(sep_margin) else np.inf
    out["min_sep_mm"] = min_sep if np.isfinite(min_sep) else 0.0

    # --- remaining physics bookkeeping ---
    n_refl = exit_idx - 1              # hole passes are not reflections
    out["throughput"] = float(TRUNC ** 2 * REFL ** n_refl)
    out["w_max_mm"] = float(np.max(w_eff[:exit_idx + 1]))
    out["stab_tan"] = float(res.stability_tan)
    out["stab_sag"] = float(res.stability_sag)
    out["aoi_deg"] = float(np.mean(res.aoi[1:exit_idx])) if exit_idx > 1 else 0.0
    v_all = np.concatenate([foot[k][foot[k][:, 2] <= exit_idx, 1]
                            for k in range(cfg.N) if len(foot[k])])
    out["H_req_mm"] = float(2.0 * (np.max(np.abs(v_all)) + W0 + 3.0))
    out["envelope_mm"] = 2.0 * (cfg.R_ring + RADIAL_ALLOWANCE)

    checks = [
        (out["opl_m"] >= OPL_MIN_M, f"OPL {out['opl_m']:.2f} m < {OPL_MIN_M}"),
        (out["exit_miss_mm"] < EXIT_TOL, "exit miss"),
        (out["hole_margin_mm"] >= 0.0, "intermediate spot leaks into hole"),
        (out["ap_margin_mm"] >= 0.0, "beam edge clips aperture"),
        (out["sep_margin_mm"] >= 0.0, "spots overlap"),
        (abs(out["stab_tan"]) <= 1.0, "tangentially unstable"),
        (abs(out["stab_sag"]) <= 1.0, "sagittally unstable"),
        (out["envelope_mm"] <= ENVELOPE_MAX, "envelope too big"),
    ]
    bad = [msg for okc, msg in checks if not okc]
    out["feasible"] = not bad
    out["reason"] = "" if not bad else "; ".join(bad)
    return out


def _polish_objective(x: np.ndarray, base: Dict) -> float:
    p = dict(base)
    p["R_ring"] = float(np.clip(x[0], R_RING_MIN, R_RING_MAX))
    p["input_offset_z"] = float(x[1])
    p["input_angle"] = float(x[2])
    r = evaluate(p)
    if not np.isfinite(r["exit_miss_mm"]):
        return 1e3
    obj = r["exit_miss_mm"]
    # soft margins keep the pattern comfortably legal, not just barely
    for key, want, wt in (("hole_margin_mm", 0.30, 5.0),
                          ("sep_margin_mm", 0.20, 5.0),
                          ("ap_margin_mm", 0.30, 5.0)):
        v = r[key]
        if np.isfinite(v):
            obj += wt * max(0.0, want - v)
    if r["n_exit"] and r["n_exit"] != base["n_target"]:
        obj += 2.0 * abs(r["n_exit"] - base["n_target"]) / base["N"]
    return obj


def polish(base: Dict) -> Dict:
    from scipy.optimize import minimize
    x0 = np.array([base["R_ring"], base["input_offset_z"],
                   base["input_angle"]])
    best = minimize(_polish_objective, x0, args=(base,),
                    method="Nelder-Mead",
                    options=dict(maxfev=160, xatol=1e-3, fatol=1e-3,
                                 initial_simplex=x0 + np.array(
                                     [[0, 0, 0], [0.4, 0, 0],
                                      [0, 0.3, 0], [0, 0, 0.004]])))
    p = dict(base)
    p["R_ring"] = float(np.clip(best.x[0], R_RING_MIN, R_RING_MAX))
    p["input_offset_z"] = float(best.x[1])
    p["input_angle"] = float(best.x[2])
    out = evaluate(p)
    out["polished"] = True
    return out


# grids of launch seeds per family (sagittal offset must respect aperture)
SEED_Z = {"one_inch": (2.5, 4.0, 5.5, 7.0), "half_inch": (1.8, 2.6, 3.4)}
SEED_ANG = (-0.032, -0.024, -0.016, -0.008, 0.008, 0.016, 0.024, 0.032)


def stage_b(dfa: pd.DataFrame, top: int, workers: int,
            polish_top: int) -> pd.DataFrame:
    cands = dfa.head(top).to_dict("records")
    jobs: List[Dict] = []
    for c in cands:
        for z0 in SEED_Z[c["family"]]:
            for ang in SEED_ANG:
                jobs.append(dict(
                    family=c["family"], sku=c["sku"], roc=c["roc"],
                    N=int(c["N"]), chord_skip=int(c["chord_skip"]),
                    R_ring=float(c["R_ring"]), n_target=int(c["n_exit"]),
                    input_offset_z=z0, input_angle=ang))
    print(f"Stage B: {len(jobs)} seed traces over {len(cands)} candidates")
    results: List[Dict] = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(evaluate, jobs, chunksize=8)):
            results.append(r)
            if (i + 1) % 500 == 0:
                print(f"  {i + 1}/{len(jobs)} traces "
                      f"({time.time() - t0:.0f}s)")
    dfb = pd.DataFrame(results)

    # pick best seed per candidate design, then polish the most promising
    key = ["family", "sku", "N", "chord_skip", "n_target"]
    dfb["seed_score"] = (
        dfb["feasible"].astype(float) * 100.0
        - dfb["exit_miss_mm"].clip(upper=20)
        + dfb[["hole_margin_mm", "sep_margin_mm", "ap_margin_mm"]]
        .clip(-5, 2).sum(axis=1))
    best_seed = (dfb.sort_values("seed_score", ascending=False)
                 .groupby(key, as_index=False).first())
    to_polish = best_seed.sort_values(
        ["feasible", "throughput", "seed_score"],
        ascending=[False, False, False]).head(polish_top).to_dict("records")
    print(f"Stage B: polishing {len(to_polish)} best candidates")
    polished: List[Dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(polish, {k: p[k] for k in (
            "family", "sku", "roc", "N", "chord_skip", "R_ring",
            "n_target", "input_offset_z", "input_angle")})
            for p in to_polish]
        for f in as_completed(futs):
            polished.append(f.result())
    dfp = pd.DataFrame(polished)
    return dfb, dfp


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--top", type=int, default=300,
                    help="Stage A candidates carried into Stage B")
    ap.add_argument("--polish-top", type=int, default=60)
    ap.add_argument("--out-dir", default=os.path.join(_HERE, "results"))
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    t0 = time.time()
    dfa = stage_a()
    print(f"Stage A: {len(dfa)} analytic candidates "
          f"({time.time() - t0:.0f}s)")
    dfa.to_csv(os.path.join(args.out_dir, "stage_a_candidates.csv"),
               index=False)
    if not len(dfa):
        print("No analytic candidates -- constraints are infeasible.")
        return 1

    dfb, dfp = stage_b(dfa, top=args.top, workers=args.workers,
                       polish_top=args.polish_top)
    dfb.to_csv(os.path.join(args.out_dir, "stage_b_seeds.csv"), index=False)
    dfp = dfp.sort_values(["feasible", "opl_m", "throughput"],
                          ascending=[False, False, False])
    dfp.to_csv(os.path.join(args.out_dir, "stage_b_polished.csv"),
               index=False)

    feas = dfp[dfp["feasible"]]
    print(f"\n{len(feas)} fully feasible designs "
          f"(of {len(dfp)} polished)")
    cols = ["family", "sku", "N", "chord_skip", "R_ring", "n_exit",
            "opl_m", "throughput", "envelope_mm", "H_req_mm",
            "exit_miss_mm", "hole_margin_mm", "sep_margin_mm",
            "ap_margin_mm", "min_sep_mm", "w_max_mm", "aoi_deg"]
    with pd.option_context("display.width", 250):
        print(feas[cols].head(20).to_string(index=False))
    print(f"\nTotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
