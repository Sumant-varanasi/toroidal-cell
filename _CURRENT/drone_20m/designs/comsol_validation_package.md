# COMSOL mirror-only validation package (toroidal ring port)

*(Implements Benoy's "COMSOL Ray-Tracing Validation Protocol for
Mirror-Only Multipass Gas-Cell Spot-Pattern Designs" (2026-07-08,
[prof_inputs](prof_inputs/comsol_ray_tracing_validation_protocol_mirror_only.txt))
for the chord-skip N-mirror ring. "No need experiment. No need to model
the cell body." Tools: `comsol_package.py`, `compare_comsol.py`. Data:
[designs/comsol/](comsol/).)*

## What ships in `designs/comsol/`

| file | contents |
|---|---|
| `comsol_geom_<design>.csv` (×9) + `comsol_geom_all.csv` | every mirror's centre (mm), optical-axis normal, sagittal axis, ROC, clear-aperture radius, hole radius (mirror 0), plus a `launch_ray` row: exact entry point + unit direction, w0 (in `sagx`), wavelength mm (`sagy`), expected pass count (`sagz`), nominal OPL m (`roc_mm`). Frame: ring centre = origin, ring plane z = 0, mirror k at 2πk/N. |
| `comsol_perturbations.csv` | alignment-residual regimes (easy/medium/hard) and the two drone architecture envelopes (Al isostatic flexure; hybrid plastic body + Al cartridge) as per-axis maxima for the parametric sweeps. |
| `comsol_runlog_native.csv` | protocol step 7 executed with our exact tracer: nominal + every per-DOF coherent worst case (all mirrors at +max, then −max; each launch DOF at its box edge), 37 runs × 9 designs, in the protocol's run-log format (pass count, path length, edge/hole/exit clearance, PASS/FAIL). This is the reference answer sheet the COMSOL model should reproduce. |

## Building the COMSOL model (10 minutes per design)

1. **Physics**: 3D component → Ray Optics → Geometrical Optics. Air/vacuum
   background; no absorption (spot-pattern validation only).
2. **Geometry**: for each `mirror_k` row make a spherical cap: sphere
   radius = `roc_mm`, cap centre at (x, y, z), cap axis along (nx, ny, nz)
   (points from the mirror face toward the ring centre; the sphere centre
   sits at centre + ROC·n̂), clear radius = `aperture_r_mm`. Mirror 0
   additionally carries a concentric hole disk of `hole_r_mm` — model it
   as a postprocessing hit test (protocol §5.2) rather than a Boolean cut.
3. **Boundary conditions**: mirror caps = specular reflection; everything
   else absorbs. Store ray position at each boundary interaction.
4. **Release**: one chief ray from the `launch_ray` row (grid/bundle
   releases for the sensitivity stages). Sweep variables x_in, y_in
   (tangential/sagittal offsets at mirror 0), θ_t, θ_s.
5. **Sweeps**: (i) nominal; (ii) input sweeps to the capture envelopes in
   [capture_envelope.csv](capture_envelope.csv); (iii) per-DOF mirror
   perturbations from `comsol_perturbations.csv`; (iv) Monte-Carlo
   1000–5000 cases sampled uniformly inside the architecture envelope.
6. **Export**: chief-ray interaction points (x, y, z per bounce, ordered)
   to CSV → `compare_comsol.py --design <name> --csv <export>` reports
   RMS/worst deviation vs our tracer (pass < 10 µm, the same criterion the
   Optiland cross-validation met at 0.000 µm RMS).

## Native reference results (already run)

* Nominal: all 9 designs PASS with the expected pass count and OPL.
* Worst-case per-DOF (steps 7): **8 of 10 mirror-DOF extremes pass for
  every menu design**. The recurring failure is the coherent `d_ax` pair —
  all mirrors displaced radially by the same +max or −max, i.e. a uniform
  ring-radius change of 0.08 mm (flexure) / 0.18 mm (hybrid). That is the
  architecture's one soft axis: re-entrance accumulates ≈1.2 rad of
  transverse phase per mm of R_ring, so common-mode radial drift IS the
  thermal-breathing mode — already governed by the documented thermal
  windows (±26 K aluminium on the 20 m design) and the machined-trim law,
  and excluded from the random-drift budget by construction (a common-mode
  radial shift is a temperature signal, not a tolerance draw).
  Boundary designs (29 m ceiling, 14 cm compact) additionally fail the
  coherent `d_sag`+ (whole-ring vertical shift) at the hybrid envelope —
  consistent with their known walk-tightness.
* Per the protocol's own classification, a design failing a coherent
  worst case but passing Monte-Carlo is **marginal, requiring the drift
  source to be bounded** — for `d_ax` the bound is the thermal window,
  which the drone thermal budget already enforces.
* Monte-Carlo (step 8) at 5000 trials per design per architecture:
  [mc5000_drone_yield.csv](mc5000_drone_yield.csv) — run
  `drone_20m/mc5000.py`; yields and Wilson lower bounds vs the >99.9 %
  drone criterion, failure modes separated
  (incomplete / early-leak / exit-miss / overlap).

## Pass/fail thresholds (protocol §13, adopted)

* nominal pass count + exit direction: exact;
* no clipping of the beam bundle: `edge_clear_mm > 0`;
* pre-exit hole clearance: `hole_clear_mm > 0`;
* exit fully inside the hole: `exit_clear_mm ≥ 0`;
* MC yield: >99 % lab, >99.5 % field, **>99.9 % drone**.
