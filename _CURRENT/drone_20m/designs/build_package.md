# Build package — tri-gas flagship (25.7 m) and standard-build (20.4 m) cells

*(Executes the paper's first next step up to the purchase order and the
bench: complete BOM, critical dimensions with tolerances, assembly and
alignment procedure. Companion documents:
[experimental_protocol.md](experimental_protocol.md) for acceptance
tests, [flight_system_plan.md](flight_system_plan.md) for the airborne
integration. CAD: [cad/](cad/); per-design machining numbers:
[spec_D190_26m.md](spec_D190_26m.md), spec_D190_maxT / drone_20m sheets.)*

## 1. Bill of materials

| # | item | part | qty | ~unit USD | notes |
|---|---|---|---|---|---|
| 1 | concave mirrors (flagship) | Thorlabs CM254-200-M01 (ROC 400) | 16 | 74 | one lot; record lot # |
| 1′ | concave mirrors (standard cell) | CM254-150-M01 (ROC 300) | 16 | 74 | |
| 2 | drilled mirror M0 | one of item 1 modified: Ø2.6 mm bore, rear countersink 60° to Ø6 | 1 | ~80 svc | ultrasonic/diamond drill from rear; ≤0.5 mm coated land removed at edge |
| 3 | ring housing | Al 6061-T6, from Ø200×40 stock; machine per §2 | 1 | 250–600 CNC | single-setup pockets |
| 4 | lid + base | Al 6061, 4 mm plates per CAD | 2 | incl. | O-ring groove per CAD DFM pass |
| 5 | window (CH₄+NH₃) | Thorlabs WW10530-C (Ø1/2″ UVFS wedged, 1050–1700 AR) | 1 | ~90 | |
| 6 | window (CH₄+H₂) | Thorlabs WW30530-D (Ø1/2″ sapphire wedged, 1.65–3.0 µm AR) | 1 | ~150 | c-cut; verify -D curve at 1653.7 nm on the test report |
| 7 | window O-ring | FKM, Ø12 × 1 mm section | 2 | 1 | NH₃-compatible (not NBR) |
| 8 | fibre collimator + mode-match lens | adjustable FC/APC collimator with f ≈ 2 mm asphere (collimation-package class) | 1 | 120 | focus ring = alignment trim; conjugates on spec sheet |
| 9 | alternative first stage | reflective OAP fibre collimator (protected silver/gold) | 1 | 400 | athermal, serves all three λ |
| 10 | laser (CH₄) | Eblana EP1654-DM (fibre-pigtailed DFB) | 1 | ~2k | |
| 11 | laser (NH₃) | Eblana EP1512-DM | 1 | ~2k | |
| 12 | laser (H₂) | Nanoplus / LD-PD 2122 nm DFB, PM pigtail | 1 | ~4k | PM key aligned sagittal (§6.6 of paper) |
| 13 | detector (CH₄/NH₃) | standard InGaAs, Ø1 mm class | 1 | 150 | |
| 14 | detector (H₂) | extended InGaAs (Thorlabs FD05D class) + f = 15–25 mm lens | 1 | 250 | lens mandatory (drift budget) |
| 15 | mirror adhesive | 3M/Loctite Hysol EA 9313 class | — | 40 | 20–40 g shock qual |
| 16 | ring heater + RTD | 10–20 W foil heater + PT100 + TEC-style PI loop | 1 | 120 | trim + anti-dew |
| 17 | dampers | 4× rubber isolators, 40–60 Sh A, sized to ~1.5 kg | 4 | 30 | between cell plate and airframe |
| 18 | gas fittings | 2× M5/barb + PTFE line | 2 | 20 | |

Optics + housing subtotal ≈ US$2.3–2.9k per cell excluding lasers.

## 2. Critical dimensions and callouts (flagship; standard cell in brackets)

