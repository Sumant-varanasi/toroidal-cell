"""Polarization audit: Jones-matrix accumulation over the full path.

Over 80-322 gold reflections at 7-26 deg AOI the s/p amplitude and phase
differences accumulate, and the small sagittal launch tips the incidence
plane bounce-to-bounce, so the polarization state at the detector is a
real design property (WMS chains, polarization-sensitive fiber optics).

Method: exact traced hits -> per-bounce incidence geometry (normal from
the specular bisector, s/p basis from the incidence plane), complex
Fresnel coefficients for gold, parallel-transport basis rotation between
bounces, cumulative 2x2 Jones matrix. Reported per design:

  * per-bounce and cumulative s/p power split (diattenuation),
  * net retardance (s-p phase) at the exit,
  * for a 45 deg linear input: output ellipticity and azimuth rotation.

Gold optical constants (Babar & Weaver 2015, interpolated; protective
dielectric overcoat perturbs these at the <1e-3 level and is neglected —
absolute R stays the parametric 0.999 used everywhere else; this audit
is about RATIOS and PHASES).

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/polarization_audit.py
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

AU_N = {1512.2: 0.53 + 9.5j, 1654.0: 0.62 + 10.4j, 2121.8: 0.92 + 13.1j}

MENUS = (("robust_menu.csv", 1654.0),
         ("robust_menu_flight.csv", 1654.0),
         ("robust_menu_h2_flight.csv", 2121.8),
         ("robust_menu_hardened_flight.csv", 1654.0),
         ("robust_menu_minihole_flight.csv", 1654.0))


def unit(v):
    return v / np.linalg.norm(v)


def fresnel(nc: complex, cos_t: float):
    """Complex rs, rp for incidence from vacuum on metal index nc."""
    sin2 = 1.0 - cos_t ** 2
    root = np.sqrt(nc * nc - sin2 + 0j)
    rs = (cos_t - root) / (cos_t + root)
    rp = (nc * nc * cos_t - root) / (nc * nc * cos_t + root)
    return rs, rp


def audit_one(row, lam_nm):
    cfg = cfg_from_row(row)
    cfg.n_passes = int(row["n_exit"])
    cfg.wavelength = lam_nm * 1e-6
    res = simulate_tmpc(cfg)
    n = res.bounces
    hits = res.spot_pattern[:n]
    # entry point: hole on mirror 0 -- reconstruct from the first chord
    # backwards along the launch direction (adequate: only sets the
    # first-bounce incidence plane)
    d0 = unit(hits[1] - hits[0])
    p_entry = hits[0] - 50.0 * d0
    pts = np.vstack([p_entry, hits])
    nc = AU_N[lam_nm]

    M = np.eye(2, dtype=complex)
    s_prev = None
    aois = []
    rs_pow, rp_pow = 1.0, 1.0
    for j in range(1, len(pts) - 1):
        d_in = unit(pts[j] - pts[j - 1])
        d_out = unit(pts[j + 1] - pts[j])
        dv = d_out - d_in
        if np.linalg.norm(dv) < 1e-9:     # degenerate/duplicated segment
            continue
        nrm = unit(dv)                    # surface normal, against d_in
        cos_t = float(np.clip(-np.dot(d_in, nrm), 1e-6, 1.0))
        aois.append(np.degrees(np.arccos(cos_t)))
        s_hat = np.cross(d_in, nrm)
        if np.linalg.norm(s_hat) < 1e-12:  # normal incidence guard
            s_hat = np.array([0.0, 0.0, 1.0])
        s_hat = unit(s_hat)
        p_in = np.cross(s_hat, d_in)
        if s_prev is not None:
            # rotate previous basis into this bounce's (s, p_in) frame
            cospsi = float(np.dot(s_prev, s_hat))
            sinpsi = float(np.dot(s_prev, p_in))
            R = np.array([[cospsi, sinpsi], [-sinpsi, cospsi]],
                         dtype=complex)
            M = R @ M
        rs, rp = fresnel(nc, cos_t)
        M = np.diag([rs, rp]) @ M
        rs_pow *= abs(rs) ** 2
        rp_pow *= abs(rp) ** 2
        # transport: s stays s across the reflection; p flips with d_out
        s_prev = s_hat

    # cumulative properties
    JtJ = M.conj().T @ M
    evals = np.linalg.eigvalsh(JtJ).real
    t_min, t_max = float(evals[0]), float(evals[-1])
    # s/v input (vertical = sagittal) and 45 deg input
    e_s = M @ np.array([1.0, 0.0])
    e_p = M @ np.array([0.0, 1.0])
    e45 = M @ (np.array([1.0, 1.0]) / np.sqrt(2))
    # output ellipse for 45 deg input
    ex, ey = e45
    T45 = float(abs(ex) ** 2 + abs(ey) ** 2)
    # Stokes
    s0 = abs(ex) ** 2 + abs(ey) ** 2
    s1 = abs(ex) ** 2 - abs(ey) ** 2
    s2 = 2 * (ex * np.conj(ey)).real
    s3 = -2 * (ex * np.conj(ey)).imag
    azimuth = 0.5 * np.degrees(np.arctan2(s2, s1))
    ellipt = 0.5 * np.degrees(np.arcsin(np.clip(s3 / s0, -1, 1)))
    retard = float(np.angle(e_p[1]) - np.angle(e_s[0]))
    s_purity = float(abs(e_s[0]) ** 2
                     / (abs(e_s[0]) ** 2 + abs(e_s[1]) ** 2))
    return dict(
        design=f"{row['sku']} x{int(row['N'])} n={int(row['n_exit'])}",
        opl_m=float(row["opl_m"]), lam_nm=lam_nm, n_refl=n,
        aoi_mean_deg=float(np.mean(aois)),
        Ts_over_Tp_perbounce=float((rs_pow / rp_pow) ** (1.0 / n)),
        T_s=float(abs(e_s[0]) ** 2 + abs(e_s[1]) ** 2),
        T_p=float(abs(e_p[0]) ** 2 + abs(e_p[1]) ** 2),
        diattenuation=float((t_max - t_min) / (t_max + t_min)),
        T45=T45, out_azimuth_deg=float(azimuth) - 45.0,
        out_ellipticity_deg=float(ellipt),
        retardance_deg=float(np.degrees(retard) % 360.0),
        s_launch_purity=s_purity,
    )


def main() -> int:
    rows, seen = [], set()
    for f, lam in MENUS:
        p = os.path.join(_HERE, "designs", f)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        d = d[d["robust"]]
        for _, r in d.iterrows():
            key = (r["sku"], int(r["N"]), int(r["n_exit"]),
                   int(round(r["R_ring"], 0)))
            if key in seen:
                continue
            seen.add(key)
            rows.append(audit_one(r.to_dict(), lam))
            x = rows[-1]
            print(f"{x['design']:32s} {x['opl_m']:5.1f} m n={x['n_refl']:3d}"
                  f" aoi={x['aoi_mean_deg']:5.1f}  Ts={x['T_s']:.3f} "
                  f"Tp={x['T_p']:.3f}  ell45={x['out_ellipticity_deg']:+.2f}"
                  f" deg rot45={x['out_azimuth_deg']:+.2f} deg", flush=True)
    df = pd.DataFrame(rows)
    out = os.path.join(_HERE, "designs", "polarization_audit.csv")
    df.to_csv(out, index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
