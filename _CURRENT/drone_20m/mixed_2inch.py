"""Mixed-SKU rings on two-inch apertures: the shot at beating 29 m robust.

Lessons composed: (1) mixed closures unlock (N, s, k) combinations no
single ROC closes; (2) on 1-inch apertures they cannot hold separation
AND aperture headroom simultaneously (diagnosed: the margin-aware
winners clip under 0.25 mm ROC error because the pattern rides the
aperture edge); (3) the 2-inch family's 22.9 mm clear aperture holds
both margins easily at k = 19 (the robust 19.04 m uniform design).
Therefore: alternate CM508 curvatures on N = 8 (even N, odd s = 3),
demand separation AND aperture margin in the objective, target
k = 21-33 (21.1-33.2 m at the packing ring radius).

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mixed_2inch.py --workers 6
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

from mixed_sku_explore import (analytic_candidates,               # noqa: E402
                               circ_dist_pi_arr, theta2_arr)
from tmpc_platform_v5 import TMPCConfig, simulate_tmpc            # noqa: E402
from tmpc_platform_v5.physics import (MirrorPerturbation,          # noqa: E402
                                      mirror_footprints)

WAVELENGTH = 1.654e-3
HOLE_R = 1.3
REFL = 0.999
APERTURE = 22.9            # CM508 clear-aperture radius [mm]
MIRROR_DIA = 50.8
RADIAL_ALLOWANCE = 23.0
ENVELOPE_MAX = 190.0
SEP_WANT = 0.60
AP_WANT = 2.0
HOLE_MARGIN = 0.45
K_KEEP = tuple(range(17, 34, 2))

SKU = {150.0: "CM508-075-M01", 200.0: "CM508-100-M01",
       300.0: "CM508-150-M01", 400.0: "CM508-200-M01",
       500.0: "CM508-250-M01", 1000.0: "CM508-500-M01",
       1500.0: "CM508-750-M01", 2000.0: "CM508-1000-M01"}

COMBOS = [(8, 3, 300.0, 400.0), (8, 3, 400.0, 500.0),
          (8, 3, 1000.0, 1500.0), (8, 3, 500.0, 1000.0),
          (8, 3, 200.0, 300.0), (8, 3, 1500.0, 2000.0)]


def make_cfg2(N, s, ra, rb, r_ring, ang_t, ang_s, off_z, w0, waist_frac,
              n_passes):
    chord = 2.0 * r_ring * np.sin(np.pi * s / N)
    cfg = TMPCConfig(
        N=N, R_ring=r_ring, H=60.0, R_t=ra, R_s=ra,
        mirror_aperture=APERTURE, chord_skip=s, n_passes=n_passes,
        wavelength=WAVELENGTH, w0=w0, M2=1.0,
        input_waist_offset=float(np.clip(waist_frac, 0.0, 1.5)) * chord / 2,
        input_offset_z=off_z, input_angle=ang_t, input_angle_sag=ang_s,
        reflectivity=REFL, hole_radius=HOLE_R)
    perts = [MirrorPerturbation(dR_t=(rb - ra) if (q % 2) else 0.0,
                                dR_s=(rb - ra) if (q % 2) else 0.0)
             for q in range(N)]
    return cfg, perts


def visits_of(cfg, perts):
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < cfg.N + 1:
        return res, []
    foot = mirror_footprints(res.spot_pattern[:n],
                             res.mirror_sequence[:n], cfg)
    if 0 not in foot:
        return res, []
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    out = [(int(o), float(np.hypot(u - hole[0], v - hole[1])),
            float(w_eff[min(int(o), len(w_eff) - 1)]))
           for u, v, o in foot[0]]
    return res, sorted(out)


def metrics_of(cfg, perts, n_exit):
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    if n < n_exit:
        return None
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    clear, sep, ext = np.inf, np.inf, 0.0
    for m, arr in foot.items():
        uv = arr[:, :2]
        ws = w_eff[np.clip(arr[:, 2].astype(int), 0, len(w_eff) - 1)]
        ext = max(ext, float((np.hypot(uv[:, 0], uv[:, 1]) + ws).max()))
        if m == 0:
            for u, v, o in arr:
                j = int(o)
                if j == 0 or j >= n_exit - 1:
                    continue
                dd = float(np.hypot(u - hole[0], v - hole[1]))
                wj = float(w_eff[min(j, len(w_eff) - 1)])
                clear = min(clear, dd - (HOLE_R + wj))
        if len(arr) >= 2:
            for i in range(len(uv)):
                for jj in range(i + 1, len(uv)):
                    dd = float(np.hypot(*(uv[i] - uv[jj])))
                    sep = min(sep, dd - (float(ws[i]) + float(ws[jj])))
    return dict(opl_m=res.opl / 1000.0, sep=float(sep), clear=float(clear),
                ap_margin=float(APERTURE - ext),
                w_max=float(w_eff.max()))


def refine2(cand):
    N, s = cand["N"], cand["s"]
    ra, rb = cand["roc_a"], cand["roc_b"]
    n_exit = cand["n_exit"]
    n_pass = n_exit + N + 4

    def objective(x):
        r, at, asag, oz, w0, wf = x
        if not (60.0 <= r <= 72.0 and 0.2 <= w0 <= 0.7):
            return 1e6
        cfg, perts = make_cfg2(N, s, ra, rb, r, at, asag, oz, w0, wf,
                               n_pass)
        _, vis = visits_of(cfg, perts)
        vv = [v for v in vis if abs(v[0] - n_exit) <= 1]
        if not vv:
            return 1e5
        j, miss, _ = vv[0]
        pen = 50.0 * miss
        for jj, m2, w2 in vis:
            if 0 < jj < j and m2 < HOLE_R + w2 + HOLE_MARGIN:
                pen += 10.0 * (HOLE_R + w2 + HOLE_MARGIN - m2)
        if miss < 0.5:
            cfg2, perts2 = make_cfg2(N, s, ra, rb, r, at, asag, oz, w0,
                                     wf, n_exit)
            met = metrics_of(cfg2, perts2, n_exit)
            if met:
                pen += 10.0 * max(0.0, SEP_WANT - met["sep"])
                pen += 6.0 * max(0.0, AP_WANT - met["ap_margin"])
                pen += 10.0 * max(0.0, HOLE_MARGIN - met["clear"])
        return pen

    best = None
    for at0, as0, w00 in ((0.030, 0.030, 0.35), (0.055, 0.040, 0.45)):
        x0 = np.array([cand["r_ring"], at0, as0, 0.0, w00, 0.55])
        res = minimize(objective, x0, method="Nelder-Mead",
                       options=dict(maxiter=260, xatol=2e-5, fatol=1e-4))
        if best is None or res.fun < best.fun:
            best = res
        if best.fun < 0.05:
            break
    r, at, asag, oz, w0, wf = best.x
    cfg2, perts2 = make_cfg2(N, s, ra, rb, r, at, asag, oz, w0, wf, n_exit)
    met = metrics_of(cfg2, perts2, n_exit) or {}
    _, vis = visits_of(*make_cfg2(N, s, ra, rb, r, at, asag, oz, w0, wf,
                                  n_pass))
    vv = [v for v in vis if abs(v[0] - n_exit) <= 1]
    miss = vv[0][1] if vv else np.inf
    env = 2 * (r + RADIAL_ALLOWANCE)
    out = dict(N=N, s=s, roc_a=ra, roc_b=rb, k=cand["k"], n_exit=n_exit,
               r_ring=float(r), ang_t=float(at), ang_s=float(asag),
               off_z=float(oz), w0=float(w0), waist_frac=float(wf),
               exit_miss=float(miss), envelope_mm=float(env),
               throughput=REFL ** max(0, n_exit - 1),
               sku_a=SKU.get(ra, str(ra)), sku_b=SKU.get(rb, str(rb)),
               **{k: met.get(k, np.nan) for k in
                  ("opl_m", "sep", "clear", "ap_margin", "w_max")})
    out["feasible"] = bool(miss < 0.05 and met.get("sep", -9) > 0.0
                           and met.get("clear", -9) > 0.0
                           and met.get("ap_margin", -9) > 0.8
                           and env <= ENVELOPE_MAX)
    return out


def explore2(combo):
    # packing floor for 50.8 mm mirrors at N=8
    r_lo = (MIRROR_DIA + 1.0) / (2 * np.sin(np.pi / combo[0])) + 0.2
    try:
        cands = [c for c in analytic_candidates(combo, r_lo, 72.0)
                 if c["k"] in K_KEEP][:4]
        return [refine2(c) for c in cands]
    except Exception as exc:                                   # noqa: BLE001
        return [dict(N=combo[0], s=combo[1], roc_a=combo[2],
                     roc_b=combo[3], feasible=False, k=0, n_exit=0,
                     reason=f"error: {exc}")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    print(f"{len(COMBOS)} two-inch mixed combos (N=8, s=3), "
          f"k {K_KEEP[0]}..{K_KEEP[-1]}, sep>={SEP_WANT}, ap>={AP_WANT}")
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, out in enumerate(ex.map(explore2, COMBOS)):
            for r in out:
                rows.append(r)
                tag = "FEASIBLE" if r.get("feasible") else "--"
                print(f"  [{i+1}/{len(COMBOS)}] {r['roc_a']:.0f}/"
                      f"{r['roc_b']:.0f} k={r.get('k',0)} "
                      f"opl={r.get('opl_m', 0):.1f} m "
                      f"env={r.get('envelope_mm', 0):.0f} "
                      f"miss={r.get('exit_miss', 9):.3f} "
                      f"sep={r.get('sep', -9):.2f} "
                      f"ap={r.get('ap_margin', -9):.1f} {tag}", flush=True)
    pd.DataFrame(rows).to_csv(
        os.path.join(_HERE, "designs", "mixed_2inch.csv"), index=False)
    feas = [r for r in rows if r.get("feasible")]
    print(f"\n{len(feas)} feasible two-inch mixed designs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
