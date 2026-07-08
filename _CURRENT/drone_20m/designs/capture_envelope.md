# Input-drift capture envelopes (the prof's acceptance model, executed)

*(Benoy 2026-07-08: "for an input spot pattern drift or angle drift in the
beam exits the [exit] hole with decent clearance it's good" + "Check this
for each of your designs." Tool: `capture_envelope.py`; data:
[capture_envelope.csv](capture_envelope.csv).)*

## What was measured

Per design and per launch degree of freedom (in-plane offset t, sagittal
offset z, tangential tilt, sagittal tilt), bisection to the largest drift
that still (a) completes the full path with no clipping, (b) keeps every
pre-exit pass clear of the coupling hole, and (c) exits with the whole
beam inside the hole rim (clearance ≥ 0). The capture envelope is the
per-axis box; P_cap = worst position axis, Θ_cap = worst angle axis.

## Results

| design | OPL (m) | P_cap (mm) | Θ_cap (mrad) | vs Al-flexure demand (0.07 mm / 0.20 mrad) | vs hybrid-plastic demand (0.17 mm / 0.55 mrad) |
|---|---|---|---|---|---|
| D190 25.7 m tri-gas | 25.7 | 0.499 | 10.1 | 7.1× / 51× | 2.9× / 18× |
| D160 27 m | 26.7 | 1.055 | 14.2 | 15× / 71× | 6.2× / 26× |
| D180 24 m H2 (2121.8 nm) | 23.8 | 0.411 | 6.0 | 5.9× / 30× | 2.4× / 11× |
| D180 15 m sparse | 15.3 | 1.034 | 18.8 | 15× / 94× | 6.1× / 34× |
| D130 9.1 m half-inch (0.8 mm hole) | 9.1 | 0.507 | 8.0 | 7.2× / 40× | 3.0× / 15× |
| D190 19 m two-inch | 19.0 | 1.137 | 13.2 | 16× / 66× | 6.7× / 24× |
| D190 29 m ceiling | 29.0 | 0.473 | 3.0 | 6.8× / 15× | 2.8× / 5.5× |
| D150 20.7 m flight | 20.7 | 0.410 | 4.2 | 5.9× / 21× | 2.4× / 7.6× |
| D180 22 m | 22.3 | 0.366 | 6.5 | 5.2× / 32× | 2.2× / 12× |

Demand = alignment-residual regime + drone operational-drift vector from
the prof's framework, conservative arithmetic sum: Al isostatic flexure
uses the easy regime (0.02 mm / 0.05 mrad) + drone Al-flexure drift
(0.05 mm / 0.15 mrad); hybrid plastic body + Al mirror cartridge uses the
medium regime (0.05 / 0.15) + hybrid drone drift (0.12 / 0.40).

## Findings

1. **Every menu design passes both architectures**, minimum margins 2.2×
   in position (D180_22m vs hybrid) and 5.5× in angle (29 m ceiling vs
   hybrid). Even the *hard* alignment regime plus hybrid drift
   (0.24 mm / 0.80 mrad summed) is inside every envelope.
2. **Angle capture is the architecture's quiet superpower** — 3–19 mrad,
   1–2 orders above the demand. The re-entrant ring tolerates launch
   angle drift far better than launch position drift because tilt
   deforms the Lissajous pattern slowly while position drift translates
   it toward the hole rim roughly 1:1.
3. **Position capture tracks exit-hole clearance**, as the acceptance
   model predicts: the sparse/2-inch designs (largest hole margins)
   capture >1 mm; the 29 m ceiling design and the walk-tight 22 m sit
   at 0.37–0.47 mm — still 5–7× the flexure demand.
4. The tightest angle budget in the menu is the 29 m ceiling design
   (3.0 mrad) — consistent with its role as the passive-build boundary.
5. Capture ≫ residual+drift for every design means: **construction error
   within the capture box is fully recoverable by one alignment session,
   and post-alignment drone drift never walks the exit out of the hole**
   — the two claims the prof's framework asks a paper to state
   separately.
