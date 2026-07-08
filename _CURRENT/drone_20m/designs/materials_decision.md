# Materials decision (the prof's "choose one combination for drone")

*(Benoy 2026-07-08: "Look up how the various cells are designed using
combination of various materials. Choose one combination for drone. Don't
chose titanium or Invar as they are expensive. Aluminium is a reasonable
choice." + "find a generic low-cost design capable of 3D printing with
plastic/peek." Evidence: [hybrid_materials.csv](hybrid_materials.csv),
[mc5000_drone_yield.csv](mc5000_drone_yield.csv),
[capture_envelope.csv](capture_envelope.csv), CAD in [cad/](cad/).)*

## The decision

**Drone baseline: machined aluminium 6061 monolithic ring** (mirror seats
cut in the body, one CNC setup), O-ring as gas seal only, three-dot epoxy
or spring-clip mirror retention, dowel-pinned collimator, direct 2 mm
detector. No titanium, no Invar: the composed-drift Monte-Carlo shows the
aluminium-flexure drift vector already yields ≥99.9 % on the drone-tier
designs, so the more expensive metals buy margin the designs do not need
(their one thermal weakness — common-mode ring-radius drift — is handled
by the trim law and the ±8–30 K thermal windows, not by CTE exotica).

**Low-cost route: hybrid printed shell + aluminium mirror cartridge.**
The printed polymer shell (with integral base) carries a machined
aluminium annulus holding every mirror pocket and the entry/exit cone on
three dowels — plastic never defines an optical datum. The only machined
part shrinks from the full housing to a simple ring; the print is a
tens-of-dollars part; the cartridge a $100–200 job.

## The evidence chain

1. **Mass** (CAD volumes, real solids): hybrid saves 33–46 % of structure —
   compact Ø141: 817 → 435 g; mini Ø129: 497 → 263 g; max Ø183:
   1270 → 688 g; two-inch Ø182: 1751 → 1056 g (PA12 shell; add ~2–4 %
   for CF-PA12, ~15 % for PEEK).
2. **Stiffness**: 6 mm printed lids hold their first mode at 475–1354 Hz;
   carbon-filled PA12 stays ≥674 Hz on every lid — above the 60–700 Hz
   (dominant <500 Hz) rotor band the aluminium lids clear by an octave.
3. **Drift → yield** (the number that decides): 5000-trial composed
   Monte-Carlo, uniform inside alignment-residual + drone drift:

   | design | Al flexure yield (Wilson LB) | hybrid yield (LB) |
   |---|---|---|
   | tri-gas 25.7 m | **100.00 % (99.92)** | 89.7 % (88.8) |
   | sparse 15.3 m | **100.00 % (99.92)** | 90.4 % (89.6) |
   | two-inch 19.0 m | **100.00 % (99.92)** | **95.0 % (94.3)** |
   | H2-opt. 23.8 m | 99.60 % | 64.6 % |
   | mini 9.1 m (½″) | 99.72 % | 64.8 % |
   | compact 20.7 m | 99.28 % | 63.6 % |
   | 27 m / 29 m / 22.3 m | 98.7 / 95.9 / 92.5 % | 70 / 37 / 53 % |

   Aluminium meets the >99.9 % drone product criterion outright on three
   designs; the hybrid is a research-grade option whose natural carrier is
   the sparse two-inch design (95 %) — exactly the prof's predicted
   trade ("plastic needs a relaxed spot-pattern tolerance envelope").
4. **Capture**: every design's input-drift capture envelope exceeds even
   the hybrid demand box by ≥2.2× position / ≥5.5× angle, so construction
   error is alignable in both architectures; the yield gap above is pure
   operational drift.

## What "generic low-cost 3D-printable design" means concretely

The **two-inch sparse design (19.0 m, Ø182, N = 8, k = 19)** in the hybrid
build: the largest clearances in the menu (hole margin 3.8 mm, aperture
margin 10.3 mm), 100 % as-built completion at every process grade
including FDM, 95 % hybrid drone yield, 1.06 kg structure. Files:
`cad/tmpc_19m_2in_hybrid.step` (+ per-part STLs for print quoting).
A PEEK shell is supported by the same cartridge (PEEK CTE 45–50 ppm/K vs
PA12 100+) for hot environments; for ordinary drone use CF-PA12 is the
better-stiffness cheaper print.

## Rejected options (and why, per the framework)

* **Titanium / Invar** — excluded by cost per the prof's directive; the
  yield table shows aluminium suffices for the drone tier.
* **All-plastic optical datum** (printed pockets carrying mirrors) —
  research-grade construction MC already passes on sparse designs, but the
  drone drift vector (0.7 mm / 3 mrad class) collapses yield; plastic
  creep/CTE/moisture also shrink the thermal closure window to ±2–6 K.
  Lab prototyping only.
* **Bosch-rail frames, O-ring-referenced mirrors, external kinematic
  stacks on the airframe** — the framework's own not-recommended list;
  our architecture never used them (monolithic ring = the anti-Bosch).
