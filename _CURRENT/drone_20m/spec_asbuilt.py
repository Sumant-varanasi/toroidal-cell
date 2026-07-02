"""As-built experiment spec generator for drone TMPC designs.

Takes verified rows from results/stage_b_polished.csv and writes, per
size class, a complete physical build + alignment specification:

  * machined ring geometry and per-mirror placement table (position,
    facing azimuth) -- the housing drawing numbers,
  * injection optics: hole position on mirror 0, beam size at the hole,
    in-cell waist size and its distance past the hole (collimator focus
    setting), launch tilts in mrad, exit-beam separation angle for the
    detector pickoff,
  * per-mirror spot constellation coordinates (u = in-plane, v = height),
  * chord/AOI/bounce accounting and the loss budget,
  * the full physical-check matrix from the exact ray trace.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/spec_asbuilt.py [--top-only]
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

from search_drone20m import (EXIT_TOL, HOLE_R, M2, REFL, TRUNC, W0,      # noqa: E402
                             WAVELENGTH, RADIAL_ALLOWANCE, evaluate,
                             waist_offset_for)
from tmpc_platform_v5 import TMPCConfig, simulate_tmpc                   # noqa: E402
from tmpc_platform_v5.physics import mirror_footprints                   # noqa: E402
from tmpc_platform_v5.samplers import FAMILIES                           # noqa: E402

MIRROR_PRICE_USD = 74.0     # CM254-xxx-M01 list ballpark
MIRROR_MASS_G = 20.0        # 1" gold mirror substrate
HOUSING_G_PER_MM = 2.6      # machined Al ring, ~3 mm wall, per mm dia


def cfg_from_row(row: dict) -> TMPCConfig:
    fam = FAMILIES[row["family"]]
    w0w = float(np.clip(row.get("w0_waist", W0), 0.25, W0))
    return TMPCConfig(
        N=int(row["N"]), R_ring=float(row["R_ring"]), H=40.0,
        R_t=float(row["roc"]), R_s=float(row["roc"]),
        mirror_aperture=fam["clear_aperture_radius_mm"],
        chord_skip=int(row["chord_skip"]),
        n_passes=int(row["n_target"]) + 2 * int(row["N"]),
        wavelength=WAVELENGTH, w0=w0w, M2=M2,
        input_waist_offset=waist_offset_for(w0w),
        input_offset_z=float(row["input_offset_z"]),
        input_angle=float(row["input_angle"]),
        input_angle_sag=float(row.get("input_angle_sag", 0.0)),
        reflectivity=REFL, hole_radius=HOLE_R)


def write_spec(row: dict, out_md: str, out_json: str) -> dict:
    r = evaluate({k: row[k] for k in (
        "family", "sku", "roc", "N", "chord_skip", "R_ring", "n_target",
        "mode_s", "input_offset_z", "input_angle", "input_angle_sag",
        "w0_waist", "envelope_max", "opl_min")})
    assert r["feasible"], f"row no longer feasible: {r['reason']}"

    cfg = cfg_from_row(row)
    res = simulate_tmpc(cfg)
    N, n_exit = cfg.N, int(r["n_exit"])
    hits = res.spot_pattern[:res.bounces]
    mseq = res.mirror_sequence[:res.bounces]
    foot = mirror_footprints(hits, mseq, cfg)
    w_eff = np.maximum(res.w_tangential, res.w_sagittal)[:res.bounces + 1]

    # geometry numbers
    chords = np.linalg.norm(np.diff(hits[:n_exit + 1], axis=0), axis=1)
    aoi = res.aoi[1:n_exit]                       # skip the hole pseudo-hit
    H = float(np.ceil(r["H_req_mm"] + 1.0))
    w0w = float(cfg.w0)
    z_off = float(cfg.input_waist_offset)
    n_refl = n_exit - 1

    # entrance/exit beam geometry at the hole
    d_in = hits[1] - hits[0]
    d_in /= np.linalg.norm(d_in)                  # first in-cell chord
    d_out = hits[n_exit] - hits[n_exit - 1]
    d_out /= np.linalg.norm(d_out)                # arriving at the hole
    sep_angle = float(np.degrees(np.arccos(np.clip(d_in @ d_out, -1, 1))))

    # per-mirror machining table
    place = []
    for k in range(N):
        th = 2 * np.pi * k / N
        place.append((k, cfg.R_ring * np.cos(th), cfg.R_ring * np.sin(th),
                      np.degrees(th),
                      (np.degrees(th) + 180.0) % 360.0))

    hole_uv = foot[0][foot[0][:, 2].astype(int) == 0][0, :2]
    mass = N * MIRROR_MASS_G + HOUSING_G_PER_MM * r["envelope_mm"]

    ok = lambda b: "PASS" if b else "FAIL"        # noqa: E731
    L = []
    L.append(f"# As-built spec -- class {row['size_class']}: "
             f"{r['opl_m']:.2f} m in a {r['envelope_mm']:.0f} mm envelope")
    L.append("")
    L.append(f"{N} x Thorlabs **{row['sku']}** (1\" protected-gold concave, "
             f"ROC {row['roc']:.0f} mm, CA radius "
             f"{cfg.mirror_aperture:.1f} mm, R = {REFL} @ 1654 nm)")
    L.append("")
    L.append("## 1. Machined ring housing")
    L.append("")
    L.append(f"| item | value |")
    L.append(f"|---|---|")
    L.append(f"| mirror-face ring radius R_ring | **{cfg.R_ring:.3f} mm** "
             f"(closure-critical: machine to +/-0.05 mm, then tune by "
             f"ring temperature / shims) |")
    L.append(f"| mirrors | N = {N}, every {360.0 / N:.2f} deg |")
    L.append(f"| pocket normal | radial, facing cell centre |")
    L.append(f"| cell height (inner) | {H:.0f} mm |")
    L.append(f"| assembly envelope | {r['envelope_mm']:.0f} mm dia "
             f"(R_ring + {RADIAL_ALLOWANCE:.0f} mm substrate+wall) |")
    L.append(f"| enclosed gas volume | "
             f"{np.pi * cfg.R_ring**2 * H * 1e-6:.2f} L |")
    L.append(f"| est. mass (mirrors + Al ring) | ~{mass:.0f} g |")
    L.append(f"| optics cost | {N} x ~${MIRROR_PRICE_USD:.0f} = "
             f"~${N * MIRROR_PRICE_USD:.0f} |")
    L.append("")
    L.append("Mirror placement (cell frame, z = 0 mid-height plane):")
    L.append("")
    L.append("| mirror | x [mm] | y [mm] | azimuth [deg] | "
             "normal azimuth [deg] |")
    L.append("|---|---|---|---|---|")
    for k, x, y, azd, nazd in place:
        L.append(f"| M{k} | {x:+8.3f} | {y:+8.3f} | {azd:7.2f} | "
                 f"{nazd:7.2f} |")
    L.append("")
    L.append("## 2. Injection / extraction optics (behind mirror M0)")
    L.append("")
    L.append(f"| item | value |")
    L.append(f"|---|---|")
    L.append(f"| entrance hole | radius {HOLE_R} mm through M0, centred "
             f"at (u, v) = ({hole_uv[0]:+.2f}, {hole_uv[1]:+.2f}) mm on "
             f"the mirror face (u = in-plane, v = height) |")
    L.append(f"| beam at the hole | 1/e^2 radius {W0} mm |")
    L.append(f"| in-cell waist | {w0w:.3f} mm, located "
             f"{z_off:.0f} mm past the hole (set collimator focus to "
             f"{z_off:.0f} mm) |")
    L.append(f"| launch tilt, in-plane | {cfg.input_angle * 1e3:+.2f} mrad "
             f"from the M0->M{cfg.chord_skip % N} chord |")
    L.append(f"| launch tilt, out-of-plane | "
             f"{cfg.input_angle_sag * 1e3:+.2f} mrad |")
    L.append(f"| launch height offset | {cfg.input_offset_z:+.2f} mm |")
    L.append(f"| exit beam | back through the same hole, "
             f"{sep_angle:.1f} deg from the injection axis -- place the "
             f"detector on that line behind M0 |")
    L.append("")
    L.append("## 3. Path accounting")
    L.append("")
    L.append(f"| item | value |")
    L.append(f"|---|---|")
    L.append(f"| OPL (hole -> hole) | **{r['opl_m']:.3f} m** |")
    L.append(f"| chords | {n_exit} legs, mean {np.mean(chords):.2f} mm "
             f"(min {np.min(chords):.2f}, max {np.max(chords):.2f}) |")
    L.append(f"| reflections | {n_refl} (R^{n_refl} = "
             f"{REFL ** n_refl * 100:.2f} %) |")
    L.append(f"| spots per mirror | {n_exit // N} |")
    L.append(f"| AOI | mean {np.mean(aoi):.2f} deg, "
             f"max {np.max(aoi):.2f} deg |")
    L.append(f"| beam radius in cell | {np.min(w_eff[:n_exit + 1]):.2f} "
             f"- {r['w_max_mm']:.2f} mm |")
    L.append(f"| throughput @ R = {REFL} | "
             f"**{r['throughput'] * 100:.2f} %** "
             f"= {TRUNC ** 2 * 100:.1f} % (hole in+out) x "
             f"{REFL ** n_refl * 100:.2f} % (mirrors) |")
    L.append(f"| throughput, parametric | T(R) = "
             f"{TRUNC ** 2:.4f} x R^{n_refl}  "
             f"(R = 0.984 -> {TRUNC**2 * 0.984**n_refl * 100:.2f} %, "
             f"R = 0.97 -> {TRUNC**2 * 0.97**n_refl * 100:.2f} %) |")
    L.append(f"| stability | m_tan = {r['stab_tan']:+.3f}, "
             f"m_sag = {r['stab_sag']:+.3f} (|m| <= 1) |")
    L.append("")
    L.append("## 4. Physical-check matrix (exact 3-D ray trace)")
    L.append("")
    L.append("| check | margin | verdict |")
    L.append("|---|---|---|")
    L.append(f"| exits through entrance hole | miss "
             f"{r['exit_miss_mm']:.3f} mm (tol {EXIT_TOL}) | "
             f"{ok(r['exit_miss_mm'] < 0.35)} |")
    L.append(f"| OPL >= {row['opl_min']} m | {r['opl_m']:.2f} m | "
             f"{ok(r['opl_m'] >= row['opl_min'])} |")
    L.append(f"| intermediate spots clear hole | "
             f"+{r['hole_margin_mm']:.2f} mm | "
             f"{ok(r['hole_margin_mm'] >= 0)} |")
    L.append(f"| beam edge inside clear aperture | "
             f"+{r['ap_margin_mm']:.2f} mm | {ok(r['ap_margin_mm'] >= 0)} |")
    L.append(f"| spot separation (fringe safety) | "
             f"+{r['sep_margin_mm']:.2f} mm beyond touching "
             f"(min sep {r['min_sep_mm']:.2f} mm) | "
             f"{ok(r['sep_margin_mm'] >= 0)} |")
    L.append(f"| per-plane stability | tan {r['stab_tan']:+.3f} / "
             f"sag {r['stab_sag']:+.3f} | "
             f"{ok(abs(r['stab_tan']) <= 1 and abs(r['stab_sag']) <= 1)} |")
    L.append(f"| envelope | {r['envelope_mm']:.0f} <= "
             f"{row['envelope_max']:.0f} mm | "
             f"{ok(r['envelope_mm'] <= row['envelope_max'])} |")
    pack = 2 * cfg.R_ring * np.sin(np.pi / N) - 25.4
    L.append(f"| mirror packing web | {pack:.2f} mm | {ok(pack >= 1.0)} |")
    L.append("")
    L.append("## 5. Spot constellations (mirror-face coordinates, mm)")
    L.append("")
    L.append("u = in-plane (tangential), v = height (sagittal); "
             "visit order in parentheses. M0 also shows the hole (H).")
    L.append("")
    for k in range(N):
        fk = foot[k]
        sel = fk[fk[:, 2].astype(int) <= n_exit]
        pts = "  ".join(
            f"({p[0]:+.2f},{p[1]:+.2f})#{int(p[2])}" for p in sel)
        tag = " [H = entrance hole at #0]" if k == 0 else ""
        L.append(f"- **M{k}**{tag}: {pts}")
    L.append("")
    L.append("Generated by drone_20m/spec_asbuilt.py from the exact "
             "ray-traced design; tolerances from the Monte-Carlo study "
             "in the same folder.")

    with open(out_md, "w") as fh:
        fh.write("\n".join(L) + "\n")
    cfg_kwargs = dict(
        N=N, chord_skip=cfg.chord_skip, R_ring=round(cfg.R_ring, 4),
        H=H, R_t=cfg.R_t, R_s=cfg.R_s,
        mirror_aperture=cfg.mirror_aperture, w0=round(w0w, 4), M2=M2,
        wavelength=WAVELENGTH,
        input_waist_offset=round(z_off, 2),
        input_offset_z=round(cfg.input_offset_z, 4),
        input_angle=round(cfg.input_angle, 6),
        input_angle_sag=round(cfg.input_angle_sag, 6),
        reflectivity=REFL, hole_radius=HOLE_R, n_passes=n_exit + 1)
    with open(out_json, "w") as fh:
        json.dump({"cfg": cfg_kwargs, "sku": row["sku"],
                   "size_class": row["size_class"],
                   "metrics": {k: (float(v) if isinstance(
                       v, (int, float, np.floating)) else v)
                       for k, v in r.items() if k != "reason"}},
                  fh, indent=2)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(_HERE, "results",
                                                  "stage_b_polished.csv"))
    ap.add_argument("--out-dir", default=os.path.join(_HERE, "results"))
    args = ap.parse_args(argv)

    df = pd.read_csv(args.csv)
    feas = df[df["feasible"]].copy()
    if not len(feas):
        print("no feasible designs")
        return 1
    print(f"{len(feas)} feasible designs across "
          f"{feas['size_class'].nunique()} classes")
    for cls, gr in feas.groupby("size_class"):
        corners = {
            "maxOPL": gr.sort_values(["opl_m", "throughput"],
                                     ascending=False).iloc[0],
            "maxT": gr.sort_values(["throughput", "opl_m"],
                                   ascending=False).iloc[0],
        }
        seen = set()
        for corner, row in corners.items():
            key = (row["sku"], row["N"], row["chord_skip"],
                   row["n_target"], round(row["R_ring"], 3))
            if key in seen:
                continue                     # both corners = same design
            seen.add(key)
            md = os.path.join(args.out_dir, f"spec_{cls}_{corner}.md")
            js = os.path.join(args.out_dir, f"design_{cls}_{corner}.json")
            r = write_spec(row.to_dict(), md, js)
            print(f"  {cls}/{corner}: {r['opl_m']:.2f} m @ "
                  f"{r['throughput']*100:.2f}% in "
                  f"{r['envelope_mm']:.0f} mm -> {os.path.basename(md)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
