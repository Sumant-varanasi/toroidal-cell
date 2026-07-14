"""Extract bounce vertices from a COMSOL ray export and score vs our tracer.

The COMSOL Data export samples the chief ray on a uniform time grid.
Between wall hits the trajectory is exactly straight, so each bounce
vertex is recovered *exactly* as the intersection of the two fitted
chord lines on either side of the direction kink — sampling density only
needs to give >=2 samples per chord.

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/comsol_extract.py \
        --design D190_19m_2inch
Writes/updates designs/comsol/comsol_agreement.csv.
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

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc               # noqa: E402

SPECS = {
    "D190_26m_trigas": "design_spec_D190_26m.json",
    "D160_27m": "design_spec_D160_27m.json",
    "D180_24m_H2": "design_spec_D180_24m_H2.json",
    "D180_15m_sparse": "design_spec_D180_15m_sparse.json",
    "D130_9m_halfinch": "design_spec_D130_9m_halfinch.json",
    "D190_19m_2inch": "design_spec_D190_19m_2inch.json",
    "D190_29m_max": "design_D190_29m.json",
    "D150_14cm_flight": "design_D150_14cm.json",
    "D180_22m": "design_D180_22m.json",
}


def load_ray_export(path: str) -> np.ndarray:
    """Return (n_times, 3) positions of the single chief ray [mm]."""
    header = None
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("%"):
                header = line[1:].strip()
                continue
            vals = line.split()
            if vals:
                rows.append([float(v) for v in vals])
    if not rows:
        raise SystemExit(f"no data rows in {path}")
    arr = np.asarray(rows)
    if header and "@" in header:
        # one row per ray: leading Index column, then interleaved
        # (qx, qy, qz) @ t0, (qx, qy, qz) @ t1, ...  Pick the longest
        # finite (non-frozen) ray — the chief ray survives all bounces.
        best = None
        for r in range(arr.shape[0]):
            vals = arr[r]
            if (len(vals) - 1) % 3 == 0:
                vals = vals[1:]
            elif len(vals) % 3 != 0:
                continue
            P = vals.reshape(-1, 3)
            finite = np.isfinite(P).all(axis=1)
            n_ok = int(finite.sum())
            if best is None or n_ok > best[0]:
                best = (n_ok, P[finite])
        if best is None:
            raise SystemExit(f"no parsable ray rows in {path}")
        return best[1]
    if arr.shape[1] >= 3:
        return arr[:, -3:]
    raise SystemExit(f"unrecognised export layout {arr.shape} in {path}")


def _line_intersect(pa, da, pb, db):
    """Midpoint of the closest approach of two lines."""
    w0 = pa - pb
    bb = float(da @ db)
    dd, ee = float(da @ w0), float(db @ w0)
    den = 1.0 - bb * bb
    if abs(den) < 1e-12:
        return None
    s = (bb * ee - dd) / den
    t = (ee - bb * dd) / den
    return 0.5 * ((pa + s * da) + (pb + t * db))


def bounce_vertices(P: np.ndarray, ang_tol: float = 5e-5,
                    min_run: int = 3) -> np.ndarray:
    """Intersect consecutive long chord-runs -> one vertex per bounce.

    Fixed-time sampling drops a single short 'crossing' step at each
    reflection, so a bounce reads as two kinks bracketing a 1-step run.
    Keeping only runs of >= min_run steps and intersecting consecutive
    kept-run lines recovers exactly one vertex per physical bounce.
    """
    d = np.diff(P, axis=0)
    L = np.linalg.norm(d, axis=1)
    keep = L > 1e-9
    idx = np.nonzero(keep)[0]              # step k spans P[idx[k]] -> +1
    u = d[keep] / L[keep][:, None]
    dots = np.clip((u[:-1] * u[1:]).sum(axis=1), -1.0, 1.0)
    kink = np.arccos(dots) > ang_tol
    runs = []
    start = 0
    for i in range(len(kink)):
        if kink[i]:
            runs.append((start, i))
            start = i + 1
    runs.append((start, len(u) - 1))
    # keep only substantial straight runs (drop 1-2 step crossing stubs)
    long_runs = [(a, b) for (a, b) in runs if (b - a + 1) >= min_run]
    lines = []
    for a, b in long_runs:
        pa = P[idx[a]]
        pb = P[idx[b] + 1]
        da = pb - pa
        da = da / np.linalg.norm(da)
        lines.append((pa, da))
    verts = []
    for (pa, da), (pb, db) in zip(lines[:-1], lines[1:]):
        v = _line_intersect(pa, da, pb, db)
        if v is not None:
            verts.append(v)
    return np.asarray(verts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, choices=sorted(SPECS))
    ap.add_argument("--export", default=None)
    args = ap.parse_args()

    exp = args.export or os.path.join(_HERE, "designs", "comsol", "java",
                                      f"{args.design}_ray.txt")
    P = load_ray_export(exp)
    verts = bounce_vertices(P)

    with open(os.path.join(_HERE, "designs", SPECS[args.design]),
              "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    cfg = TMPCConfig(**spec["cfg"])
    n_exit = int(spec["metrics"]["n_exit"])
    cfg.n_passes = n_exit + 1
    res = simulate_tmpc(cfg)
    ours = np.asarray(res.spot_pattern[: res.bounces])

    best = None
    for off in (1, 0, 2):                 # ours[off:] vs comsol verts
        n = min(len(ours) - off, len(verts))
        if n < 10:
            continue
        dev = np.linalg.norm(ours[off:off + n] - verts[:n], axis=1)
        rms = float(np.sqrt((dev ** 2).mean()))
        if best is None or rms < best[1]:
            best = (off, rms, dev, n)
    off, rms, dev, n = best
    um = dev * 1e3
    print(f"{args.design}: comsol vertices={len(verts)} traced bounces="
          f"{len(ours)} aligned n={n} (offset {off})")
    print(f"  RMS  {um.mean() and np.sqrt((um**2).mean()):9.3f} um")
    print(f"  worst{um.max():9.3f} um (bounce {int(um.argmax())})")
    print(f"  median{np.median(um):8.3f} um")

    # exit check: vertex at design exit bounce near hole centre
    exit_ok = ""
    j = n_exit - off
    if 0 <= j < len(verts):
        m0 = verts[j]
        hole = np.array([ours[0][0], ours[0][1], ours[0][2]])
        miss = float(np.linalg.norm(m0 - hole))
        exit_ok = f"exit-vertex miss from entrance point: {miss:.4f} mm " \
                  f"(hole r = {cfg.hole_radius} mm)"
        print("  " + exit_ok)

    out = os.path.join(_HERE, "designs", "comsol", "comsol_agreement.csv")
    row = dict(design=args.design, n_vertices=len(verts), n_compared=n,
               align_offset=off, rms_um=float(np.sqrt((um ** 2).mean())),
               worst_um=float(um.max()), median_um=float(np.median(um)),
               exit_note=exit_ok)
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
