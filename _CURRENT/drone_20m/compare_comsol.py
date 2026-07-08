"""Compare a COMSOL ray export against the platform's exact trace.

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/compare_comsol.py \
        --design D190_26m_trigas --csv path/to/comsol_export.csv

The COMSOL export should contain one row per mirror interaction of the
chief ray, ordered by interaction time, with columns for the hit-point
coordinates in the model frame (any of qx/qy/qz, x/y/z, px/py/pz —
case-insensitive; extra columns are ignored). The model frame must be
the geometry frame shipped in designs/comsol/comsol_geom_<design>.csv
(ring centre at the origin, ring plane z = 0).

Reports per-bounce deviation statistics and the same PASS metric used
for the Optiland cross-validation: RMS deviation and worst deviation in
micrometres over the full bounce sequence.
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
COL_SETS = (("qx", "qy", "qz"), ("x", "y", "z"), ("px", "py", "pz"))


def load_comsol(path: str) -> np.ndarray:
    df = pd.read_csv(path, comment="%")
    df.columns = [str(c).strip().lower() for c in df.columns]
    for cols in COL_SETS:
        if all(c in df.columns for c in cols):
            return df[list(cols)].to_numpy(dtype=float)
    raise SystemExit(f"no coordinate columns {COL_SETS} in {path}; "
                     f"found {list(df.columns)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, choices=sorted(SPECS))
    ap.add_argument("--csv", required=True)
    ap.add_argument("--unit-scale", type=float, default=1.0,
                    help="multiply COMSOL coordinates by this to get mm "
                         "(1000 if the export is in metres)")
    args = ap.parse_args()

    with open(os.path.join(_HERE, "designs", SPECS[args.design]),
              "r", encoding="utf-8") as f:
        spec = json.load(f)
    cfg = TMPCConfig(**spec["cfg"])
    n_exit = int(spec["metrics"]["n_exit"])
    cfg.n_passes = n_exit + 1
    res = simulate_tmpc(cfg)
    ours = np.asarray(res.spot_pattern[: res.bounces])

    theirs = load_comsol(args.csv) * args.unit_scale
    n = min(len(ours), len(theirs))
    if len(theirs) != len(ours):
        print(f"note: bounce counts differ (ours {len(ours)}, comsol "
              f"{len(theirs)}); comparing first {n}")
    d_um = np.linalg.norm(ours[:n] - theirs[:n], axis=1) * 1e3
    print(f"{args.design}: {n} interactions compared")
    print(f"  RMS deviation   {np.sqrt((d_um ** 2).mean()):10.3f} um")
    print(f"  worst deviation {d_um.max():10.3f} um  "
          f"(bounce {int(d_um.argmax())})")
    print(f"  median          {np.median(d_um):10.3f} um")
    ok = d_um.max() < 10.0
    print(f"  verdict: {'PASS' if ok else 'CHECK'} (worst < 10 um "
          f"criterion, same as the Optiland cross-validation)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
