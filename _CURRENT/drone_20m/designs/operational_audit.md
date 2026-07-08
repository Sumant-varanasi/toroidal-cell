# Operational physics audit — polarization, vibration, and everything else

*(Closes the "all aspects" loop for the paper: every effect a referee
may probe, either analyzed with numbers or bounded and dismissed with
numbers. Data: [polarization_audit.csv](polarization_audit.csv),
[mc400_new_designs.csv](mc400_new_designs.csv), tolerance-run
sensitivity tables.)*

## 1. Polarization (exact Jones-matrix accumulation over the traced path)

Over 98–204 gold reflections the s/p Fresnel differences accumulate, and
the sagittal launch tips the incidence plane slightly bounce-to-bounce.
Computed with complex-index Fresnel coefficients (bare-gold constants,
Babar & Weaver; the protective/enhancement dielectric perturbs ratios at
the <10⁻³/bounce level) along the exact traced geometry:

| design | AOI | s-launch purity at exit | 45°-launch exit ellipticity | s/p split (bare-gold worst case) |
|---|---|---|---|---|
| 20.4 m Ø180 (drone_20m) | 11.3° | **99.3 %** | 30° | ×1.13 over path |
| 25.7 m Ø185 (tri-gas) | 11.4° | **99.6 %** | 37° | ×1.17 |
| 15.3 m Ø175 (sparse) | 11.3° | **99.3 %** | 24° | ×1.10 |
| 20.7 m Ø141 (drone_14cm) | 15.1° | 96.3 % | 13° | ×1.33 |
| 9.1 m Ø129 (½″ mini) | 25.7° | **99.8 %** | −19° | ×1.57 |
| 14.9 m Ø133 (skip-3) | **36.0°** | 99.9 % | 6° | **×6.4** |

Design rules that follow:

1. **Launch linearly polarized along the sagittal (vertical) axis.** The
   incidence planes stay near-horizontal for the whole pattern, so s is
   an eigenaxis: s-launched light exits 96.3–99.9 % pure in every
   design. Fiber chain: use PM fiber keyed to sagittal, or a polarizer
   at the collimator.
2. **Do not put polarization-analyzing optics after the cell.** A 45°
   launch exits 6–39° elliptical (accumulated metallic retardance) with
   pattern-specific azimuth rotation — harmless for direct detection on
   a photodiode (our chain), hazardous for any polarization-filtered
   receive path.
3. The high-AOI skip-3 family (36°) is strongly diattenuating (up to
   ×6.4 s/p in bare-gold worst case; ~×1.1 rescaled to an R = 0.999
   coating) — one more reason the near-diameter (low-AOI) chord-skip
   family is the right architecture, and a quantitative novelty for the
   paper (polarization behaviour of dense re-entrant rings is not in
   the literature).

## 2. Vibration → signal budget ("will shaking show up in the spectra?")

Chain, at the ArduPilot-class operational level (1.5–3 g RMS broadband,
60–700 Hz; rubber dampers between airframe and cell at transmissibility
0.1–0.3 above 100 Hz per the flight-proven Empa configuration → 0.2–1 g
at the cell):

| link | magnitude | vs budget |
|---|---|---|
| elastic seat tilt, monolithic Al ring @1 g | stress ρgh ≈ 0.8 kPa → strain 1.2×10⁻⁸ → **0.01–0.1 µrad** | flight tilt budget 100 µrad: margin >10³ |
| resonant amplification | lid f₁ = 1.2–2.0 kHz (Al) is **above** the 60–700 Hz band; worst in-band Q≈50 edge case ≤ 10 µrad | margin >10 |
| ring radius modulation @1 g | <10 nm elastic | closure valley ±100 µm: margin 10⁴ |
| launch-chain pointing (collimator cantilever) | 1–10 µrad @1 g (kHz-class barrel modes) | MC launch-tilt σ = 100 µrad contributes ≲10 % of walk: vibration adds ~1 % |
| exit-spot jitter on detector | dominant *residual*: µrad-scale pointing × lever ≈ µm-scale spot motion | focus the exit (f ≤ 25 mm lens) and overfill margin; quad feedback in the active tier |
| aero-optic (rotor-wash δp ≈ 50 Pa) | δn ≈ 1.3×10⁻⁷ → δOPL ≈ 2.6 µm at 20 m, sub-10 Hz | common-mode baseline; invisible to WMS, fitted in DA |
| acoustic excitation of windows | wedged 3 mm windows, first modes ≫10 kHz | negligible |

Conclusion (matches the Empa flight finding): with the cell rigid inside
and damped outside, **vibration couples to the signal through the launch
and detector chain, not through the ring optics** — the mitigation is a
short stiff collimator boss (in the CAD), a focusing lens at the
detector, and dampers under the whole assembly. Numbers above give a
referee the margins; the Fusion-360 modal study on the shipped STEP is
the confirmation step for the specific machined part.

## 3. Remaining effects, bounded

* **Gravity/orientation sag**: ring self-weight deflection <0.5 µm; a
  90° attitude change re-orients it — absorbed by the walk budget
  (±100 µm class); re-zeroed by the standard trim anyway.
* **Mirror surface quality**: split correctly for the reviewer —
  low-order figure error (catalog λ/10 irregularity) is power/astigmatism
  → already Monte-Carloed as ROC error (±1 mm σ ≫ spec); Å-class
  polish roughness → TIS ≈ (4πσ/λ)² ≈ 10⁻⁵/bounce → 0.1–0.3 % total
  diffuse scatter over the path — this is precisely the stray-light
  reservoir whose interference the enforced spot separation suppresses
  (see the overlap criterion), closing the loop between surface spec
  and fringe budget.
* **Refractive-index of the sample** (1 atm ↔ vacuum): OPL changes by
  n−1 ≈ 2.7×10⁻⁴ (5.5 mm on 20.4 m) — a calibration constant, not a
  drift; pressure-driven variation is 10⁻⁶-scale.
* **Detector étendue (H₂ channel)**: extended-InGaAs is small (FD05D
  Ø0.5 mm). Exit drift p95 is 2.7–4.3 mrad (1″ designs) and 15.3 mrad
  (½″ mini): an f = 15–25 mm collection lens keeps the focused spot
  within ±0.4 mm — mandatory for the mini + H₂ combination; already in
  the spec-sheet pickoff geometry.
* **Contamination (open-flow mode)**: dust on gold at grazing spots adds
  scatter; mitigation: 10 µm inlet mesh, downward-facing apertures,
  periodic R check via the throughput monitor (T = R^(n−1) makes the
  cell its own reflectometer — a 0.01 % per-mirror change reads as 2 %
  transmission change on 204 bounces).
* **Condensation**: the ring trim heater doubles as an anti-dew heater;
  keep cell a few K above ambient dew point — consistent with the ±18–26
  K thermal windows.
* **Adhesive creep/ageing**: bonded mounts qualified to 20–40 g;
  post-cure creep appears as slow pattern walk — inside the trim
  authority (±10 K heater = ±17 µm ring-equivalent); recalibration
  interval set by the throughput monitor trend.
* **Laser power**: mW-class on Ø0.6 mm spots → W/cm² regime; damage
  thresholds are kW/cm²-class — no thermal lensing on gold at 10⁻³
  absorption of mW.

The paper can therefore claim tolerance coverage across machining,
assembly, coating lot, wavelength, temperature, humidity/moisture,
vibration, orientation, polarization and contamination — each with a
number, a margin, or a designed-in mitigation.
