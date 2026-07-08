"""ROC-compensation / thermal-window / M2 studies for the new designs.

Reuses investigations.py's study machinery on the feedback-round stars:
  --which trigas26m : 25.72 m tri-gas champion (1", hole 1.3 mm)
  --which mini9m    : 9.11 m half-inch mini cell (0.8 mm hole; env pins
                      the search constants before import)

Run from _CURRENT/ (once per design):
    ../.venv/Scripts/python.exe drone_20m/investigations_new.py --which trigas26m
    ../.venv/Scripts/python.exe drone_20m/investigations_new.py --which mini9m
"""
from __future__ import annotations

import argparse
import os
import sys

_ap = argparse.ArgumentParser()
_ap.add_argument("--which", choices=["trigas26m", "mini9m"], required=True)
A = _ap.parse_args()
if A.which == "mini9m":
    os.environ["TMPC_W0"] = "0.8"
    os.environ["TMPC_HOLE_R"] = "0.8"
    os.environ["TMPC_RADIAL_ALLOWANCE"] = "13.0"
    os.environ["TMPC_ENVELOPE_MAX"] = "130.0"

import pandas as pd                                               # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import investigations as inv                                      # noqa: E402

SETUPS = {
    "trigas26m": {"trigas_26m": "design_spec_D190_26m.json"},
    "mini9m": {"mini_9m": "design_spec_D130_9m_halfinch.json"},
}


def main() -> int:
    inv.DESIGNS = SETUPS[A.which]
    out_dir = os.path.join(_HERE, "designs")
    tag = A.which

    print(f"=== ROC compensation ({tag}) ===", flush=True)
    roc = inv.roc_study()
    roc.to_csv(os.path.join(out_dir, f"study_roc_{tag}.csv"), index=False)

    print(f"=== Thermal window ({tag}) ===", flush=True)
    th = inv.thermal_study()
    th.to_csv(os.path.join(out_dir, f"study_thermal_{tag}.csv"),
              index=False)

    print(f"=== M2 robustness ({tag}) ===", flush=True)
    m2 = inv.m2_study()
    m2.to_csv(os.path.join(out_dir, f"study_m2_{tag}.csv"), index=False)

    name = list(inv.DESIGNS)[0]
    lines = [f"## Engineering studies: {name}", ""]
    ok = roc[roc.feasible]
    if len(ok) >= 2:
        slope = ((ok.dR_ring_mm.max() - ok.dR_ring_mm.min())
                 / (ok.roc_err_pct.max() - ok.roc_err_pct.min()))
        lines.append(f"* ROC-error compensation: linear ring trim "
                     f"{slope:+.3f} mm per 1 % ROC error; feasible over "
                     f"{ok.roc_err_pct.min():+.1f}.."
                     f"{ok.roc_err_pct.max():+.1f} %.")
    for mat in ("aluminium", "invar"):
        lines.append(f"* Thermal window ({mat} ring, launch frozen): "
                     f"{inv.window(th, name, mat)}.")
    m2ok = m2[m2.feasible]
    lines.append(f"* Beam quality: all checks pass to M2 = "
                 f"{m2ok.M2.max():.2f}." if len(m2ok) else
                 "* Beam quality: M2 sweep failed nominal - inspect.")
    md = os.path.join(out_dir, "investigations_addendum.md")
    with open(md, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n\n")
    print("\n".join(lines))
    print(f"appended -> {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
