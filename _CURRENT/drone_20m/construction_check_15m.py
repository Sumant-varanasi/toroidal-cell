"""Construction-tolerance MC for the hardened sparse design (15.3 m).

The walk-hardened search produced CM254-100-M01 x16, n=112 (7 spots per
mirror, 15.30 m, Ø175, 89.5 %): the sparsest long-path pattern found.
This runs the same manufacturing-process Monte-Carlo as
mech_materials.py on it, to test whether sparse patterns extend the
cheap-build envelope beyond drone_20m.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/construction_check_15m.py
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
                                 "robust_menu_hardened_flight.csv"))
    m = d[(d["sku"] == "CM254-100-M01") & (d["N"] == 16)
          & (d["n_exit"] == 112)]
    row = m.iloc[0].to_dict()
    rows = []
    for proc, p in PROCESS_GRADES.items():
        r = mc_task({"row": row, "name": "hardened_15m (15.3 m)",
                     "proc": proc, "p": p})
        rows.append(r)
        print(f"  {proc:26s} complete={r.get('complete_frac', 0)*100:5.0f}%"
              f"  sep_ok={r.get('sep_ok')} hole_ok={r.get('hole_ok')} "
              f"exit_ok={r.get('exit_ok')} survives={r.get('survives')}",
              flush=True)
    out = os.path.join(_HERE, "designs", "construction_tolerance_15m.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
