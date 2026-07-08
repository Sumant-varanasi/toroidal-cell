"""As-built spec sheets for the feedback-round designs.

Run from _CURRENT/ once per wavelength (env pins the search module):
    ../.venv/Scripts/python.exe drone_20m/new_specs.py --which h2
    ../.venv/Scripts/python.exe drone_20m/new_specs.py --which 27m
"""
from __future__ import annotations

import argparse
import os
import sys

_ap = argparse.ArgumentParser()
_ap.add_argument("--which", choices=["h2", "27m"], required=True)
A = _ap.parse_args()
if A.which == "h2":
    os.environ["TMPC_WAVELENGTH_MM"] = "2.1218e-3"

import pandas as pd                                               # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from spec_asbuilt import write_spec                               # noqa: E402

PICKS = {
    "h2": ("designs/robust_menu_h2_flight.csv", "CM254-200-M01", 16, 176,
           "spec_D180_24m_H2", 69.0),
    "27m": ("designs/robust_menu_v9deep_flight.csv", "CM254-075-M01", 12,
            228, "spec_D160_27m", 60.7),
}


def main() -> int:
    csv, sku, n_mir, n_exit, tag, rr = PICKS[A.which]
    d = pd.read_csv(os.path.join(_HERE, csv))
    m = d[(d["sku"] == sku) & (d["N"] == n_mir) & (d["n_exit"] == n_exit)
          & ((d["R_ring"] - rr).abs() < 0.5)]
    row = m.iloc[0].to_dict()
    md = os.path.join(_HERE, "designs", f"{tag}.md")
    js = os.path.join(_HERE, "designs", f"design_{tag}.json")
    r = write_spec(row, md, js)
    print(f"{tag}: {r['opl_m']:.2f} m @ {r['throughput']*100:.1f}% "
          f"in {r['envelope_mm']:.0f} mm -> {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
