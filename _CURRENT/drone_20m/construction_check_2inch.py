"""Manufacturing-process MC for the two-inch flight-robust designs.

Same process grades as mech_materials.py, applied to the 19.0 m and
11.6 m CM508 designs found by the printable-target search.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/construction_check_2inch.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from mech_materials import PROCESS_GRADES, mc_task                # noqa: E402


def main() -> int:
    d = pd.read_csv(os.path.join(_HERE, "designs",
                                 "robust_menu_twoinch_flight.csv"))
    picks = [("CM508-150-M01", 8, 152, 'two-inch 19.0 m (8 mirrors)'),
             ("CM508-500-M01", 7, 105, 'two-inch 11.6 m (7 mirrors)')]
    rows = []
    for sku, n_mir, n_exit, name in picks:
        m = d[(d["sku"] == sku) & (d["N"] == n_mir)
              & (d["n_exit"] == n_exit)]
        if not len(m):
            print(f"skip {name}: not in menu")
            continue
        row = m.iloc[0].to_dict()
        for proc, p in PROCESS_GRADES.items():
            r = mc_task({"row": row, "name": name, "proc": proc, "p": p})
            rows.append(r)
            print(f"  {name:28s} {proc:26s} "
                  f"complete={r.get('complete_frac', 0)*100:5.0f}%  "
                  f"sep_ok={r.get('sep_ok')} hole_ok={r.get('hole_ok')} "
                  f"exit_ok={r.get('exit_ok')} "
                  f"survives={r.get('survives')}", flush=True)
    out = os.path.join(_HERE, "designs", "construction_tolerance_2inch.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
