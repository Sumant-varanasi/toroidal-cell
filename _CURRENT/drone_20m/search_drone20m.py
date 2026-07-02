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
      * re-entrance closure: after n = k*N bounces the tangential AND
        sagittal transverse phases n*theta both sit near a multiple of
        2*pi (beam lands back on the entrance hole and exits),
      * constellation quality: with M = round(n*theta/2pi), gcd(M, k) = 1
        in BOTH planes, so the k spots on each mirror are evenly spaced
        (no clustered/coincident spots, maximal hole clearance) -- the
        star-polygon re-entrance rule of the Herriott/Tuzson literature
        applied to the transverse oscillation,
      * the amplitude the pattern needs for spot separation,
        A_req = sep_need / (2 sin(pi/k)), fits inside the clear aperture,
      * estimated OPL = n * chord in the 19.5 - 26 m window.

Stage B -- exact verification. Each surviving candidate is seeded with
    launch offsets/angles sized from A_req, then refined with a fine
    R_ring scan (the accumulated transverse phase moves ~1 rad per mm of
    ring radius, so the machined ring radius is the natural closure-tuning
    knob against a catalog-locked ROC) followed by a local Nelder-Mead
    polish of (R_ring, input_offset_z, input_angle). Every physical check
    is enforced on the traced path:
      * ray survives (no geometric clipping),
      * beam edge (1/e^2) stays inside the clear aperture at every bounce,
      * beam exits through the entrance hole (first hole re-visit) at
        >= 19.5 m OPL,
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
from math import gcd
from typing import Dict, List

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

OPL_MIN_M = 19.5         # default verified-OPL floor (per-class override)
OPL_EST_LO_M = 4.5       # Stage A estimate window (classes filter later)
OPL_EST_HI_M = 26.5
N_EXIT_MIN = 40          # bounce-count window (throughput vs OPL trade)
N_EXIT_MAX = 208
K_SET = (5, 7, 9, 11, 13)  # spots per mirror -- odd only: for even k
#   the tangential pi-slot coincides with a sagittal near-return and an
#   intermediate spot can leak into the hole (star-polygon parity rule)
LISSAJOUS_EXTENT = 1.30    # 2-D constellation reaches ~1.3x the per-plane
#   amplitude, so the aperture-fit test must use it (1.0 was optimistic)
FAMILIES_USE = ("one_inch",)   # 1" confirmed by user; with N<=16 the
#   half-inch aperture cannot reach the 20 m class anyway
EXIT_TOL = 0.5           # spot-centre distance counting as "through the hole"
PHASE_TOL_T = 0.45       # tan closure tol [rad] -- R_ring scan zeroes this
PHASE_TOL_S = 0.30       # sag closure tol [rad] -- amplitude polish absorbs
SEP_NEED = 3.2           # adjacent-spot spacing target ~ 2*w_typ + margin
W_TYP = 1.45             # typical in-cell beam radius for sizing [mm]

R_RING_MAX = (ENVELOPE_MAX - 2.0 * RADIAL_ALLOWANCE) / 2.0        # 77 mm
R_RING_MIN = 25.0
N_RANGE = range(8, 17)   # mirror count 8..16 (user constraint, 2026-07-02)


# ---------------------------------------------------------------------------
# Stage A -- analytic prescreen
# ---------------------------------------------------------------------------
def _circ_dist(phase: np.ndarray) -> np.ndarray:
    """Distance of a phase [rad] from the nearest multiple of 2*pi."""
    return np.abs((phase + np.pi) % (2.0 * np.pi) - np.pi)


