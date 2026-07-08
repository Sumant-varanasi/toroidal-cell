"""Mass + lid-mode table for full-metal vs hybrid builds (prof directive).

Benoy 2026-07-08: choose one material combination for the drone (no
titanium/Invar — expensive; aluminium reasonable) and find a generic
low-cost design capable of 3D printing with plastic/PEEK. His framework's
answer — confirmed here with actual CAD volumes — is:

  drone baseline : all-aluminium body (mirror seats machined in the body)
  low-cost route : printed plastic shell + machined aluminium mirror
                   cartridge (the plastic never defines an optical datum)

This script builds both architectures for each design with housing_cad,
takes real solid volumes, and tabulates structure/total mass and the lid
fundamental mode per shell material. Plastic lids are evaluated at 6 mm
(vs 4 mm metal) — the standard thickness compensation for E ~ 2-4 GPa.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/hybrid_materials.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from housing_cad import DESIGNS, build, build_hybrid, load_row    # noqa: E402
from mech_materials import MATERIALS, lid_first_mode_hz           # noqa: E402

MATERIALS = dict(MATERIALS)
MATERIALS.setdefault("PEEK (CNC/printed)", dict(E=3.6, rho=1.31, cte=47.0))

MIRROR_G = {"one_inch": 20.0, "half_inch": 6.0, "two_inch": 57.0}
OPTICS_G = 80.0
RHO_AL = 2.70
SHELL_MATS = ["PA12 (MJF/SLS)", "PA12-CF (MJF)", "PLA (FDM)",
              "Tough resin (SLA)", "PEEK (CNC/printed)"]
BUILD_DESIGNS = ["14cm", "29m", "9m_mini", "19m_2in"]


def vol_cm3(part) -> float:
    return float(part.val().Volume()) / 1000.0


def main() -> int:
    rows = []
    for key in BUILD_DESIGNS:
        row = load_row(key)
        fam = str(row.get("family", "one_inch"))
        n_mir = int(row["N"])
        env = float(row["envelope_mm"])
        mirrors_g = n_mir * MIRROR_G[fam] + OPTICS_G

        body, lid, base = build(row)
        v_metal = vol_cm3(body) + vol_cm3(lid) + vol_cm3(base)
        m_al = v_metal * RHO_AL
        rows.append(dict(design=key, architecture="all-aluminium",
                         shell_material="Al 6061 (CNC)",
                         structure_g=round(m_al),
                         total_g=round(m_al + mirrors_g),
                         lid_f1_hz=round(lid_first_mode_hz(
                             env, MATERIALS["Al 6061 (CNC)"], 4.0)),
                         lid_t_mm=4.0))

        shell, cart, hlid = build_hybrid(row)
        v_plastic = vol_cm3(shell) + vol_cm3(hlid)
        m_cart = vol_cm3(cart) * RHO_AL
        for mat in SHELL_MATS:
            mp = MATERIALS[mat]
            m_struct = v_plastic * mp["rho"] + m_cart
            rows.append(dict(design=key,
                             architecture="hybrid plastic + Al cartridge",
                             shell_material=mat,
                             structure_g=round(m_struct),
                             total_g=round(m_struct + mirrors_g),
                             lid_f1_hz=round(lid_first_mode_hz(
                                 env, mp, 6.0)),
                             lid_t_mm=6.0))
        print(f"{key}: all-Al {v_metal:.0f} cm^3, hybrid plastic "
              f"{v_plastic:.0f} cm^3 + Al cartridge {vol_cm3(cart):.0f} "
              f"cm^3", flush=True)
    df = pd.DataFrame(rows)
    out = os.path.join(_HERE, "designs", "hybrid_materials.csv")
    df.to_csv(out, index=False)
    with pd.option_context("display.width", 200):
        print(df.to_string(index=False))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
