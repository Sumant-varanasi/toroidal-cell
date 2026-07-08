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
_ap.add_argument("--which", choices=["h2", "27m", "26m", "15m", "9m_mini",
                                     "19m_2in"],
                 required=True)
A = _ap.parse_args()
if A.which == "19m_2in":
    os.environ["TMPC_RADIAL_ALLOWANCE"] = "23.0"
if A.which == "h2":
    os.environ["TMPC_WAVELENGTH_MM"] = "2.1218e-3"
elif A.which == "9m_mini":
    os.environ["TMPC_W0"] = "0.8"
    os.environ["TMPC_HOLE_R"] = "0.8"
    os.environ["TMPC_RADIAL_ALLOWANCE"] = "13.0"
    os.environ["TMPC_ENVELOPE_MAX"] = "130.0"

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
    "26m": ("designs/robust_menu_hardened_flight.csv", "CM254-200-M01", 16,
            176, "spec_D190_26m", 74.5),
    "15m": ("designs/robust_menu_hardened_flight.csv", "CM254-100-M01", 16,
            112, "spec_D180_15m_sparse", 69.6),
    "9m_mini": ("designs/robust_menu_minihole_flight.csv", "CM127-050-M01",
                14, 98, "spec_D130_9m_halfinch", 51.6),
    "19m_2in": ("designs/robust_menu_twoinch_flight.csv", "CM508-150-M01",
                8, 152, "spec_D190_19m_2inch", 67.8),
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
