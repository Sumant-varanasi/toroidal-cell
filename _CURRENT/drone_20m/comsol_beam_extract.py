"""Score COMSOL ray-bundle beam widths against the Gaussian/ABCD envelope.

Companion to comsol_beam_gen.py.  The bundle's transverse second moments
about the chief ray reproduce the beam 1/e^2 radius exactly in the
paraxial limit (moments propagate by the same ABCD matrices as the
complex q), so at every exported time step we:
  1. project the 16 bundle-ray offsets onto the plane normal to the
     chief direction,
  2. take w = sqrt(4 * eigenvalues) of the 2x2 moment matrix
     (principal 1/e^2 radii; calibrated so t=0 gives w(release)),
  3. compare against the platform's astigmatic ABCD w_t/w_s evaluated at
     the same path length (sorted-pair comparison, since principal axes
     need not align with the tangential/sagittal planes).
Steps within +/-2 samples of a chief-ray bounce are masked (rays cross
the mirror at slightly different times there).

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/comsol_beam_extract.py --design freespace
    ../.venv/Scripts/python.exe drone_20m/comsol_beam_extract.py --design D150_14cm_flight
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc                 # noqa
from tmpc_platform_v5.beam import (astigmatic_focal_lengths,           # noqa
                                   _w_of_q, _apply, _free, _lens)
from comsol_gen import SPECS                                           # noqa
from comsol_beam_gen import FS, bundle                                 # noqa


def load_rays(path: str) -> np.ndarray:
    """(n_rays, n_times, 3) positions; NaN where a ray is not alive."""
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("%") or not line.strip():
                continue
            rows.append([float(v) for v in line.split()])
    n_cols = max(len(r) for r in rows)
    rays = []
    for r in rows:
        vals = np.full(n_cols, np.nan)
        vals[: len(r)] = r
        if (n_cols - 1) % 3 == 0:
            vals = vals[1:]                       # drop Index column
        rays.append(vals.reshape(-1, 3))
    return np.asarray(rays)


def match_bundle(P: np.ndarray, expected) -> np.ndarray:
    """Rows of P matching the released bundle (COMSOL exports allocate
    extra never-released grid rays that stay NaN — drop them).

    Rays are fingerprinted by release position AND initial direction,
    because sin-phase rays share the chief's release point.
    """
    p0 = P[:, 0, :]
    d0 = P[:, 1, :] - p0
    nrm = np.linalg.norm(d0, axis=1)
    ok = np.isfinite(p0).all(axis=1) & np.isfinite(d0).all(axis=1) \
        & (nrm > 1e-12)
    d0 = np.where(ok[:, None], d0 / np.where(nrm[:, None] > 0, nrm[:, None],
                                             1.0), np.nan)
    picked = []
    for pe, de in expected:
        score = (np.linalg.norm(p0 - pe, axis=1)
                 + 10.0 * np.linalg.norm(d0 - de, axis=1))
        score[~ok] = np.inf
        for i in picked:
            score[i] = np.inf
        j = int(np.argmin(score))
        if not np.isfinite(score[j]) or score[j] > 1e-3:
            raise SystemExit(f"bundle ray not found in export "
                             f"(best score {score[j]:.2e})")
        picked.append(j)
    return P[picked]


def moment_widths(P: np.ndarray, chief: int):
    """Per-time principal 1/e^2 radii (w_A >= w_B) from bundle moments."""
    n_rays, n_t, _ = P.shape
    others = [i for i in range(n_rays) if i != chief]
    wA = np.full(n_t, np.nan)
    wB = np.full(n_t, np.nan)
    for k in range(n_t):
        if not np.isfinite(P[:, k, :]).all():
            continue
        if k + 1 < n_t and np.isfinite(P[chief, k + 1]).all():
            d = P[chief, k + 1] - P[chief, k]
        else:
            d = P[chief, k] - P[chief, k - 1]
        nd = np.linalg.norm(d)
        if nd < 1e-12:
            continue
        d = d / nd
        b1 = np.cross(d, np.array([0.0, 0.0, 1.0]))
        if np.linalg.norm(b1) < 1e-6:
            b1 = np.cross(d, np.array([1.0, 0.0, 0.0]))
        b1 /= np.linalg.norm(b1)
        b2 = np.cross(d, b1)
        U = P[others, k, :] - P[chief, k, :]
        c1 = U @ b1
        c2 = U @ b2
        C = np.array([[np.mean(c1 * c1), np.mean(c1 * c2)],
                      [np.mean(c1 * c2), np.mean(c2 * c2)]])
        ev = np.linalg.eigvalsh(C)
        wA[k] = np.sqrt(4.0 * ev[1])
        wB[k] = np.sqrt(4.0 * ev[0])
    return wA, wB


def chief_kinks(Pc: np.ndarray, ang_tol: float = 5e-5) -> np.ndarray:
    d = np.diff(Pc, axis=0)
    L = np.linalg.norm(d, axis=1)
    ok = L > 1e-9
    u = np.full_like(d, np.nan)
    u[ok] = d[ok] / L[ok, None]
    dots = np.clip((u[:-1] * u[1:]).sum(axis=1), -1.0, 1.0)
    return np.nonzero(np.arccos(dots) > ang_tol)[0] + 1


def ref_widths_along_path(s: np.ndarray, pts: np.ndarray,
                          w0: float, M2: float, lam: float, z_rel: float,
                          R_t: float, R_s: float):
    """ABCD w_t, w_s at path lengths s (measured from pts[0] = release).

    pts = [release, bounce1, bounce2, ...]; astigmatic lens applied at
    each bounce with AOI derived from the chord directions.
    """
    zR = np.pi * w0 ** 2 / (M2 * lam)
    seg_len = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    seg_start_s = np.concatenate([[0.0], np.cumsum(seg_len)])
    q_t = complex(z_rel, zR)
    q_s = complex(z_rel, zR)
    q_at_seg = [(q_t, q_s)]
    dirs = np.diff(pts, axis=0)
    dirs = dirs / np.linalg.norm(dirs, axis=1)[:, None]
    for i in range(len(seg_len) - 1):
        q_t = _apply(q_t, _free(seg_len[i]))
        q_s = _apply(q_s, _free(seg_len[i]))
        cosd = float(np.clip(dirs[i] @ dirs[i + 1], -1.0, 1.0))
        aoi = 0.5 * (np.pi - np.arccos(cosd))
        f_t, f_s = astigmatic_focal_lengths(R_t, R_s, aoi)
        q_t = _apply(q_t, _lens(f_t))
        q_s = _apply(q_s, _lens(f_s))
        q_at_seg.append((q_t, q_s))
    wt = np.full(len(s), np.nan)
    ws = np.full(len(s), np.nan)
    for j, sj in enumerate(s):
        i = int(np.searchsorted(seg_start_s[1:], sj, side="right"))
        if i >= len(q_at_seg):
            continue
        ds = sj - seg_start_s[i]
        qt = q_at_seg[i][0] + ds
        qs = q_at_seg[i][1] + ds
        wt[j] = _w_of_q(qt, lam, M2)
        ws[j] = _w_of_q(qs, lam, M2)
    return wt, ws


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True,
                    choices=["freespace"] + sorted(SPECS))
    ap.add_argument("--export", default=None)
    ap.add_argument("--fig", default=None)
    args = ap.parse_args()

    name = ("freespace_beam_ray.txt" if args.design == "freespace"
            else f"{args.design}_beam_ray.txt")
    exp = args.export or os.path.join(_HERE, "designs", "comsol", "java",
                                      name)
    P = load_rays(exp)
    n_rays, n_t, _ = P.shape

    if args.design == "freespace":
        w0, M2, lam = FS["w0"], FS["M2"], FS["lam"]
        rel = np.array([0.0, 0.0, 0.5])
        u = np.array([0.0, 0.0, 1.0])
        z_rel = 0.0
        pts = np.vstack([rel, rel + np.array([0.0, 0.0, 1e4])])
        R_t = R_s = 1e12
    else:
        with open(os.path.join(_HERE, "designs", SPECS[args.design]),
                  "r", encoding="utf-8") as fh:
            spec = json.load(fh)
        cfg = TMPCConfig(**spec["cfg"])
        cfg.n_passes = int(spec["metrics"]["n_exit"]) + 1
        res = simulate_tmpc(cfg)
        pattern = np.asarray(res.spot_pattern[: res.bounces])
        s0, s1 = pattern[0], pattern[1]
        u = (s1 - s0) / np.linalg.norm(s1 - s0)
        rel = s0 + 3.0 * u
        pts = np.vstack([rel, pattern[1:]])
        w0 = float(cfg.w0)
        M2 = float(getattr(cfg, "M2", 1.0))
        lam = float(cfg.wavelength)
        z_rel = 3.0 - float(getattr(cfg, "input_waist_offset", 0.0))
        R_t, R_s = float(cfg.R_t), float(cfg.R_s)

    theta_d = M2 * lam / (np.pi * w0)
    expected = bundle(rel, u, w0, theta_d, z_rel, 8)
    P = match_bundle(P, expected)
    n_rays = P.shape[0]
    chief = 0                       # bundle() lists the chief first
    wA, wB = moment_widths(P, chief)

    # path length of the chief ray at each step
    steps = np.linalg.norm(np.diff(P[chief], axis=0), axis=1)
    steps = np.nan_to_num(steps)
    s = np.concatenate([[0.0], np.cumsum(steps)])

    # mask steps near bounces and steps where any ray is dead
    good = np.isfinite(wA)
    for kk in chief_kinks(P[chief]):
        good[max(0, kk - 2): kk + 3] = False

    wt, ws = ref_widths_along_path(s, pts, w0, M2, lam, z_rel, R_t, R_s)
    ref_hi = np.maximum(wt, ws)
    ref_lo = np.minimum(wt, ws)
    good &= np.isfinite(ref_hi)

    rel_hi = (wA[good] - ref_hi[good]) / ref_hi[good] * 100.0
    rel_lo = (wB[good] - ref_lo[good]) / ref_lo[good] * 100.0
    print(f"{args.design}: {n_rays} rays, {n_t} steps, chief={chief}, "
          f"{int(good.sum())} scored steps, path {s[good].max() / 1e3:.3f} m")
    print(f"  w range COMSOL: {np.nanmin(wB[good]):.4f} - "
          f"{np.nanmax(wA[good]):.4f} mm")
    print(f"  major-axis dev vs ABCD: mean {np.mean(np.abs(rel_hi)):.3f}% "
          f" max {np.max(np.abs(rel_hi)):.3f}%")
    print(f"  minor-axis dev vs ABCD: mean {np.mean(np.abs(rel_lo)):.3f}% "
          f" max {np.max(np.abs(rel_lo)):.3f}%")

    fig_path = args.fig or os.path.join(
        _HERE, "designs", "figures", f"comsol_beam_{args.design}.png")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9.5, 4.2))
        sm = s / 1e3
        ax.plot(sm[good], wA[good], ".", ms=2.5, color="#1f77b4",
                label="COMSOL ray bundle (major)")
        ax.plot(sm[good], wB[good], ".", ms=2.5, color="#2ca02c",
                label="COMSOL ray bundle (minor)")
        ax.plot(sm, ref_hi, "-", lw=1.0, color="#c0392b",
                label="ABCD astigmatic envelope (max)")
        ax.plot(sm, ref_lo, "--", lw=1.0, color="#c0392b",
                label="ABCD astigmatic envelope (min)")
        ax.set_xlabel("path length along beam [m]")
        ax.set_ylabel("1/e$^2$ beam radius [mm]")
        ttl = ("Free space: COMSOL ray bundle vs Gaussian law"
               if args.design == "freespace"
               else f"{args.design}: COMSOL ray bundle vs astigmatic ABCD")
        ax.set_title(ttl + f"  (max dev {np.max(np.abs(rel_hi)):.2f}%)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        os.makedirs(os.path.dirname(fig_path), exist_ok=True)
        fig.savefig(fig_path, dpi=170)
        print(f"wrote {fig_path}")
    except Exception as exc:                                   # noqa: BLE001
        print("plot skipped:", exc)

    out = os.path.join(_HERE, "designs", "comsol", "comsol_beam.csv")
    row = dict(design=args.design, n_rays=n_rays, n_steps=int(good.sum()),
               path_m=float(s[good].max() / 1e3),
               w_min_mm=float(np.nanmin(wB[good])),
               w_max_mm=float(np.nanmax(wA[good])),
               dev_major_mean_pct=float(np.mean(np.abs(rel_hi))),
               dev_major_max_pct=float(np.max(np.abs(rel_hi))),
               dev_minor_mean_pct=float(np.mean(np.abs(rel_lo))),
               dev_minor_max_pct=float(np.max(np.abs(rel_lo))))
    df = pd.DataFrame([row])
    if os.path.exists(out):
        old = pd.read_csv(out)
        old = old[old["design"] != args.design]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(out, index=False)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
