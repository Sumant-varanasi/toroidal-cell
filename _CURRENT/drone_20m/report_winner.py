"""Full engineering verification of one drone-20m design.

Reads a design row (CLI flags or the top feasible row of
results/stage_b_polished.csv), re-traces it, and writes:

    results/winner_summary.md      -- all physical checks + loss budget + BOM
    results/winner_config.json     -- exact TMPCConfig kwargs (preset-ready)

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/report_winner.py
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

from search_drone20m import (EXIT_TOL, HOLE_R, M2, REFL, TRUNC, W0,       # noqa: E402
                             WAVELENGTH, RADIAL_ALLOWANCE, evaluate)
from tmpc_platform_v5.samplers import FAMILIES                            # noqa: E402

MIRROR_PRICE_USD = {"half_inch": 61.0, "one_inch": 75.0}   # ~Thorlabs list
MIRROR_MASS_G = {"half_inch": 5.0, "one_inch": 20.0}       # substrate approx


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(_HERE, "results",
                                                  "stage_b_polished.csv"))
    ap.add_argument("--rank", type=int, default=0,
                    help="which feasible row (sorted by OPL) to report")
    args = ap.parse_args(argv)

    df = pd.read_csv(args.csv)
    feas = df[df["feasible"]].sort_values(
        ["opl_m", "throughput"], ascending=False).reset_index(drop=True)
    if not len(feas):
        print("no feasible designs in", args.csv)
        return 1
    row = feas.iloc[args.rank].to_dict()

    job = dict(family=row["family"], sku=row["sku"], roc=float(row["roc"]),
               N=int(row["N"]), chord_skip=int(row["chord_skip"]),
               R_ring=float(row["R_ring"]), n_target=int(row["n_target"]),
               input_offset_z=float(row["input_offset_z"]),
               input_angle=float(row["input_angle"]))
    r = evaluate(job)
    assert r["feasible"], f"re-trace no longer feasible: {r['reason']}"

    fam = FAMILIES[row["family"]]
    n_refl = r["n_exit"] - 1
    refl_T = REFL ** n_refl
    H = float(np.ceil(r["H_req_mm"]))
    cfg_kwargs = dict(
        N=int(job["N"]), chord_skip=int(job["chord_skip"]),
        R_ring=round(job["R_ring"], 3), H=H,
        R_t=job["roc"], R_s=job["roc"],
        mirror_aperture=fam["clear_aperture_radius_mm"],
        w0=W0, M2=M2, wavelength=WAVELENGTH,
        input_offset_z=round(job["input_offset_z"], 4),
        input_angle=round(job["input_angle"], 5),
        reflectivity=REFL, hole_radius=HOLE_R,
        n_passes=int(r["n_exit"]) + 1,
    )
    with open(os.path.join(_HERE, "results", "winner_config.json"),
              "w") as fh:
        json.dump({"cfg": cfg_kwargs, "sku": row["sku"],
                   "family": row["family"], "metrics": {
                       k: (float(v) if isinstance(v, (int, float, np.floating))
                           else v) for k, v in r.items()}}, fh, indent=2)

    chord = 2 * job["R_ring"] * np.sin(np.pi * job["chord_skip"] / job["N"])
    vol_L = np.pi * job["R_ring"] ** 2 * H * 1e-6
    mass_mirrors = job["N"] * MIRROR_MASS_G[row["family"]]
    price = job["N"] * MIRROR_PRICE_USD[row["family"]]

    ok = lambda b: "PASS" if b else "FAIL"          # noqa: E731
    lines = [
        "# Drone 20 m TMPC -- winning design",
        "",
        f"**Mirror**: {int(job['N'])} x Thorlabs **{row['sku']}** "
        f"({fam['diameter_mm']:.1f} mm dia protected-gold concave, "
        f"ROC {job['roc']:.0f} mm, clear-aperture radius "
        f"{fam['clear_aperture_radius_mm']} mm, R = {REFL} @ 1654 nm)",
        "",
        "## Geometry",
        "",
        f"| parameter | value |",
        f"|---|---|",
        f"| mirrors N | {int(job['N'])} |",
        f"| chord_skip | {int(job['chord_skip'])} |",
        f"| ring radius R_ring | {job['R_ring']:.2f} mm |",
        f"| chord length | {chord:.1f} mm |",
        f"| mean AOI | {r['aoi_deg']:.2f} deg |",
        f"| cell height H | {H:.0f} mm |",
        f"| assembly envelope | {r['envelope_mm']:.0f} mm dia "
        f"(= 2 x (R_ring + {RADIAL_ALLOWANCE:.0f} mm allowance)) |",
        f"| enclosed gas volume | {vol_L:.2f} L |",
        f"| entrance hole radius | {HOLE_R} mm (mirror 0, at first spot) |",
        f"| launch | waist w0 = {W0} mm at the hole, "
        f"offset_z = {job['input_offset_z']:.2f} mm, "
        f"in-plane tilt = {job['input_angle'] * 1e3:.2f} mrad |",
        "",
        "## Performance",
        "",
        f"| metric | value |",
        f"|---|---|",
        f"| optical path length | **{r['opl_m']:.2f} m** |",
        f"| passes (hole to hole) | {int(r['n_exit'])} chords, "
        f"{n_refl} reflections |",
        f"| spots per mirror | {int(r['n_exit']) // int(job['N'])} |",
        f"| throughput | **{r['throughput'] * 100:.2f} %** |",
        f"|   - mirror reflections {REFL}^{n_refl} | {refl_T * 100:.2f} % |",
        f"|   - hole truncation in + out (2 x 13.5 %) | "
        f"{TRUNC ** 2 * 100:.1f} % |",
        f"| max beam radius in cell | {r['w_max_mm']:.2f} mm |",
        "",
        "## Physical checks (exact 3-D trace)",
        "",
        f"| check | margin | verdict |",
        f"|---|---|---|",
        f"| exits through entrance hole | miss = {r['exit_miss_mm']:.3f} mm "
        f"(< {EXIT_TOL} mm) | {ok(r['exit_miss_mm'] < EXIT_TOL)} |",
        f"| OPL >= 19.5 m | {r['opl_m']:.2f} m | {ok(r['opl_m'] >= 19.5)} |",
        f"| intermediate spots clear hole | +{r['hole_margin_mm']:.2f} mm "
        f"beyond hole edge + beam radius | {ok(r['hole_margin_mm'] >= 0)} |",
        f"| beam edge inside clear aperture | +{r['ap_margin_mm']:.2f} mm "
        f"| {ok(r['ap_margin_mm'] >= 0)} |",
        f"| no spot overlap (sep - sum of radii) | "
        f"+{r['sep_margin_mm']:.2f} mm (min sep {r['min_sep_mm']:.2f} mm) "
        f"| {ok(r['sep_margin_mm'] >= 0)} |",
        f"| tangential stability m | {r['stab_tan']:.3f} "
        f"| {ok(abs(r['stab_tan']) <= 1)} |",
        f"| sagittal stability m | {r['stab_sag']:.3f} "
        f"| {ok(abs(r['stab_sag']) <= 1)} |",
        f"| envelope < 190 mm | {r['envelope_mm']:.0f} mm "
        f"| {ok(r['envelope_mm'] <= 190)} |",
        f"| ring packing (edge gap) | "
        f"{2 * job['R_ring'] * np.sin(np.pi / job['N']) - fam['diameter_mm']:.2f} mm "
        f"| {ok(2 * job['R_ring'] * np.sin(np.pi / job['N']) >= fam['diameter_mm'] + 1.0)} |",
        "",
        "## Drone bill of materials (optics)",
        "",
        f"| item | qty | ~unit price | mass |",
        f"|---|---|---|---|",
        f"| {row['sku']} gold concave mirror | {int(job['N'])} | "
        f"${MIRROR_PRICE_USD[row['family']]:.0f} | "
        f"{MIRROR_MASS_G[row['family']]:.0f} g |",
        f"| **totals (mirrors only)** | | "
        f"**${price:.0f}** | **{mass_mirrors:.0f} g** |",
        "",
        f"Machined Al ring housing (~{r['envelope_mm']:.0f} mm dia x "
        f"{H:.0f} mm, ~3 mm wall) adds roughly 300-450 g; "
        "total optical head well under 1 kg -- drone-portable.",
        "",
        "Laser + collimator inject from OUTSIDE the ring through the back "
        "of mirror 0; after the final pass the beam exits back through the "
        "same hole, angularly separated from the input by twice the AOI, "
        "onto a detector beside the collimator.",
    ]
    out_md = os.path.join(_HERE, "results", "winner_summary.md")
    with open(out_md, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n-> {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
