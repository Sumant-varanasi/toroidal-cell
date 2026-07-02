# Engineering investigations -- drone TMPC headline designs

## 1. ROC-error compensation (assembly rule)

Same-lot ROC error applied to every mirror; the machined ring radius is re-trimmed (launch untouched). Feasibility means the FULL check matrix passes again.

| design | ROC error | ring trim dR_ring | feasible | exit miss | OPL | T |
|---|---|---|---|---|---|---|
| drone_20m | -1.0 % | -0.720 mm | PASS | 0.012 mm | 20.18 m | 11.5 % |
| drone_20m | -0.5 % | -0.360 mm | PASS | 0.006 mm | 20.28 m | 11.5 % |
| drone_20m | +0.0 % | -0.000 mm | PASS | 0.000 mm | 20.38 m | 11.5 % |
| drone_20m | +0.5 % | +0.360 mm | PASS | 0.006 mm | 20.48 m | 11.5 % |
| drone_20m | +1.0 % | +0.720 mm | PASS | 0.012 mm | 20.58 m | 11.5 % |
| drone_25m | -1.0 % | -0.720 mm | PASS | 0.023 mm | 24.53 m | 7.0 % |
| drone_25m | -0.5 % | -0.360 mm | PASS | 0.012 mm | 24.65 m | 7.1 % |
| drone_25m | +0.0 % | -0.000 mm | PASS | 0.000 mm | 24.77 m | 7.1 % |
| drone_25m | +0.5 % | +0.360 mm | PASS | 0.012 mm | 24.90 m | 7.1 % |
| drone_25m | +1.0 % | +0.720 mm | PASS | 0.023 mm | 25.02 m | 7.0 % |
| drone_16cm | -1.0 % | -0.620 mm | PASS | 0.122 mm | 20.43 m | 5.6 % |
| drone_16cm | -0.5 % | -0.310 mm | PASS | 0.061 mm | 20.54 m | 7.3 % |
| drone_16cm | +0.0 % | -0.000 mm | PASS | 0.000 mm | 20.64 m | 7.9 % |
| drone_16cm | +0.5 % | +0.310 mm | PASS | 0.061 mm | 20.75 m | 7.3 % |
| drone_16cm | +1.0 % | +0.620 mm | PASS | 0.122 mm | 20.85 m | 5.7 % |

Assembly procedure: measure the delivered mirrors' actual ROC (autocollimator or interferometer), then machine the ring to the trimmed R_ring from this table (interpolate linearly); final closure is walked in with the ring-temperature / shim trim.

## 2. Thermal operating window (launch frozen)

| design | aluminium ring | invar ring |
|---|---|---|
| drone_20m | -26..+26 K | -30..+30 K |
| drone_25m | -20..+20 K | -30..+30 K |
| drone_16cm | -8..+8 K | -30..+30 K |

Window = delta-T range (from the alignment temperature) where every check still passes with no re-alignment. Outside it the exit spot walks off the hole; a lab-grade 5 K cabin/enclosure or an invar ring both work -- or actively trim the ring temperature, which doubles as the closure fine-tuning knob.

## 3. Beam-quality robustness

| design | M2=1.0 | 1.05 | 1.1 | 1.2 | 1.3 |
|---|---|---|---|---|---|
| drone_20m | PASS | PASS | PASS | PASS | PASS |
| drone_25m | PASS | PASS | PASS | PASS | PASS |
| drone_16cm | PASS | PASS | PASS | PASS | PASS |

(FAIL cells show the spot-separation margin; the fix is a slightly larger launch amplitude at design time.)
