# Experimental verification protocol — measuring the paper's budgets

*(Executes the paper's second next step as a lab procedure: every
measurement has an expected value from the verified simulations and an
explicit pass band. Instruments assumed: the build-package bench, a
signal generator + lock-in (or DAQ with digital demod), calibrated gas
mixtures, a hot/cold chamber or lab HVAC authority of ±10 K, and a
shaker or the drone itself for the vibration step.)*

## P1 — Transmission vs photon budget

Method: power meter at collimator output (P₀) and at detector plane
(P₁), CH₄ laser, cell locked (build step 7). T_cell = P₁/P₀ ÷ chain
losses (window ×2 passes ≈ 0.99², collimator per datasheet).
**Expected:** T = R^(n−1): 83.9 % (flagship, n = 176) / 86.7 %
(standard, n = 144) at R = 0.999; the measured T yields the delivered
lot's R via R = T^(1/(n−1)) — record it; every other budget rescales
with it. **Pass:** within −5 % absolute of prediction with the fitted R
∈ [0.9975, 0.9995].

## P2 — Path-length verification

Method (either): (a) frequency-modulation phase delay — modulate the
laser at f_m = 5–20 MHz, measure RF phase between a reference detector
and the cell detector: Δφ = 2π f_m · OPL/c (25.72 m → 0.54° per MHz);
(b) ring-down-style time of flight with a fast pulse and >200 MHz
detector. **Expected:** 25.72 / 20.38 m. **Pass:** ±0.5 %.

## P3 — Fringe floor / noise-equivalent absorbance (the OD-noise claim)

Method: evacuated or N₂-flushed cell; sweep the laser over the working
window (≥1.5 cm⁻¹); record 30 min of spectra at 1 Hz; fit and remove a
3rd-order baseline per spectrum; compute (i) RMS residual absorbance at
1 s (NEA), (ii) Allan–Werle deviation of a fitted null concentration,
(iii) FFT of residuals in optical-frequency domain. **Expected:** NEA
class 2×10⁻⁵ (1σ, short-term) direct; ≤10⁻⁵ with WMS; Allan minimum
beyond 60 s. **Diagnostics designed in:** peaks in (iii) at
0.034–0.037 cm⁻¹ (flagship/standard chord FSR) indicate mirror-spot
scatter coupling — compare against the −34…−148 dB overlap budget;
1 cm⁻¹-scale ripple indicates window etalon (re-seat/tilt window);
0.4 cm⁻¹ ripple indicates collimator internal etalon. **Pass:** NEA ≤
1×10⁻⁴ direct at 1 s (paper's conservative LOD basis); target class
2×10⁻⁵.

## P4 — Polarization eigenaxis (paper §6.6)

Method: PM launch keyed sagittal; rotatable analyser + power meter on
the exit; measure transmitted power vs analyser angle at launch
polarization set 0° (sagittal) and 45°. **Expected:** sagittal launch →
extinction ratio ≥ 13 dB (purity ≥ 96.3–99.9 % depending on design);
45° launch → strongly elliptical output (ellipticity tens of degrees;
do not use). **Pass:** sagittal purity ≥ 95 %; record the full curve
for the paper's measured-vs-predicted figure.

## P5 — Thermal window and trim authority

Method: with the launch frozen, step ambient (or the ring heater) in
1 K increments; log transmission and exit-spot position. **Expected:**
transmission plateau over ±18 K (flagship) / ±26 K (standard) around
the lock point; ring-heater authority moves the closure peak by
1.7 µm/K equivalent. **Pass:** plateau ≥ ±10 K; peak recoverable by
heater across the full excursion.

## P6 — Vibration-to-signal (the "shaking" budget)

Method: mount the damped assembly on a shaker (or fly it); excite
60–700 Hz at 1.5–3 g RMS broadband; record transmission and retrieved
null concentration during excitation. **Expected:** transmission
modulation < a few %, dominated by launch-chain pointing; retrieved
concentration unaffected within the P3 noise (the flight-proven
precedent for this architecture class saw no effect on dampers).
**Pass:** no line-shaped artefacts; added white noise ≤ 2× quiescent;
any narrow spectral feature triggers a damper/lens iteration, not a
cell rebuild.

## P7 — Gas response (per channel)

CH₄: calibrated 2–100 ppm mixtures; expected sensitivity 3.8×10⁻⁵
absorbance per ppm·m → 129 ppb (1σ) at NEA 10⁻⁴, 20.4 m. NH₃ 1512.2 nm:
92 ppb basis; note wall adsorption — use PTFE lines, log step-response
time. H₂ 2121.8 nm: %-level mixtures in N₂; expected 0.17–0.31 %v at
NEA 10⁻⁴ (direct); fit with a Rautian/Galatry profile (the line is
Dicke-narrowed, FWHM ≈ 0.026–0.04 cm⁻¹ at 1 atm — a Voigt fit will bias
low); WMS target: tens of ppm. **Pass:** linearity R² ≥ 0.999 over one
decade; retrieved LODs within 2× of the basis values.

## P8 — Contamination self-monitor (open-flow mode)

Method: log P1's fitted R continuously during dusty/field operation.
**Expected:** ΔR per mirror of 10⁻⁴ reads as ≈2 % transmission change
at 204 chords — the cell is its own reflectometer. **Action level:** R
drop >5×10⁻⁴ → inspect/purge; heater a few K above dew point in humid
air.

Deliverables per cell: filled P1–P8 record, fitted lot R, measured NEA
+ Allan plot, polarization curve, thermal plateau — these are the
measured panels the paper's revision needs to move from
simulation-verified to demonstrated.
