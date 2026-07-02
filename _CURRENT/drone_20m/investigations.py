"""Post-design investigations for the drone TMPC headline designs.

1. ROC-error compensation: Thorlabs specs focal length to ~+/-1%. For a
   same-lot batch error applied to all mirrors, how much ring-radius trim
   restores closure, and does the design stay feasible? Output = the
   assembly rule 'measure ROC, machine the ring to R_ring(ROC)'.
2. Thermal window: an aluminium ring scales R_ring by 23.6 ppm/K
   (mirror ROC is glass, ~0 in comparison), detuning closure. Sweep
   delta-T with the launch FROZEN (operational drift, no re-alignment)
   and find the usable window; compare invar (1.2 ppm/K).
3. M^2 robustness: real DFB + fiber collimators are M^2 ~ 1.05-1.2;
   spot sizes scale with M2, shrinking separation margins.

Writes designs/investigations.md (+ CSV). Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/investigations.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import search_drone20m as S                                       # noqa: E402

DESIGNS = {
    "drone_20m": "design_D190_maxT.json",
    "drone_25m": "design_D190_maxOPL.json",
    "drone_16cm": "design_D160_maxOPL.json",
}
ALPHA_AL = 23.6e-6      # 6061 aluminium CTE [1/K]
ALPHA_INVAR = 1.2e-6    # invar 36 CTE [1/K]


def base_params(fname: str) -> dict:
    with open(os.path.join(_HERE, "designs", fname)) as fh:
        m = json.load(fh)["metrics"]
    return dict(
        family=m["family"], sku=m["sku"], roc=float(m["roc"]),
        N=int(m["N"]), chord_skip=int(m["chord_skip"]),
        R_ring=float(m["R_ring"]), n_target=int(m["n_target"]),
        mode_s=m["mode_s"],
        input_offset_z=float(m["input_offset_z"]),
        input_angle=float(m["input_angle"]),
        input_angle_sag=float(m["input_angle_sag"]),
        w0_waist=float(m["w0_waist"]),
        waist_frac=float(m["waist_frac"]),
        envelope_max=190.0, opl_min=0.0)   # study reports, classes don't gate


def scan_R(base: dict, span: float = 3.0, step: float = 0.01) -> dict:
    """Re-tune R_ring only (launch frozen) and return the best evaluate."""
    best, best_obj = None, np.inf
    for dR in np.arange(-span, span + 1e-9, step):
        r = S.evaluate({**base, "R_ring": base["R_ring"] + dR,
                        "exit_at_target": True})
        o = S._objective(r)
        if o < best_obj:
            best, best_obj = dR, o
    out = S.evaluate({**base, "R_ring": base["R_ring"] + best})
    out["dR_ring_mm"] = best
    return out


def roc_study() -> pd.DataFrame:
    rows = []
    for name, fname in DESIGNS.items():
        b = base_params(fname)
        for frac in (-0.01, -0.005, 0.0, 0.005, 0.01):
            p = dict(b)
            p["roc"] = b["roc"] * (1.0 + frac)
            r = scan_R(p)
            rows.append(dict(
                design=name, roc_err_pct=100 * frac,
                roc_mm=p["roc"], dR_ring_mm=r["dR_ring_mm"],
                R_ring_mm=b["R_ring"] + r["dR_ring_mm"],
                feasible=r["feasible"], exit_miss_mm=r["exit_miss_mm"],
                opl_m=r["opl_m"], throughput=r["throughput"],
                sep_margin_mm=r["sep_margin_mm"],
                envelope_mm=r["envelope_mm"], reason=r["reason"]))
            print(f"  {name} ROC{100*frac:+.1f}%: dR_ring="
                  f"{r['dR_ring_mm']:+.3f} mm feasible={r['feasible']} "
                  f"miss={r['exit_miss_mm']:.3f}", flush=True)
    return pd.DataFrame(rows)


def thermal_study() -> pd.DataFrame:
    rows = []
    dts = np.arange(-30, 30 + 1e-9, 2.0)
    for name, fname in DESIGNS.items():
        b = base_params(fname)
        for alpha, mat in ((ALPHA_AL, "aluminium"), (ALPHA_INVAR, "invar")):
            for dT in dts:
                p = dict(b)
                p["R_ring"] = b["R_ring"] * (1.0 + alpha * dT)
                r = S.evaluate(p)
                rows.append(dict(
                    design=name, material=mat, dT_K=float(dT),
                    feasible=r["feasible"],
                    exit_miss_mm=r["exit_miss_mm"],
                    throughput=r["throughput"], reason=r["reason"]))
    return pd.DataFrame(rows)


def m2_study() -> pd.DataFrame:
    rows = []
    for name, fname in DESIGNS.items():
        b = base_params(fname)
        for m2 in (1.0, 1.05, 1.1, 1.2, 1.3):
            r = S.evaluate({**b, "M2": m2})
            rows.append(dict(
                design=name, M2=m2, feasible=r["feasible"],
                sep_margin_mm=r["sep_margin_mm"],
                hole_margin_mm=r["hole_margin_mm"],
                w_max_mm=r["w_max_mm"], throughput=r["throughput"],
                exit_miss_mm=r["exit_miss_mm"], reason=r["reason"]))
    return pd.DataFrame(rows)


def window(df: pd.DataFrame, design: str, mat: str) -> str:
    d = df[(df.design == design) & (df.material == mat)
           & df.feasible].dT_K
    if not len(d):
        return "none"
    return f"{d.min():+.0f}..{d.max():+.0f} K"


def main() -> int:
    out_dir = os.path.join(_HERE, "designs")
    print("=== 1. ROC-error compensation ===", flush=True)
    roc = roc_study()
    roc.to_csv(os.path.join(out_dir, "study_roc_compensation.csv"),
               index=False)
    print("=== 2. Thermal window ===", flush=True)
    th = thermal_study()
    th.to_csv(os.path.join(out_dir, "study_thermal.csv"), index=False)
    print("=== 3. M^2 robustness ===", flush=True)
    m2 = m2_study()
    m2.to_csv(os.path.join(out_dir, "study_m2.csv"), index=False)

    L = ["# Engineering investigations -- drone TMPC headline designs", ""]
    L.append("## 1. ROC-error compensation (assembly rule)")
    L.append("")
    L.append("Same-lot ROC error applied to every mirror; the machined "
             "ring radius is re-trimmed (launch untouched). Feasibility "
             "means the FULL check matrix passes again.")
    L.append("")
    L.append("| design | ROC error | ring trim dR_ring | feasible | "
             "exit miss | OPL | T |")
    L.append("|---|---|---|---|---|---|---|")
    for _, r in roc.iterrows():
        L.append(f"| {r.design} | {r.roc_err_pct:+.1f} % | "
                 f"{r.dR_ring_mm:+.3f} mm | "
                 f"{'PASS' if r.feasible else 'FAIL'} | "
                 f"{r.exit_miss_mm:.3f} mm | {r.opl_m:.2f} m | "
                 f"{100 * r.throughput:.1f} % |")
    L.append("")
    L.append("Assembly procedure: measure the delivered mirrors' actual "
             "ROC (autocollimator or interferometer), then machine the "
             "ring to the trimmed R_ring from this table (interpolate "
             "linearly); final closure is walked in with the ring-"
             "temperature / shim trim.")
    L.append("")
    L.append("## 2. Thermal operating window (launch frozen)")
    L.append("")
    L.append("| design | aluminium ring | invar ring |")
    L.append("|---|---|---|")
    for name in DESIGNS:
        L.append(f"| {name} | {window(th, name, 'aluminium')} | "
                 f"{window(th, name, 'invar')} |")
    L.append("")
    L.append("Window = delta-T range (from the alignment temperature) "
             "where every check still passes with no re-alignment. "
             "Outside it the exit spot walks off the hole; a lab-grade "
             "5 K cabin/enclosure or an invar ring both work -- or "
             "actively trim the ring temperature, which doubles as the "
             "closure fine-tuning knob.")
    L.append("")
    L.append("## 3. Beam-quality robustness")
    L.append("")
    L.append("| design | M2=1.0 | 1.05 | 1.1 | 1.2 | 1.3 |")
    L.append("|---|---|---|---|---|---|")
    for name in DESIGNS:
        cells = []
        for m2v in (1.0, 1.05, 1.1, 1.2, 1.3):
            row = m2[(m2.design == name) & (m2.M2 == m2v)].iloc[0]
            cells.append("PASS" if row.feasible
                         else f"FAIL({row.sep_margin_mm:+.2f})")
        L.append(f"| {name} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("(FAIL cells show the spot-separation margin; the fix is a "
             "slightly larger launch amplitude at design time.)")
    with open(os.path.join(out_dir, "investigations.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
