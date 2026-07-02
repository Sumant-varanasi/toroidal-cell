# As-built spec -- class D170: 16.60 m in a 160 mm envelope

13 x Thorlabs **CM254-150-M01** (1" protected-gold concave, ROC 300 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **62.087 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 13, every 27.69 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 21 mm |
| assembly envelope | 160 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.25 L |
| est. mass (mirrors + Al ring) | ~676 g |
| optics cost | 13 x ~$74 = ~$962 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +62.087 |   +0.000 |    0.00 |  180.00 |
| M1 |  +54.975 |  +28.853 |   27.69 |  207.69 |
| M2 |  +35.269 |  +51.096 |   55.38 |  235.38 |
| M3 |   +7.484 |  +61.634 |   83.08 |  263.08 |
| M4 |  -22.016 |  +58.052 |  110.77 |  290.77 |
| M5 |  -46.473 |  +41.171 |  138.46 |  318.46 |
| M6 |  -60.283 |  +14.858 |  166.15 |  346.15 |
| M7 |  -60.283 |  -14.858 |  193.85 |   13.85 |
| M8 |  -46.473 |  -41.171 |  221.54 |   41.54 |
| M9 |  -22.016 |  -58.052 |  249.23 |   69.23 |
| M10 |   +7.484 |  -61.634 |  276.92 |   96.92 |
| M11 |  +35.269 |  -51.096 |  304.62 |  124.62 |
| M12 |  +54.975 |  -28.853 |  332.31 |  152.31 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.11) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.297 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.297 mm, located 0.0 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.38 mm max) |
| launch tilt, in-plane | -31.50 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +44.62 mrad |
| launch height offset | -0.11 mm |
| exit beam | back through the same hole, 141.7 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **16.603 m** |
| chords | 143 legs, mean 116.10 mm (min 112.96, max 119.08) |
| reflections | 142 (R^142 = 11.69 %) |
| spots per mirror | 11 |
| AOI | mean 20.84 deg, max 22.59 deg |
| beam radius in cell | 0.22 - 0.38 mm |
| throughput @ R = 0.985 | **11.69 %** = 100.00 % (hole in+out) x 11.69 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^142  (R = 0.984 -> 10.12 %, R = 0.97 -> 1.32 %) |
| stability | m_tan = +0.586, m_sag = +0.638 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 16.0 m | 16.60 m | PASS |
| intermediate spots clear hole | +2.33 mm | PASS |
| beam edge inside clear aperture | +3.43 mm | PASS |
| spot separation (fringe safety) | +0.40 mm beyond touching (min sep 1.00 mm) | PASS |
| per-plane stability | tan +0.586 / sag +0.638 | PASS |
| envelope | 160 <= 170 mm | PASS |
| mirror packing web | 4.32 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.11)#0  (+1.38,-5.75)#13  (-2.48,-4.67)#26  (+3.65,+1.97)#39  (-4.18,+6.18)#52  (+4.66,+3.18)#65  (-4.65,-3.37)#78  (+4.18,-6.14)#91  (-3.65,-1.76)#104  (+2.47,+4.81)#117  (-1.37,+5.66)#130  (+0.00,-0.11)#143
- **M1**: (+4.41,+4.08)#8  (-4.00,-2.41)#21  (+2.93,-6.22)#34  (-1.98,-2.74)#47  (+0.62,+4.01)#60  (+0.74,+6.03)#73  (-1.94,+1.02)#86  (+3.21,-5.27)#99  (-3.90,-5.34)#112  (+4.57,+0.92)#125  (-4.67,+5.93)#138
- **M2**: (-1.35,+3.08)#3  (+2.70,+6.22)#16  (-3.54,+2.12)#29  (+4.38,-4.61)#42  (-4.63,-5.85)#55  (+4.60,-0.18)#68  (-4.28,+5.51)#81  (+3.36,+4.85)#94  (-2.53,-1.40)#107  (+1.18,-6.10)#120  (+0.10,-3.63)#133
- **M3**: (+3.77,-1.30)#11  (-3.03,+4.92)#24  (+1.72,+5.47)#37  (-0.53,-0.37)#50  (-0.77,-5.79)#63  (+2.15,-4.43)#76  (-3.08,+2.05)#89  (+4.10,+6.25)#102  (-4.52,+3.15)#115  (+4.70,-3.80)#128  (-4.50,-6.15)#141
- **M4**: (-2.59,-5.30)#6  (+3.75,-5.11)#19  (-4.28,+0.96)#32  (+4.68,+6.08)#45  (-4.66,+4.06)#58  (+4.12,-2.85)#71  (-3.49,-6.26)#84  (+2.26,-2.37)#97  (-1.16,+4.21)#110  (-0.21,+5.91)#123  (+1.58,+0.67)#136
- **M5**: (-3.89,+4.82)#1  (+2.80,-1.79)#14  (-1.77,-6.18)#27  (+0.37,-3.37)#40  (+0.97,+3.39)#53  (-2.11,+6.16)#66  (+3.35,+1.70)#79  (-3.97,-4.63)#92  (+4.59,-5.65)#105  (-4.70,-0.15)#118  (+4.37,+5.71)#131
- **M6**: (-3.64,+6.22)#9  (+4.44,+2.70)#22  (-4.64,-3.82)#35  (+4.53,-6.02)#48  (-4.22,-1.24)#61  (+3.26,+5.15)#74  (-2.35,+5.42)#87  (+0.99,-0.68)#100  (+0.33,-5.94)#113  (-1.58,-4.27)#126  (+2.89,+2.47)#139
- **M7**: (-2.89,-2.26)#4  (+1.58,+4.43)#17  (-0.32,+5.86)#30  (-0.99,+0.46)#43  (+2.35,-5.53)#56  (-3.26,-5.03)#69  (+4.22,+1.45)#82  (-4.53,+6.08)#95  (+4.64,+3.64)#108  (-4.44,-2.90)#121  (+3.63,-6.21)#134
- **M8**: (-4.37,-5.62)#12  (+4.70,+0.37)#25  (-4.59,+5.74)#38  (+3.97,+4.48)#51  (-3.35,-1.91)#64  (+2.10,-6.19)#77  (-0.96,-3.20)#90  (-0.37,+3.56)#103  (+1.77,+6.15)#116  (-2.80,+1.58)#129  (+3.90,-4.96)#142
- **M9**: (-1.57,-0.89)#7  (+0.21,-5.97)#20  (+1.16,-4.04)#33  (-2.26,+2.58)#46  (+3.49,+6.26)#59  (-4.12,+2.65)#72  (+4.66,-4.22)#85  (-4.68,-6.02)#98  (+4.28,-0.74)#111  (-3.75,+5.23)#124  (+2.59,+5.18)#137
- **M10**: (+4.50,+6.19)#2  (-4.70,+3.62)#15  (+4.51,-3.34)#28  (-4.10,-6.23)#41  (+3.08,-1.84)#54  (-2.15,+4.58)#67  (+0.77,+5.71)#80  (+0.54,+0.15)#93  (-1.72,-5.57)#106  (+3.03,-4.78)#119  (-3.77,+1.51)#132
- **M11**: (-0.10,+3.81)#10  (-1.18,+6.06)#23  (+2.53,+1.18)#36  (-3.36,-4.98)#49  (+4.28,-5.40)#62  (-4.60,+0.41)#75  (+4.63,+5.92)#88  (-4.38,+4.46)#101  (+3.54,-2.33)#114  (-2.70,-6.24)#127  (+1.35,-2.88)#140
- **M12**: (+4.67,-5.86)#5  (-4.57,-0.70)#18  (+3.90,+5.46)#31  (-3.21,+5.14)#44  (+1.94,-1.24)#57  (-0.74,-6.08)#70  (-0.62,-3.84)#83  (+1.98,+2.94)#96  (-2.94,+6.22)#109  (+4.00,+2.21)#122  (-4.41,-4.24)#135

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