| feature | value | tolerance / callout |
|---|---|---|
| ring radius R_ring (pocket-seat datum to axis) | **74.507 mm** [72.155] | ±0.020 machining; final value from §3 step 2 trim law |
| pocket azimuths | 16 × 22.500° | ±0.01° (single-setup rotary) |
| pocket seat plane | ⊥ radial axis at R_ring + 6.35 | flatness 0.010 mm over Ø25.6 (= 0.4 mrad); precision tier: lap to 0.003 |
| pocket bore | Ø25.50 H7, depth 7.0 | mirror is bonded, not pressed: 3 adhesive dots |
| M0 bore in housing | cone per CAD, half-angle AOI + 8° = 19.4° [19.3°] | window boss ⊥ bisector |
| coupling hole in mirror | Ø2.60 ±0.05, at face centre + (0, +0.338 mm) [(0, +0.543)] sagittal offset | position ±0.05; rear countersink |
| cavity bore | Ø(2·R_ring − 4) | ±0.1 |
| envelope | Ø185.0 [Ø180.3] × 33 h | — |
| gas ports | 2 × M5 at 90°/270° | — |
| lid/base bolt circle | 16 × M3 on Ø(R_ring + 12) | — |

## 3. Assembly & alignment procedure

1. **Incoming metrology.** Measure every mirror's ROC (autocollimator/
   interferometer, ±0.1 % goal); record per serial. Compute lot-mean ROC
   error ε [%].
2. **Ring trim law.** Machine R_ring = design value + 0.750·ε mm
   [0.72·ε]. (Linear law verified over ±1 %; interpolate freely.)
3. **Mirror bonding.** Bond 15 stock mirrors + the drilled M0 into
   pockets (3-dot epoxy, cure per datasheet, no clamping stress). M0's
   hole offset is oriented to the sagittal (+z) axis; scribe mark up.
4. **Window + ports.** Fit wedged window on the boss, wedge apex
   sagittal, boss gives the 3–5° tilt; torque lid/base with O-rings;
   leak-check to <10⁻³ mbar·L/s (soap/pressure decay is sufficient for
   flow-through use).
5. **Launch bench.** Mount collimator on the boss bracket; set the
   collimator focus to the spec-sheet conjugate (flagship: waist 0.295 mm
   at 72.3 mm past the hole; standard: 0.326 mm at 102 mm). Feed with
   the CH₄ DFB first regardless of target gas (visible on standard
   InGaAs card + strongest margins).
6. **First light.** Align launch tilts to the spec-sheet values (mrad
   entries) using the two adjuster screws; look for the exit spot at
   2×AOI (22.6–22.7°) behind M0 — target the quadrant/photodiode centre.
   Expected transmitted power at R = 0.999 lot: 83.9 % [86.7 %] ×
   window/collimator losses (~3–5 %).
7. **Ring-temperature walk-in.** With the PI loop, scan ring temperature
   ±3 K in 0.2 K steps while logging transmission: the closure peak is
   the setpoint (gain 1.7 µm/K ≈ 60 µrad of accumulated phase per K).
   Lock. This absorbs the final machining residual.
8. **Freeze.** Torque-seal the launch adjusters. For flight: verify the
   assembly passes the §experimental_protocol vibration profile with
   <5 % transmission modulation.
9. **Gas-line swap procedure.** Change laser + detector (+ window if
   moving to/from H₂); rescale collimator focus by √(λ₂/λ₁) (one ring
   turn — values on spec sheet); re-run step 7. No mechanical
   realignment of mirrors is required (Monte-Carlo verdicts in paper
   Table 7).

## 4. Acceptance gates (details in experimental_protocol.md)

* transmission within −5 % absolute of R^(n−1) × chain losses,
* exit spot within 1 mm of nominal position at 50 mm,
* fringe floor: NEA ≤ 1×10⁻⁴ direct / ≤ 1×10⁻⁵ WMS at 1 s,
* no chord-FSR-spaced structure (0.034 cm⁻¹) above 3× baseline noise,
* polarization purity ≥ 95 % sagittal-in/sagittal-out,
* thermal: lock holds over ±10 K ambient with heater authority to spare.
