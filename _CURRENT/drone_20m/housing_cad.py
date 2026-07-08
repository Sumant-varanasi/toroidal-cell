"""Parametric CAD generator for the TMPC drone housing.

Generates a manufacturable skeleton of the cell for a chosen design from
the robust menu and exports STEP (imports directly into Fusion 360 /
SolidWorks for FEA, drawings, DFM edits) plus STL (print quoting).

Model contents:
  * ring body: outer cylinder at the design envelope, central cavity
    bore, N radial mirror pockets (flat-bottom, Ø25.6 mm, bottom plane at
    R_ring + substrate thickness so every mirror face centre sits exactly
    on the design ring radius),
  * mirror-0 rear port: conical clearance bore (half-angle AOI + 8°) for
    the entry and exit beams through the coupling hole, with a flat
    window/collimator boss on the outer wall,
  * two gas ports (M5 clearance) in the ring wall,
  * lid and base plates with a matching bolt circle,
  * three mounting bosses on the base.

This is deliberately geometry-first: O-ring grooves, thread specs and
final wall thinning are DFM steps for Fusion 360. The point is that every
optical datum (ring radius, pocket tilt = 0, seat depth, port angles) is
generated from the verified design row, so the CAD cannot drift from the
optics.

Run from _CURRENT/ (after: pip install cadquery):
    ../.venv/Scripts/python.exe drone_20m/housing_cad.py --design 14cm
    ../.venv/Scripts/python.exe drone_20m/housing_cad.py --design 20m
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import cadquery as cq                                             # noqa: E402

FAMILY_DIMS = {
    "one_inch": dict(mirror_dia=25.4, mirror_t=6.35),
    "half_inch": dict(mirror_dia=12.7, mirror_t=6.35),
    "two_inch": dict(mirror_dia=50.8, mirror_t=12.7),
}
POCKET_CLEAR = 0.10        # press-fit-ish pocket clearance on radius [mm]
PLATE_T = 4.0
BOLT_D = 3.4               # M3 clearance
BOSS_D = 12.0

DESIGNS = {
    "14cm": ("robust_menu_flight.csv", "CM254-500-M01", 12, 204),
    "20m": ("robust_menu.csv", "CM254-150-M01", 16, 144),
    "29m": ("robust_menu_flight.csv", "CM254-750-M01", 12, 204),
    "9m_mini": ("robust_menu_minihole_flight.csv", "CM127-050-M01", 14, 98),
    "19m_2in": ("robust_menu_twoinch_flight.csv", "CM508-150-M01", 8, 152),
}


def load_row(key: str) -> dict:
    f, sku, n_mir, n_exit = DESIGNS[key]
    d = pd.read_csv(os.path.join(_HERE, "designs", f))
    m = d[(d["sku"] == sku) & (d["N"] == n_mir) & (d["n_exit"] == n_exit)]
    if not len(m):
        raise SystemExit(f"design {key} not found in {f}")
    return m.iloc[0].to_dict()


def build(row: dict):
    N = int(row["N"])
    fam = FAMILY_DIMS[str(row.get("family", "one_inch"))]
    mirror_dia, mirror_t = fam["mirror_dia"], fam["mirror_t"]
    wall_h = mirror_dia + 5.2                 # cavity: mirror + seal clear
    r_ring = float(row["R_ring"])
    r_od = float(row["envelope_mm"]) / 2.0
    aoi = np.deg2rad(float(row["aoi_deg"]))
    r_cav = r_ring - 2.0                      # cavity bore radius
    seat_r = r_ring + mirror_t                # pocket bottom radial distance

    # ---- ring body --------------------------------------------------------
    body = (cq.Workplane("XY")
            .circle(r_od).extrude(wall_h)
            .faces(">Z").workplane()
            .hole(2 * r_cav, wall_h))

    # mirror pockets: flat-bottom radial bores
    for q in range(N):
        ang = 2 * np.pi * q / N
        cx, cy = np.cos(ang), np.sin(ang)
        pocket = (cq.Workplane(cq.Plane(
            origin=(seat_r * cx, seat_r * cy, wall_h / 2.0),
            xDir=(-cy, cx, 0), normal=(cx, cy, 0)))
            .circle(mirror_dia / 2.0 + POCKET_CLEAR)
            .extrude(-(seat_r - r_cav + 0.5)))
        body = body.cut(pocket)

    # ---- mirror-0 rear port: cone for entry+exit beams --------------------
    cone_half = aoi + np.deg2rad(8.0)
    cone_len = r_od - r_ring + 6.0
    r_tip, r_base = 2.0, 2.0 + cone_len * np.tan(cone_half)
    cone = cq.Solid.makeCone(r_tip, r_base, cone_len,
                             cq.Vector(r_ring - 1.0, 0, wall_h / 2.0),
                             cq.Vector(1, 0, 0))
    body = body.cut(cq.Workplane(obj=cone))
    # window/collimator boss pad: flat milled on the outer wall
    boss_w = min(30.0, r_od * 0.45)
    boss = (cq.Workplane(cq.Plane(origin=(r_od - 1.5, 0, wall_h / 2.0),
                                  xDir=(0, 1, 0), normal=(1, 0, 0)))
            .rect(boss_w, wall_h * 0.85).extrude(6.0))
    body = body.union(boss)

    # ---- gas ports ---------------------------------------------------------
    for ang_deg in (90.0, 270.0):
        a = np.deg2rad(ang_deg)
        cx, cy = np.cos(a), np.sin(a)
        port = (cq.Workplane(cq.Plane(
            origin=((r_od + 1) * cx, (r_od + 1) * cy, wall_h / 2.0),
            xDir=(-cy, cx, 0), normal=(-cx, -cy, 0)))
            .circle(2.5).extrude(r_od - r_cav + 2.0))
        body = body.cut(port)

    # ---- bolt circle -------------------------------------------------------
    r_bolt = (r_od + r_ring + mirror_t) / 2.0 + 2.0
    r_bolt = min(r_bolt, r_od - 4.0)
    bolt_angs = [2 * np.pi * (q + 0.5) / N for q in range(N)]

    def with_bolts(wp):
        for a in bolt_angs:
            wp = wp.faces(">Z").workplane(centerOption="CenterOfBoundBox") \
                   .pushPoints([(r_bolt * np.cos(a), r_bolt * np.sin(a))]) \
                   .hole(BOLT_D)
        return wp

    body = with_bolts(body)
    lid = with_bolts(cq.Workplane("XY", origin=(0, 0, wall_h))
                     .circle(r_od).extrude(PLATE_T))
    base = cq.Workplane("XY", origin=(0, 0, -PLATE_T)) \
        .circle(r_od).extrude(PLATE_T)
    for a in (90, 210, 330):
        ar = np.deg2rad(a)
        base = base.union(
            cq.Workplane("XY", origin=((r_od - 8) * np.cos(ar),
                                       (r_od - 8) * np.sin(ar), -PLATE_T))
            .circle(BOSS_D / 2).extrude(-4.0))
    base = with_bolts(base)
    return body, lid, base


def build_hybrid(row: dict):
    """Hybrid architecture per the prof's low-cost directive: printable
    plastic outer shell (with integral base) + machined aluminium
    mirror-cartridge ring carrying every optical datum, + plastic lid.

    The cartridge is an annulus holding the N mirror pockets and the
    mirror-0 entry/exit cone; it drops into the shell on three dowels so
    the plastic never defines mirror position or tilt (O-ring stays a
    seal only, per the framework)."""
    N = int(row["N"])
    fam = FAMILY_DIMS[str(row.get("family", "one_inch"))]
    mirror_dia, mirror_t = fam["mirror_dia"], fam["mirror_t"]
    wall_h = mirror_dia + 5.2
    r_ring = float(row["R_ring"])
    r_od = float(row["envelope_mm"]) / 2.0
    aoi = np.deg2rad(float(row["aoi_deg"]))
    r_cav = r_ring - 2.0
    seat_r = r_ring + mirror_t
    r_cart = min(seat_r + 4.0, r_od - 4.5)   # cartridge outer radius
    gap = 0.30                                # shell/cartridge clearance

    # ---- aluminium cartridge ring -----------------------------------------
    cart = (cq.Workplane("XY").circle(r_cart).extrude(wall_h)
            .faces(">Z").workplane().hole(2 * r_cav, wall_h))
    for q in range(N):
        ang = 2 * np.pi * q / N
        cx, cy = np.cos(ang), np.sin(ang)
        pocket = (cq.Workplane(cq.Plane(
            origin=(seat_r * cx, seat_r * cy, wall_h / 2.0),
            xDir=(-cy, cx, 0), normal=(cx, cy, 0)))
            .circle(mirror_dia / 2.0 + POCKET_CLEAR)
            .extrude(-(seat_r - r_cav + 0.5)))
        cart = cart.cut(pocket)
    cone_half = aoi + np.deg2rad(8.0)
    cone_len = r_od - r_ring + 6.0
    r_tip, r_base = 2.0, 2.0 + cone_len * np.tan(cone_half)
    cone = cq.Solid.makeCone(r_tip, r_base, cone_len,
                             cq.Vector(r_ring - 1.0, 0, wall_h / 2.0),
                             cq.Vector(1, 0, 0))
    cart = cart.cut(cq.Workplane(obj=cone))
    r_dowel = (r_cav + seat_r) / 2.0
    for a_deg in (30.0, 150.0, 270.0):
        a = np.deg2rad(a_deg)
        cart = (cart.faces("<Z")
                .workplane(centerOption="CenterOfBoundBox")
                .pushPoints([(r_dowel * np.cos(a), -r_dowel * np.sin(a))])
                .hole(3.0, 6.0))

    # ---- plastic shell: outer wall + integral base -------------------------
    shell = (cq.Workplane("XY").circle(r_od).extrude(wall_h)
             .faces(">Z").workplane().hole(2 * (r_cart + gap), wall_h))
    floor = (cq.Workplane("XY", origin=(0, 0, -PLATE_T))
             .circle(r_od).extrude(PLATE_T))
    for a_deg in (30.0, 150.0, 270.0):    # dowel bosses in the floor
        a = np.deg2rad(a_deg)
        floor = (floor.faces(">Z")
                 .workplane(centerOption="CenterOfBoundBox")
                 .pushPoints([(r_dowel * np.cos(a), r_dowel * np.sin(a))])
                 .hole(3.0, PLATE_T / 2.0))
    shell = shell.union(floor)
    shell = shell.cut(cq.Workplane(obj=cone))   # cone continues outward
    boss_w = min(30.0, r_od * 0.45)
    boss = (cq.Workplane(cq.Plane(origin=(r_od - 1.5, 0, wall_h / 2.0),
                                  xDir=(0, 1, 0), normal=(1, 0, 0)))
            .rect(boss_w, wall_h * 0.85).extrude(6.0))
    shell = shell.union(boss).cut(cq.Workplane(obj=cone))

    # ---- plastic lid with axial gas ports ----------------------------------
    lid = (cq.Workplane("XY", origin=(0, 0, wall_h))
           .circle(r_od).extrude(PLATE_T))
    for sx in (+1.0, -1.0):
        lid = (lid.faces(">Z").workplane(centerOption="CenterOfBoundBox")
               .pushPoints([(sx * r_cav / 2.0, 0.0)]).hole(5.0))

    # ---- bolt circle through lid + shell wall ------------------------------
    r_bolt = (r_cart + gap + r_od) / 2.0
    bolt_angs = [2 * np.pi * (q + 0.5) / N for q in range(N)]
    for a in bolt_angs:
        pt = [(r_bolt * np.cos(a), r_bolt * np.sin(a))]
        lid = (lid.faces(">Z").workplane(centerOption="CenterOfBoundBox")
               .pushPoints(pt).hole(BOLT_D))
        shell = (shell.faces(">Z")
                 .workplane(centerOption="CenterOfBoundBox")
                 .pushPoints(pt).hole(BOLT_D))
    return shell, cart, lid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="14cm", choices=sorted(DESIGNS))
    ap.add_argument("--hybrid", action="store_true",
                    help="plastic shell + aluminium mirror cartridge")
    ap.add_argument("--out-dir", default=os.path.join(_HERE, "designs",
                                                      "cad"))
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    row = load_row(args.design)
    if args.hybrid:
        shell, cart, lid = build_hybrid(row)
        tag = f"tmpc_{args.design}_hybrid"
        asm = cq.Assembly()
        asm.add(shell, name="shell_plastic", color=cq.Color(0.2, 0.25, 0.3))
        asm.add(cart, name="cartridge_al", color=cq.Color(0.75, 0.76, 0.78))
        asm.add(lid, name="lid_plastic", color=cq.Color(0.25, 0.3, 0.35))
        step = os.path.join(args.out_dir, f"{tag}.step")
        asm.save(step)
        parts = ((shell, "shell_plastic"), (cart, "cartridge_al"),
                 (lid, "lid_plastic"))
    else:
        body, lid, base = build(row)
        tag = f"tmpc_{args.design}"
        asm = cq.Assembly()
        asm.add(body, name="ring_body", color=cq.Color(0.75, 0.76, 0.78))
        asm.add(lid, name="lid", color=cq.Color(0.6, 0.62, 0.65))
        asm.add(base, name="base", color=cq.Color(0.6, 0.62, 0.65))
        step = os.path.join(args.out_dir, f"{tag}.step")
        asm.save(step)
        parts = ((body, "ring_body"), (lid, "lid"), (base, "base"))
    for part, nm in parts:
        cq.exporters.export(part, os.path.join(args.out_dir,
                                               f"{tag}_{nm}.stl"))
        v = part.val().Volume() if hasattr(part, "val") else part.Volume()
        print(f"  {nm}: volume {v / 1000.0:.1f} cm^3")
    print(f"design {args.design}: N={int(row['N'])} "
          f"R_ring={row['R_ring']:.3f} mm envelope="
          f"{row['envelope_mm']:.1f} mm AOI={row['aoi_deg']:.2f} deg")
    print(f"wrote {step} + {len(parts)} STLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
