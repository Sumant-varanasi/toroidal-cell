# Manufacturing, weight, vibration and "construction tolerance"

*(Dr. Benoy, 2026-07-08: "Now think how you will design the actual cell in
Fusion 360. Can you design using 3D printing? Or do you need CNC machining?
Using aluminium and various materials, do simulation for weight and
vibration... This is called construction tolerance. Will the gas cell
survive construction tolerance? ... say if we can 3D print something under
200$.")*

## 0. The deliverables

* **Parametric CAD** generated *from the verified optics rows* (ring
  radius, pocket azimuths, seat depth, mirror-0 beam cone at the design
  AOI, window boss, gas ports, bolt circle): [cad/](cad/) contains STEP
  (imports directly into Fusion 360 for DFM/FEA) + STL (print quoting)
  for `tmpc_14cm` (Ø141), `tmpc_20m` (Ø180), `tmpc_29m` (Ø183) —
  regenerate with `housing_cad.py --design {14cm,20m,29m}`. Because the
  CAD is generated from the design row, the optical datums cannot drift
  from the verified optics. Fusion 360 next steps for the team: shell
  the ring where stress allows, add O-ring grooves + window bezel,
  modal + static FEA on the STEP.
* **Construction-tolerance Monte-Carlo** — our exact ray-tracer MC run
  at tolerance grades mapped from published process capabilities:
  [construction_tolerance.csv](construction_tolerance.csv).
* **Materials table** (mass, first mode, thermal window, moisture):
  [materials_table.csv](materials_table.csv).

## 1. Construction tolerance: mapping processes onto the optics

Process capability (vendor/ISO data) mapped to our MC inputs — mirror-seat
tilt σ = seat flatness / 25.4 mm seat; ring radius σ from radial accuracy:

| process | tilt σ [mrad] | R_ring σ [mm] | one-off cost, 180×30 disc |
|---|---|---|---|
| CNC precision + lapped seats ("flight") | 0.1 | 0.02 | $600–1200 |
| CNC standard (ISO 2768-f + callouts) | 0.5 | 0.10 | $250–600 (US); ~half offshore |
| printed body + machined seats (hybrid) | 0.3 | 0.10 | $150–350 |
| SLA industrial (tough resin) | 1.5 | 0.15 | $60–150 |
| MJF/SLS (PA12) | 2.5 | 0.25 | $80–250 |
| FDM (PLA/PETG) | 4.0 | 0.30 | $20–60 |

100-trial exact-trace MC per design per grade (full criteria: path
completes, spots stay separated, intermediate spots clear the hole, exit
leaves the 1.3 mm hole with **no realignment**):

| build | drone_20m (20.4 m, 144 chords) | drone_14cm (20.7 m, 204 chords) | drone_29m (29.0 m, 204 chords) |
|---|---|---|---|
| CNC precision | **survives, as-built** (100 %) | **survives, as-built** (100 %) | **survives, as-built** (99 %) |
| CNC standard | completes 100 %, needs one trim (exit walk 0.92+0.48 = 1.40 > 1.3 mm) | dies (54 % completion) | dies (44 %) |
| printed + machined seats | completes 100 %, needs one trim (1.32 vs 1.30 mm — misses by 20 µm) | 75 % completion — no | 68 % — no |
| SLA | 99 % completion but spots merge (sep p05 = 0.20 mm) | 12 % | 11 % |
| MJF/SLS | 74 % | 3 % | 1 % |
| FDM | 31 % | 2 % | 1 % |

**Answer to "will the gas cell survive construction tolerance":**

* The **dense-pattern designs (k = 17, 204 chords) survive only
  precision-CNC aluminium.** That is also the flight build the drone
  needs for vibration anyway — no extra cost is being imposed by the
  optics.
* The **headline 20.4 m design (k = 9, 144 chords) is the
  manufacturing-tolerant member of the menu**: it completes the full
  path at 100 % even on standard CNC and on a printed body with machined
  seats, and fails only the *no-realignment exit* criterion — by 20 µm
  of pattern walk. With the one ring-shim/temperature trim and launch
  alignment that every build performs, both cheap builds are usable lab
  cells. Sparse patterns are the low-cost-manufacturing corner: fewer
  spots per mirror → wider spacing → more walk budget.
* **A fully-printed $200 polymer cell does not survive** — and the
  failure is structural, not just statistical: (a) best industrial SLA
  holds ±0.15 % → ±0.27 mm on a 180 mm part vs our ±0.1 mm ring budget;
  polymer seat surfaces cannot hold 2.5–12.7 µm flatness (0.1–0.5 mrad);
  (b) even a perfectly printed ring drifts out of tolerance in service:
  PA12 CTE ≈ 109 ppm/K shrinks the thermal closure window to ±2–6 K
  (vs ±8–26 K for Al), and PA12 moisture swelling (0.2–0.3 % linear)
  moves the ring radius 42–110 µm with the weather — the whole budget;
  (c) FDM bodies are 98–99 % dense and leak without epoxy infiltration;
  unbaked prints outgas into the absorption volume (SLA is the least bad:
  water-dominated, 1.9×10⁻⁸ mbar demonstrated after bake).
* The literature agrees: published 3D-printed multipass cells succeed
  only at 4–6 cm scale with tolerance-forgiving two-mirror Herriott
  geometries (best: 4.2 m path, 288 ppb CH₄ MDL, Anal. Chem. 2020), and
  the one flight-proven ring cell (Empa SC-MPC on a DJI M600) is
  monolithic CNC aluminium, <200 g bare.

**Where printing IS the right tool:** window bezels, detector/collimator
shrouds, cable/fan ducting, the enclosure, and a $50 FDM fit-check of the
full assembly before committing the CNC order (we ship STLs for exactly
this). A printed *kinematic* variant (printed body + steel balls +
adjuster screws per mirror) can match commercial mounts on repeatability
and would make a fine classroom/lab demonstrator — but it forfeits the
glued/fixed construction the drone vibration environment wants.

## 2. Weight (parametric model, lid+base 4 mm, wall to envelope)

| design | Al 6061 | Mg AZ31B | Ti-6Al-4V | PA12 print | + mirrors/optics included |
|---|---|---|---|---|---|
| drone_20m Ø180 | **1 710 g** | 1 263 g | 2 549 g | 890 g | 16×20 g mirrors + 80 g optics inside all numbers |
| drone_14cm Ø141 | **1 231 g** | 920 g | 1 814 g | 661 g | 12 mirrors |
| drone_29m Ø183 | **1 661 g** | 1 204 g | 2 519 g | 821 g | 12 mirrors |

Notes: these are solid-wall numbers; Fusion-360 shelling/pocketing
typically takes 25–35 % out of the ring and lids (target ≈ 1.1–1.3 kg for
the Ø180 Al cell, ≈ 0.9 kg for Ø141) — well inside a DJI M300/M350-class
payload (2.7 kg). Magnesium saves ~26 % over Al at similar stiffness but
complicates sealing/corrosion; titanium buys thermal window, not mass.
The empty-shell comparison with Empa's 198 g bare ring is not
apples-to-apples — theirs is a bare open ring without lids, windows,
mirrors or ports.

## 3. Vibration (analytic modes + strategy; FEA handoff ready)

First mode of the lid (edge-clamped plate — the softest structural member
of a lid-and-ring build):

| material | drone_20m Ø180 | drone_14cm Ø141 |
|---|---|---|
| Al 6061 | **1 237 Hz** | 2 026 Hz |
| Ti-6Al-4V | 1 241 Hz | 2 033 Hz |
| PA12 | **327 Hz** | 535 Hz |
| PLA | 411 Hz | 674 Hz |
| tough resin | 377 Hz | 618 Hz |

Multirotor excitation is broadband ~60–700 Hz (rotor/blade-pass harmonics
+ frame resonances) at ~1.5–3 g RMS operational levels. **Aluminium lids
sit 2–20× above the excitation band; every printed polymer variant has
its first mode inside it** — a second, independent disqualifier for the
flying polymer cell. Strategy per the flight-proven Empa result: bond or
screw the mirrors rigidly (epoxy-bonded optics qualify to 20–40 g
MIL-STD-810 shock, an order of magnitude above the drone environment) and
isolate the *whole cell* on rubber dampers from the airframe — rigid
inside, damped outside; they saw significant optical noise rigid-mounted
and no measurable effect on dampers. FEA to confirm ring modes and
damper selection runs directly on the shipped STEP in Fusion 360
(simulation workspace, modal + 3 g random-vibe) — flagged for the team
("ask others also to do this analysis").

## 4. Thermal + environment (from the measured Al closure windows)

Ring closure windows scaled by CTE from the measured Al values
(drone_20m ±26 K):

| material | CTE [ppm/K] | drone_20m window | notes |
|---|---|---|---|
| Invar 36 | 1.2 | ±511 K (never limits) | heavy; use only as a ring insert if extreme range needed |
| Ti-6Al-4V | 8.6 | ±71 K | expensive middle ground |
| **Al 6061** | 23.6 | **±26 K** | fine for drone ops with a trim heater |
| PA12 | ~109 | ±6 K + 108 µm moisture swing | fails outdoors |
| PLA/resin | 68–75 | ±8–9 K + creep | fails outdoors |

The compact Ø141 design's Al window is ±8 K → give it the ring trim
heater (already the standard alignment actuator) or a Ti/invar-insert
ring if it must free-run over wide ambient swings.

## 5. Cost reality check

One-off: CNC Al 6061 at standard tolerance costs the *same class* as a
good polymer print at this size ($250–600 US, ~half offshore, vs $80–250
MJF/SLA) — and precision CNC ($600–1200) is the only route that carries
the dense 204-chord designs. Injection molding ($8–10 k tooling,
break-even ≥ ~400 parts) only enters at production quantities, where a
molded *body* + machined seat inserts + the sparse-pattern design is the
plausible low-cost product architecture. So the honest version of the
"$200 cell" vision: **$200 buys the 144-chord sparse design in a hybrid
printed-body/machined-seat build as an indoor instrument with one
alignment; the drone instrument is a $250–1200 CNC aluminium part either
way — and at one-off quantities CNC costs no more than printing.**

Sources: process tolerances Protolabs/Hubs published specs; ISO 2768-2
flatness classes; CTE/moisture EOS PA2200 + engineering handbooks; FDM
porosity + SLA/PEEK outgassing studies (Diamond Light Source, J. Vac.
studies); printed MPC literature (Anal. Chem. 2020; Sens. Act. B 2025);
Empa drone cell AMT 13, 4715 (2020); vibration norms ArduPilot + ISMA
2016 multirotor study; bonded-optics shock quals (SPIE/Hysol EA 9313);
cost benchmarks Xometry/Protolabs/Formlabs public figures. Our MC:
`mech_materials.py` with the platform's exact tracer.
