# Flight system plan — the integrated three-channel airborne sensor

*(Executes the paper's third next step at design level: architecture,
budgets and interfaces for flying CH₄ + NH₃ + H₂ on one cell.)*

## 1. Architecture

One cell serves all three gases (paper §4.4); the channels differ only
in source, detector and window. Two integration levels:

**Level A — per-mission channel (recommended first flight).** One DFB +
matching detector installed per mission; swap per the build-package
step 9 (collimator focus rescale + window if H₂). Zero optical
complexity added; the tri-gas claim is demonstrated across missions.

**Level B — switched tri-gas (single payload).** All three pigtailed
DFBs into a 1×3 PM fibre switch (or a 3→1 PM combiner accepting the
~3 dB tap loss), one reflective OAP collimator (achromatic across
1.5–2.1 µm — the reason it was specced), sapphire -D window resident,
and a two-detector pickoff behind M0: standard InGaAs and extended
InGaAs side by side with a short-focal lens each (the exit spot is
stationary; the two λ-bands split by a longpass dichroic at ~1.9 µm).
Time-multiplex channels at 1–10 s cadence. Note: NH₃ 1512 nm through
the -D sapphire window costs ~5–8 %/surface (out of AR band) — accept,
or flip to Level A for NH₃ campaigns.

## 2. Mass & power budget (Level B)

| subsystem | mass | power |
|---|---|---|
| cell, pocketed Al Ø185, mirrors, window | ~1.15 kg | — |
| dampers + mounting plate | 0.10 kg | — |
| 3× DFB (butterfly) + switch | 0.25 kg | 3–6 W (TECs) |
| drivers + DAQ/SBC (WMS demod on CPU/FPGA) | 0.30 kg | 4–6 W |
| detectors + TIAs | 0.05 kg | <1 W |
| ring heater duty (trim + anti-dew) | — | 2–5 W avg |
| **total** | **≈1.85 kg** | **≈10–17 W** |

Fits a DJI M300/M350-class payload (2.7 kg) with margin; Level A saves
~0.2 kg and ~4 W.

## 3. Mechanical & environmental interfaces

* Cell rigid on its plate; plate on four 40–60 Sh A isolators to the
  airframe (rigid inside, damped outside — the flight-proven
  configuration for this cell class). Keep the collimator boss and
  detector bracket on the *cell* side of the dampers.
* Thermal: ring PI loop holds setpoint ±0.1 K within a ±18 K ambient
  window (flagship); heater doubles as anti-dew. Below −10 °C ambient,
  add 10 mm foam around the ring (raises heater duty margin).
* Gas: flow-through via the two M5 ports with a 10 µm inlet mesh
  (2–10 s exchange pumped), or slotted-lid open-ring for ~25 ms
  in-flight exchange when plume mapping (accepting ambient dust — P8
  monitor active).
* EMI: DFB drivers and switch leads shielded; TIA at the detector.

## 4. Data pipeline

1. WMS at f ≈ 5–10 kHz, 2f demodulation per channel; line fit per 100 ms.
2. H₂ channel fits a Rautian profile (Dicke-narrowed line).
3. Continuous health metrics: fitted lot-R from DC transmission
   (contamination monitor), residual FFT watch at the chord FSR
   (0.034 cm⁻¹) as the fringe alarm, Allan tracker for drift.
4. Outputs: ppb CH₄ / ppb NH₃ / %LEL H₂ at 1–10 Hz + GPS tag.

## 5. Flight test sequence

1. Ground: full experimental_protocol P1–P8 on the integrated payload.
2. Hover test: P6 in situ (vibration-to-signal on the airframe), 10 min.
3. Transect over a controlled release (CH₄ cylinder + flow controller):
   verify plume detection vs release rate; repeat per channel.
4. Endurance: 20 min mission logging Allan behaviour airborne; the
   drift-vs-averaging knee defines the operational integration time.

## 6. Growth path

The active-tier controller (ring heater = slow loop, ±5 mrad launch
piezo = fast loop, quad detector behind the hole; ≈US$400–700) upgrades
the same airframe payload from 25.7 m to 38.6 m (uniform) or 51.7 m
(two-SKU) once the passive system is flight-proven; the 2-inch-mirror
family search (in progress) may raise the passive ceiling itself.
