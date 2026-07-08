"""Physical comparison metrics for the robust design menu.

Computes, per design, from the exact 3-D trace:

1. GAS VOLUME + path-to-volume ratio (PVR)
   * V_full : practical chamber (cylinder of radius R_ring, height =
     1-inch mirror + seal clearance) -- what a simple lid-and-ring
     housing encloses.
   * V_min  : beam-limited chamber (slab just tall enough for the beam
     envelope + 3w clearance, mirrors sealed at their barrels /
     dead volume filled) -- the physical lower bound for this geometry.
   * PVR = OPL / V for both.

2. OVERLAP FACTOR (the professor's question)
   * every same-mirror spot pair: centre distance d, Gaussian field
     amplitude overlap  eta = (2 w_i w_j/(w_i^2+w_j^2)) *
     exp(-d^2/(w_i^2+w_j^2))  and power overlap eta^2,
   * worst pair per design, number of pairs with power overlap > 1e-4,
   * spot-density figure: spots per cm^2 of used mirror area vs
     (2w)^2 footprint -- fraction of mirror face covered by spots.

3. BEAM CROSSINGS in the cell volume: chords cross at large angles;
   for the minimum crossing angle report the fringe period
   Lambda = lambda / (2 sin(phi/2)) and the washout number w/Lambda
   (fringes averaged across the beam -- >>1 means no detectable
   interference on the detector).

4. ENTRY/EXIT COMPARISON hole-in-mirror vs side slot: physical gap
   between adjacent mirror edges, and the pass-count ceiling a side
   slot imposes (first azimuthal return, n = N) vs the hole's
   transverse selectivity (n = k*N).

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/cell_metrics.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from spec_asbuilt import cfg_from_row                             # noqa: E402
from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints            # noqa: E402

MIRROR_DIA = 25.4          # 1" substrate [mm]
SEAL_CLEAR = 2.6           # lid/base clearance around the mirror [mm]
BEAM_CLEAR_W = 3.0         # slab half-height clearance in units of w
BEAM_CLEAR_MM = 1.0        # plus a machining margin [mm]


def load_menu() -> list[dict]:
    rows = []
    for f, lam_nm in (("robust_menu.csv", 1654.0),
                      ("robust_menu_flight.csv", 1654.0),
                      ("robust_menu_h2_flight.csv", 2121.8)):
        p = os.path.join(_HERE, "designs", f)
        if os.path.exists(p):
            d = pd.read_csv(p)
            d = d[d["robust"] | d["robust_trim"]].copy()
            d["lambda_nm"] = lam_nm
            rows.append(d)
    df = pd.concat(rows)
    df["_rr"] = df["R_ring"].round(2)   # H2-native re-closures are distinct
    df = df.drop_duplicates(
        subset=["sku", "N", "chord_skip", "n_exit", "_rr"], keep="first")
    return df.sort_values("opl_m", ascending=False).to_dict("records")


def overlap_amp(d: float, wi: float, wj: float) -> float:
    """Field-amplitude overlap of two TEM00 spots separated by d."""
    s2 = wi * wi + wj * wj
    return float((2.0 * wi * wj / s2) * np.exp(-d * d / s2))


def seg_intersect_2d(p1, p2, p3, p4):
    """Intersection parameter check for segments p1p2 and p3p4 (xy)."""
    d1, d2 = p2 - p1, p4 - p3
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-12:
        return False
    dp = p3 - p1
    t = (dp[0] * d2[1] - dp[1] * d2[0]) / denom
    u = (dp[0] * d1[1] - dp[1] * d1[0]) / denom
    return 0.02 < t < 0.98 and 0.02 < u < 0.98


def metrics_one(row: dict) -> dict:
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    lam_nm = float(row.get("lambda_nm", 1654.0))
    cfg.wavelength = lam_nm * 1e-6      # row w0_waist is native to this lambda
    res = simulate_tmpc(cfg)
    n = res.bounces
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    w_eff = np.maximum(res.w_tangential, res.w_sagittal)
    w_hit = np.asarray(w_eff)[: n + 1]
    lam = cfg.wavelength

    out = {"sku": row["sku"], "N": int(row["N"]),
           "chord_skip": int(row["chord_skip"]), "n_exit": int(row["n_exit"]),
           "k_spots": int(round(row["n_exit"] / row["N"])),
           "opl_m": float(row["opl_m"]),
           "envelope_mm": float(row["envelope_mm"]),
           "R_ring_mm": float(cfg.R_ring), "lambda_nm": lam_nm}

    # ---- 1. volume ------------------------------------------------------
    R_cav_cm = cfg.R_ring / 10.0
    h_full_cm = (MIRROR_DIA + 2 * SEAL_CLEAR) / 10.0
    z = hits[:, 2]
    h_beam_mm = (float(z.max() - z.min())
                 + 2 * (BEAM_CLEAR_W * float(w_hit.max()) + BEAM_CLEAR_MM))
    v_full_ml = float(np.pi * R_cav_cm ** 2 * h_full_cm)
    v_min_ml = float(np.pi * R_cav_cm ** 2 * h_beam_mm / 10.0)
    out.update(z_extent_mm=float(z.max() - z.min()),
               h_beam_mm=h_beam_mm,
               v_full_ml=v_full_ml, v_min_ml=v_min_ml,
               pvr_full_m_per_l=float(row["opl_m"] / (v_full_ml / 1000.0)),
               pvr_min_m_per_l=float(row["opl_m"] / (v_min_ml / 1000.0)))

    # ---- 2. spot overlap on mirrors --------------------------------------
    foot = mirror_footprints(hits, mseq, cfg)
    worst = {"eta_amp": 0.0, "d_mm": np.inf, "d_over_w": np.inf,
             "mirror": -1}
    n_pairs = 0
    n_pairs_hot = 0          # power overlap > 1e-4
    min_d = np.inf
    for m, arr in foot.items():
        if len(arr) < 2:
            continue
        uv = arr[:, :2]
        order = arr[:, 2].astype(int)
        ws = w_hit[np.clip(order, 0, len(w_hit) - 1)]
        for i in range(len(uv)):
            for j in range(i + 1, len(uv)):
                d = float(np.hypot(*(uv[i] - uv[j])))
                eta = overlap_amp(d, float(ws[i]), float(ws[j]))
                n_pairs += 1
                if eta * eta > 1e-4:
                    n_pairs_hot += 1
                if d < min_d:
                    min_d = d
                if eta > worst["eta_amp"]:
                    wbar = 0.5 * (float(ws[i]) + float(ws[j]))
                    worst = {"eta_amp": eta, "d_mm": d,
                             "d_over_w": d / wbar, "mirror": int(m)}
    out.update(n_spot_pairs=n_pairs, min_pair_d_mm=float(min_d),
               worst_pair_d_mm=worst["d_mm"],
               worst_pair_d_over_w=worst["d_over_w"],
               overlap_amp_max=worst["eta_amp"],
               overlap_power_max=worst["eta_amp"] ** 2,
               pairs_power_gt_1e4=n_pairs_hot)

    # spot fill: fraction of the used mirror band covered by (pi w^2) spots
    a_spots = float(np.pi * np.sum(w_hit[:n] ** 2))
    a_band = cfg.N * np.pi * (cfg.mirror_aperture ** 2)
    out["spot_fill_frac"] = a_spots / a_band

    # ---- 3. chord crossings ----------------------------------------------
    xy = hits[:, :2]
    segs = [(xy[i], xy[i + 1]) for i in range(n - 1)]
    dirs = [s[1] - s[0] for s in segs]
    dirs = [d / np.linalg.norm(d) for d in dirs]
    min_phi = np.pi
    n_cross = 0
    for i in range(len(segs)):
        for j in range(i + 2, len(segs)):
            if seg_intersect_2d(*segs[i], *segs[j]):
                n_cross += 1
                c = abs(float(dirs[i] @ dirs[j]))
                phi = float(np.arccos(np.clip(c, 0, 1)))
                if phi < min_phi:
                    min_phi = phi
    w_typ = float(np.median(w_hit))
    lam_fringe = lam / (2.0 * np.sin(min_phi / 2.0)) if n_cross else np.inf
    out.update(n_chord_crossings=n_cross,
               min_cross_angle_deg=float(np.degrees(min_phi)),
               fringe_period_um=float(lam_fringe * 1e3),
               washout_fringes_across_beam=float(2 * w_typ / lam_fringe))

    # ---- 4. hole vs side-slot entry --------------------------------------
    gap_mm = 2.0 * cfg.R_ring * np.sin(np.pi / cfg.N) - MIRROR_DIA
    chord_m = 2.0 * cfg.R_ring * np.sin(
        np.pi * cfg.chord_skip / cfg.N) / 1000.0
    out.update(side_gap_mm=float(gap_mm),
               side_slot_max_passes=int(cfg.N),
               side_slot_opl_m=float(cfg.N * chord_m),
               hole_gain_factor=float(row["opl_m"] / (cfg.N * chord_m)))
    return out


def main() -> int:
    menu = load_menu()
    rows = [metrics_one(r) for r in menu]
    df = pd.DataFrame(rows)
    out_csv = os.path.join(_HERE, "designs", "cell_metrics.csv")
    df.to_csv(out_csv, index=False)
    cols = ["sku", "N", "n_exit", "k_spots", "opl_m", "envelope_mm",
            "v_full_ml", "v_min_ml", "pvr_min_m_per_l",
            "worst_pair_d_mm", "worst_pair_d_over_w", "overlap_power_max",
            "pairs_power_gt_1e4", "n_chord_crossings",
            "min_cross_angle_deg", "washout_fringes_across_beam",
            "side_gap_mm", "side_slot_opl_m", "hole_gain_factor"]
    with pd.option_context("display.width", 300):
        print(df[cols].to_string(index=False))
    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