def stage_a() -> pd.DataFrame:
    rows: List[Dict] = []
    r_grid = np.arange(R_RING_MIN, R_RING_MAX + 1e-9, 0.25)
    for family in FAMILIES_USE:
        fam = FAMILIES[family]
        ap = fam["clear_aperture_radius_mm"]
        diam = fam["diameter_mm"]
        # max per-plane amplitude whose 2-D constellation still fits
        A_cap = (ap - W_TYP - 0.3) / LISSAJOUS_EXTENT
        for sku, _f, roc in fam["catalog"]:
            for N in N_RANGE:
                pack_ok = 2.0 * r_grid * np.sin(np.pi / N) >= diam + PACK_GAP
                if not pack_ok.any():
                    continue
                for s in range(2, N // 2 + 1):
                    if gcd(N, s) != 1:
                        continue
                    L = 2.0 * r_grid * np.sin(np.pi * s / N)
                    ci = np.sin(np.pi * s / N)  # cos(AOI), AOI = pi/2 - pi s/N
                    ct = 1.0 - L / (roc * ci)   # tangential unit-cell cos
                    cs = 1.0 - L * ci / roc     # sagittal unit-cell cos
                    stable = (np.abs(ct) < 1 - 1e-4) & (np.abs(cs) < 1 - 1e-4)
                    ok0 = pack_ok & stable
                    if not ok0.any():
                        continue
                    th_t = np.arccos(np.clip(ct, -1, 1))
                    th_s = np.arccos(np.clip(cs, -1, 1))
                    for k in K_SET:
                        n = k * N
                        if n < N_EXIT_MIN or n > N_EXIT_MAX:
                            continue
                        A_req = SEP_NEED / (2.0 * np.sin(np.pi / k))
                        if A_req > A_cap:
                            break              # grows with k
                        opl_m = n * L * 1e-3
                        # tangential launch is a zero-crossing (hole at
                        # u=0): position closes at phase 0 OR pi.
                        e_t = np.minimum(_circ_dist(n * th_t),
                                         _circ_dist(n * th_t - np.pi))
                        # sagittal: cos-mode (height offset, hole at v=A,
                        # closes at 0) or sin-mode (vertical tilt launch,
                        # hole at v=0, closes at 0 or pi)
                        e_s_cos = _circ_dist(n * th_s)
                        e_s_sin = np.minimum(e_s_cos,
                                             _circ_dist(n * th_s - np.pi))
                        base_ok = (ok0 & (e_t < PHASE_TOL_T)
                                   & (opl_m >= OPL_EST_LO_M)
                                   & (opl_m <= OPL_EST_HI_M))
                        for mode_s, e_s in (("cos", e_s_cos),
                                            ("sin", e_s_sin)):
                            ok = base_ok & (e_s < PHASE_TOL_S)
                            if not ok.any():
                                continue
                            idxs = np.where(ok)[0]
                            # constellation quality: gcd(M, k) = 1 in both
                            # planes -> k evenly-spaced spots per mirror
                            M_t = np.rint(n * th_t[idxs]
                                          / (2 * np.pi)).astype(int)
                            M_s = np.rint(n * th_s[idxs]
                                          / (2 * np.pi)).astype(int)
                            cop = np.array([gcd(mt % k, k) == 1
                                            and gcd(ms % k, k) == 1
                                            for mt, ms in zip(M_t, M_s)])
                            idxs = idxs[cop]
                            if not len(idxs):
                                continue
                            best = idxs[np.argsort(e_s[idxs])[:2]]
                            for i in best:
                                rows.append(dict(
                                    family=family, sku=sku, roc=float(roc),
                                    N=N, chord_skip=s,
                                    R_ring=float(r_grid[i]),
                                    chord_mm=float(L[i]),
                                    aoi_deg=float(np.degrees(
                                        np.pi / 2 - np.pi * s / N)),
                                    n_exit=n, spots_per_mirror=k,
                                    mode_s=mode_s,
                                    A_req_mm=float(A_req),
                                    th_t=float(th_t[i]),
                                    th_s=float(th_s[i]),
                                    opl_est_m=float(opl_m[i]),
                                    phase_err_t=float(e_t[i]),
                                    phase_err_s=float(e_s[i]),
                                    throughput_est=float(
                                        TRUNC ** 2 * REFL ** (n - 1)),
                                    envelope_mm=float(
                                        2 * (r_grid[i] + RADIAL_ALLOWANCE)),
                                ))
    df = pd.DataFrame(rows)
    if len(df):
        # prefer fewer bounces, then roomier constellations, then closure
        df = df.sort_values(
            ["throughput_est", "A_req_mm", "phase_err_s"],
            ascending=[False, True, True]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Stage B -- exact trace + full physical checks
# ---------------------------------------------------------------------------
def waist_offset_for(w0_waist: float) -> float:
    """Waist-past-hole distance so the beam radius AT the hole equals W0.

    Converging injection: the user-fixed 1.3 mm is the beam size at the
    entrance hole; the actual waist w0_waist (<= W0) sits inside the cell.
    """
    w0_waist = min(float(w0_waist), W0)
    zR = np.pi * w0_waist ** 2 / (M2 * WAVELENGTH)
    return float(zR * np.sqrt(max((W0 / w0_waist) ** 2 - 1.0, 0.0)))


def evaluate(p: Dict) -> Dict:
    """Trace one candidate and run every physical check.

    p needs: family, sku, roc, N, chord_skip, R_ring, n_target,
             input_offset_z, input_angle; optional input_angle_sag,
             w0_waist (in-cell waist radius; W0 = legacy waist-at-hole),
             exit_at_target.
    """
    fam = FAMILIES[p["family"]]
    ap = fam["clear_aperture_radius_mm"]
    out = dict(p)
    out.update(feasible=False, reason="", opl_m=0.0, n_exit=0,
               throughput=0.0, exit_miss_mm=np.inf, hole_margin_mm=-np.inf,
               ap_margin_mm=-np.inf, sep_margin_mm=-np.inf, min_sep_mm=0.0,
               w_max_mm=0.0, H_req_mm=0.0, stab_tan=np.nan, stab_sag=np.nan,
               aoi_deg=np.nan)
    n_passes = min(int(p["n_target"]) + 2 * int(p["N"]), 2 * N_EXIT_MAX)
    w0_waist = float(np.clip(p.get("w0_waist", W0), 0.25, W0))
    try:
        cfg = TMPCConfig(
            N=int(p["N"]), R_ring=float(p["R_ring"]), H=40.0,
            R_t=float(p["roc"]), R_s=float(p["roc"]),
            mirror_aperture=ap, chord_skip=int(p["chord_skip"]),
            n_passes=n_passes, wavelength=WAVELENGTH, w0=w0_waist, M2=M2,
            input_waist_offset=waist_offset_for(w0_waist),
            input_offset_z=float(p["input_offset_z"]),
            input_angle=float(p["input_angle"]),
            input_angle_sag=float(p.get("input_angle_sag", 0.0)),
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
    n_target = int(p["n_target"])
    # first honest hole crossing
    first_cross = None
    for r in np.argsort(order):
        if order[r] == 0:
            continue
        if dists[r] < EXIT_TOL:
            first_cross = r
            break
    out["early_exit"] = int(first_cross is not None
                            and order[first_cross] < n_target)
    if p.get("exit_at_target"):
        # optimisation mode: margins and miss are always evaluated at the
        # designed exit bounce, so the objective stays continuous across
        # the exit threshold instead of walling at EXIT_TOL
        tgt = np.where(order == n_target)[0]
        if not len(tgt):
            out["reason"] = "target bounce missing"
            return out
        exit_row = int(tgt[0])
    else:
        if first_cross is None:
            out["reason"] = "never returns to hole"
            tgt = np.where(order == n_target)[0]
            if len(tgt):
                out["exit_miss_mm"] = float(dists[int(tgt[0])])
            return out
        exit_row = int(first_cross)
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
    exit_overlap = float(np.exp(-2.0 * (out["exit_miss_mm"] / W0) ** 2))
    out["throughput"] = float(TRUNC ** 2 * REFL ** n_refl * exit_overlap)
    out["w_max_mm"] = float(np.max(w_eff[:exit_idx + 1]))
    out["stab_tan"] = float(res.stability_tan)
    out["stab_sag"] = float(res.stability_sag)
    out["aoi_deg"] = float(np.mean(res.aoi[1:exit_idx])) if exit_idx > 1 else 0.0
    v_all = np.concatenate([foot[k][foot[k][:, 2] <= exit_idx, 1]
                            for k in range(cfg.N) if len(foot[k])])
    out["H_req_mm"] = float(2.0 * (np.max(np.abs(v_all)) + W0 + 3.0))
    out["envelope_mm"] = 2.0 * (cfg.R_ring + RADIAL_ALLOWANCE)

    opl_min = float(p.get("opl_min", OPL_MIN_M))
    env_max = float(p.get("envelope_max", ENVELOPE_MAX))
    checks = [
        (out["opl_m"] >= opl_min, f"OPL {out['opl_m']:.2f} m < {opl_min}"),
        (out["exit_miss_mm"] < 0.35, "exit miss > 0.35 mm"),
        (out["hole_margin_mm"] >= 0.0, "intermediate spot leaks into hole"),
        (out["ap_margin_mm"] >= 0.0, "beam edge clips aperture"),
        (out["sep_margin_mm"] >= 0.0, "spots overlap"),
        (abs(out["stab_tan"]) <= 1.0, "tangentially unstable"),
        (abs(out["stab_sag"]) <= 1.0, "sagittally unstable"),
        (out["envelope_mm"] <= env_max, "envelope too big"),
    ]
    bad = [msg for okc, msg in checks if not okc]
    out["feasible"] = not bad
    out["reason"] = "" if not bad else "; ".join(bad)
    return out


def _objective(r: Dict) -> float:
    """Composite score for refinement: exit miss + soft margin shortfalls.

    Meant to be fed target-exit evaluations (exit_at_target=True) so the
    landscape is continuous across the hole-capture threshold.
    """
    if not np.isfinite(r["exit_miss_mm"]):
        return 1e3
    obj = r["exit_miss_mm"]
    if not r["n_exit"]:
        obj += 1.0
    for key, want, wt in (("hole_margin_mm", 0.30, 5.0),
                          ("sep_margin_mm", 0.35, 8.0),
                          ("ap_margin_mm", 0.30, 5.0)):
        v = r[key]
        if np.isfinite(v):
            obj += wt * max(0.0, want - v)
    if r.get("early_exit"):
        obj += 3.0
    if r["n_exit"] and r["n_exit"] != r["n_target"]:
        obj += 2.0 * abs(r["n_exit"] - r["n_target"]) / r["N"]
    return obj


def _obj_eval(p: Dict) -> float:
    return _objective(evaluate({**p, "exit_at_target": True}))


def _r_max_of(base: Dict) -> float:
    env_max = float(base.get("envelope_max", ENVELOPE_MAX))
    return (env_max - 2.0 * RADIAL_ALLOWANCE) / 2.0


def _polish_objective(x: np.ndarray, base: Dict) -> float:
    p = dict(base)
    p["R_ring"] = float(np.clip(x[0], R_RING_MIN, _r_max_of(base)))
    p["input_offset_z"] = float(x[1])
    p["input_angle"] = float(x[2])
    p["input_angle_sag"] = float(x[3])
    p["w0_waist"] = float(np.clip(x[4], 0.30, W0))
    return _obj_eval(p)


def scan_refine(base: Dict) -> Dict:
    """Fine R_ring scan (closure tuning) + local Nelder-Mead polish.

    The accumulated transverse phase moves ~1 rad per mm of ring radius
    (the closure valley itself is only ~0.02 mm wide), so a coarse scan
    localises the valley, a 4-DOF Nelder-Mead trims the per-plane
    mismatch through the launch amplitudes (whose aberration-mediated
    phase pull is the only differential knob left once the ROC is
    catalog-locked), and a final micro-scan of R_ring nails the floor.
    """
    from scipy.optimize import minimize
    base = {**{"input_angle_sag": 0.0, "w0_waist": W0}, **base}
    base.pop("exit_at_target", None)   # honest verdict at the end
    r_max = _r_max_of(base)
    best_obj, best_R = np.inf, base["R_ring"]
    for dR in np.arange(-1.5, 1.5 + 1e-9, 0.02):
        R = float(np.clip(base["R_ring"] + dR, R_RING_MIN, r_max))
        o = _obj_eval({**base, "R_ring": R})
        if o < best_obj:
            best_obj, best_R = o, R
    x0 = np.array([best_R, base["input_offset_z"], base["input_angle"],
                   base["input_angle_sag"], base["w0_waist"]])
    res = minimize(_polish_objective, x0, args=(base,),
                   method="Nelder-Mead",
                   options=dict(maxfev=280, xatol=1e-5, fatol=1e-4,
                                initial_simplex=x0 + np.array(
                                    [[0, 0, 0, 0, 0], [0.01, 0, 0, 0, 0],
                                     [0, 0.20, 0, 0, 0],
                                     [0, 0, 0.0012, 0, 0],
                                     [0, 0, 0, 0.0012, 0],
                                     [0, 0, 0, 0, -0.10]])))
    p = dict(base)
    p["R_ring"] = float(np.clip(res.x[0], R_RING_MIN, r_max))
    p["input_offset_z"] = float(res.x[1])
    p["input_angle"] = float(res.x[2])
    p["input_angle_sag"] = float(res.x[3])
    p["w0_waist"] = float(np.clip(res.x[4], 0.30, W0))
    # micro-scan of R_ring around the polished point
    best_obj, best_R = np.inf, p["R_ring"]
    for dR in np.arange(-0.03, 0.03 + 1e-9, 0.002):
        R = float(np.clip(p["R_ring"] + dR, R_RING_MIN, r_max))
        o = _obj_eval({**p, "R_ring": R})
        if o < best_obj:
            best_obj, best_R = o, R
    p["R_ring"] = best_R
    out = evaluate(p)                 # honest first-crossing verdict
    out["polished"] = True
    return out


def _seed_jobs(c: Dict) -> List[Dict]:
    """Launch seeds sized from the analytic pattern amplitude A_req.

    Tangential amplitude comes from the in-plane tilt. The sagittal
    amplitude comes from either a height offset (cos-mode, hole at the top
    of the vertical oscillation) or a vertical tilt (sin-mode, hole at its
    zero-crossing), per the Stage A closure mode.
    """
    A = float(c["A_req_mm"])
    L = float(c["chord_mm"])
    ang_t = A * np.sin(float(c["th_t"])) / L
    ang_s = A * np.sin(float(c["th_s"])) / L
    # eigenmode spot size on the mirrors (per plane): w^2 = M2*lam*L/(pi sin
    # theta); a waist near sqrt(w_eig*W0) halves the breathing ratio
    w_eig = float(np.sqrt(M2 * WAVELENGTH * L / np.pi
                          / np.sqrt(np.sin(c["th_t"]) * np.sin(c["th_s"]))))
    w_match = float(np.clip(np.sqrt(w_eig * W0), 0.35, W0))
    jobs = []
    # amplitude-ratio seeds: equal, enlarged, and asymmetric Lissajous
    # (unequal per-plane amplitudes spread the worst-pair spot distance)
    for f_t, f_s in ((1.0, 1.0), (1.3, 1.3), (1.5, 1.0), (1.0, 1.5)):
        for sign in (+1.0, -1.0):
            for w0w in (W0, w_match):
                j = dict(
                    family=c["family"], sku=c["sku"], roc=float(c["roc"]),
                    N=int(c["N"]), chord_skip=int(c["chord_skip"]),
                    R_ring=float(c["R_ring"]), n_target=int(c["n_exit"]),
                    mode_s=c["mode_s"], input_angle=sign * ang_t * f_t,
                    w0_waist=w0w,
                    size_class=c.get("size_class", "D190"),
                    envelope_max=c.get("envelope_max", ENVELOPE_MAX),
                    opl_min=c.get("opl_min", OPL_MIN_M),
                    exit_at_target=True)   # continuous scoring for seeds
                if c["mode_s"] == "cos":
                    j["input_offset_z"] = A * f_s
                    j["input_angle_sag"] = 0.0
                else:
                    j["input_offset_z"] = 0.0
                    j["input_angle_sag"] = ang_s * f_s
                jobs.append(j)
    return jobs


def stage_b(cands: List[Dict], workers: int, refine_top: int):
    jobs: List[Dict] = []
    for c in cands:
        jobs.extend(_seed_jobs(c))
    print(f"  seeds: {len(jobs)} traces over {len(cands)} candidates",
          flush=True)
    results: List[Dict] = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(evaluate, jobs, chunksize=8)):
            results.append(r)
            if (i + 1) % 1000 == 0:
                print(f"    {i + 1}/{len(jobs)} "
                      f"({time.time() - t0:.0f}s)", flush=True)
    dfb = pd.DataFrame(results)

    key = ["family", "sku", "N", "chord_skip", "n_target", "mode_s"]
    dfb["seed_score"] = -dfb.apply(_objective, axis=1)
    best_seed = (dfb.sort_values("seed_score", ascending=False)
                 .groupby(key, as_index=False).first())
    to_refine = best_seed.sort_values(
        ["seed_score"], ascending=False).head(refine_top).to_dict("records")
    print(f"  refining {len(to_refine)} best candidates", flush=True)
    refined: List[Dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(scan_refine, {k: p[k] for k in (
            "family", "sku", "roc", "N", "chord_skip", "R_ring",
            "n_target", "mode_s", "input_offset_z", "input_angle",
            "input_angle_sag", "w0_waist", "size_class",
            "envelope_max", "opl_min")})
            for p in to_refine]
        for i, f in enumerate(as_completed(futs)):
            refined.append(f.result())
            if (i + 1) % 20 == 0:
                print(f"    refined {i + 1}/{len(to_refine)}", flush=True)
    dfp = pd.DataFrame(refined)
    return dfb, dfp


# ---------------------------------------------------------------------------
# Size classes: (envelope cap [mm], verified-OPL floor [m]). One verified
# design menu per class exposes the size <-> OPL <-> throughput trade.
DEFAULT_CLASSES = ((190.0, 19.5), (160.0, 14.0), (140.0, 10.0),
                   (120.0, 7.0), (110.0, 4.5))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--top-per-class", type=int, default=120)
    ap.add_argument("--refine-top", type=int, default=60)
    ap.add_argument("--out-dir", default=os.path.join(_HERE, "results"))
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    t0 = time.time()
    dfa = stage_a()
    print(f"Stage A: {len(dfa)} analytic candidates "
          f"({time.time() - t0:.0f}s)", flush=True)
    dfa.to_csv(os.path.join(args.out_dir, "stage_a_candidates.csv"),
               index=False)
    if not len(dfa):
        print("No analytic candidates -- constraints are infeasible.")
        return 1

    all_b, all_p = [], []
    for env_cap, opl_min in DEFAULT_CLASSES:
        label = f"D{int(env_cap)}"
        opl_hi = opl_min * 1.45 + 1.5
        sub = dfa[(dfa["envelope_mm"] <= env_cap + 1e-9)
                  & (dfa["opl_est_m"] >= opl_min)
                  & (dfa["opl_est_m"] <= opl_hi)].copy()
        sub = sub.head(args.top_per_class)
        print(f"\n=== class {label}: envelope <= {env_cap:.0f} mm, "
              f"OPL in [{opl_min}, {opl_hi:.1f}] m -- "
              f"{len(sub)} candidates ===", flush=True)
        if not len(sub):
            continue
        recs = sub.to_dict("records")
        for r in recs:
            r["size_class"] = label
            r["envelope_max"] = env_cap
            r["opl_min"] = opl_min
        dfb, dfp = stage_b(recs, workers=args.workers,
                           refine_top=args.refine_top)
        all_b.append(dfb)
        all_p.append(dfp)
        feas = dfp[dfp["feasible"]]
        print(f"  class {label}: {len(feas)} feasible of {len(dfp)}")

    dfb = pd.concat(all_b, ignore_index=True)
    dfp = pd.concat(all_p, ignore_index=True)
    dfb.to_csv(os.path.join(args.out_dir, "stage_b_seeds.csv"), index=False)
    dfp = dfp.sort_values(["size_class", "feasible", "throughput", "opl_m"],
                          ascending=[True, False, False, False])
    dfp.to_csv(os.path.join(args.out_dir, "stage_b_polished.csv"),
               index=False)

    feas = dfp[dfp["feasible"]]
    print(f"\n{len(feas)} fully feasible designs (of {len(dfp)} refined)")
    cols = ["size_class", "sku", "N", "chord_skip", "R_ring", "n_exit",
            "opl_m", "throughput", "envelope_mm", "H_req_mm",
            "exit_miss_mm", "hole_margin_mm", "sep_margin_mm",
            "ap_margin_mm", "min_sep_mm", "w_max_mm", "aoi_deg"]
    with pd.option_context("display.width", 250):
        print(feas[cols].head(30).to_string(index=False))
    print(f"\nTotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
