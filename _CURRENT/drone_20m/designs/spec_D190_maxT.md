# As-built spec -- class D190: 20.38 m in a 180 mm envelope

16 x Thorlabs **CM254-150-M01** (1" protected-gold concave, ROC 300 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **72.155 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 16, every 22.50 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 16 mm |
| assembly envelope | 180 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.26 L |
| est. mass (mirrors + Al ring) | ~789 g |
| optics cost | 16 x ~$74 = ~$1184 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +72.155 |   +0.000 |    0.00 |  180.00 |
| M1 |  +66.663 |  +27.613 |   22.50 |  202.50 |
| M2 |  +51.022 |  +51.022 |   45.00 |  225.00 |
| M3 |  +27.613 |  +66.663 |   67.50 |  247.50 |
| M4 |   +0.000 |  +72.155 |   90.00 |  270.00 |
| M5 |  -27.613 |  +66.663 |  112.50 |  292.50 |
| M6 |  -51.022 |  +51.022 |  135.00 |  315.00 |
| M7 |  -66.663 |  +27.613 |  157.50 |  337.50 |
| M8 |  -72.155 |   +0.000 |  180.00 |    0.00 |
| M9 |  -66.663 |  -27.613 |  202.50 |   22.50 |
| M10 |  -51.022 |  -51.022 |  225.00 |   45.00 |
| M11 |  -27.613 |  -66.663 |  247.50 |   67.50 |
| M12 |   -0.000 |  -72.155 |  270.00 |   90.00 |
| M13 |  +27.613 |  -66.663 |  292.50 |  112.50 |
| M14 |  +51.022 |  -51.022 |  315.00 |  135.00 |
| M15 |  +66.663 |  -27.613 |  337.50 |  157.50 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, +0.27) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.365 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.326 mm, located 102.1 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.42 mm max) |
| launch tilt, in-plane | -30.95 mrad from the M0->M7 chord |
| launch tilt, out-of-plane | +21.67 mrad |
| launch height offset | +0.27 mm |
| exit beam | back through the same hole, 157.5 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **20.381 m** |
| chords | 144 legs, mean 141.54 mm (min 139.66, max 143.14) |
| reflections | 143 (R^143 = 11.52 %) |
| spots per mirror | 9 |
| AOI | mean 11.29 deg, max 12.93 deg |
| beam radius in cell | 0.23 - 0.42 mm |
| throughput @ R = 0.985 | **11.52 %** = 100.00 % (hole in+out) x 11.52 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^143  (R = 0.984 -> 9.96 %, R = 0.97 -> 1.28 %) |
| stability | m_tan = +0.519, m_sag = +0.537 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 19.5 m | 20.38 m | PASS |
| intermediate spots clear hole | +1.46 mm | PASS |
| beam edge inside clear aperture | +4.91 mm | PASS |
| spot separation (fringe safety) | +0.36 mm beyond touching (min sep 0.99 mm) | PASS |
| per-plane stability | tan +0.519 / sag +0.537 | PASS |
| envelope | 180 <= 190 mm | PASS |
| mirror packing web | 2.75 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,+0.27)#0  (-3.44,-1.60)#16  (+4.85,+2.54)#32  (-4.18,-3.34)#48  (+1.84,+3.71)#64  (+1.60,-3.53)#80  (-4.51,+3.04)#96  (+5.03,-2.25)#112  (-3.02,+0.97)#128  (+0.00,+0.27)#144
- **M1**: (-4.13,+2.78)#7  (+5.01,-3.39)#23  (-3.56,+3.67)#39  (+0.82,-3.58)#55  (+2.45,+2.94)#71  (-4.87,-1.97)#87  (+4.83,+0.95)#103  (-2.25,+0.45)#119  (-1.06,-1.70)#135
- **M2**: (+4.97,+3.73)#14  (-2.83,-3.44)#30  (-0.24,+2.89)#46  (+3.22,-1.91)#62  (-5.04,+0.61)#78  (+4.43,+0.51)#94  (-1.42,-1.79)#110  (-2.07,+2.86)#126  (+4.26,-3.43)#142
- **M3**: (+4.74,-3.50)#5  (-2.02,+2.71)#21  (-1.29,-1.74)#37  (+3.87,+0.58)#53  (-5.00,+0.83)#69  (+3.83,-1.89)#85  (-0.53,+2.85)#101  (-2.98,-3.57)#117  (+4.70,+3.70)#133
- **M4**: (-1.17,-1.57)#12  (-2.29,+0.32)#28  (+4.39,+0.85)#44  (-4.77,-2.14)#60  (+3.06,+2.99)#76  (+0.39,-3.50)#92  (-3.74,+3.72)#108  (+4.97,-3.42)#124  (-3.89,+2.61)#140
- **M5**: (-0.29,+0.20)#3  (-3.18,+1.14)#19  (+4.77,-2.16)#35  (-4.35,+3.12)#51  (+2.16,-3.62)#67  (+1.30,+3.61)#83  (-4.35,-3.30)#99  (+5.05,+2.62)#115  (-3.25,-1.42)#131
- **M6**: (-3.92,-2.43)#10  (+4.97,+3.15)#26  (-3.78,-3.62)#42  (+1.17,+3.69)#58  (+2.17,-3.19)#74  (-4.77,+2.37)#90  (+4.92,-1.41)#106  (-2.52,+0.03)#122  (-0.71,+1.24)#138
- **M7**: (-4.48,+3.33)#1  (+5.00,-3.68)#17  (-3.09,+3.58)#33  (+0.12,-3.17)#49  (+2.97,+2.29)#65  (-5.00,-1.09)#81  (+4.58,-0.02)#97  (-1.70,+1.36)#113  (-1.75,-2.51)#129
- **M8**: (+4.84,+3.64)#8  (-2.30,-3.00)#24  (-0.94,+2.16)#40  (+3.67,-1.04)#56  (-5.03,-0.36)#72  (+4.05,+1.45)#88  (-0.83,-2.54)#104  (-2.69,+3.39)#120  (+4.57,-3.67)#136
- **M9**: (-1.46,+1.98)#15  (-1.96,-0.81)#31  (+4.24,-0.38)#47  (-4.87,+1.73)#63  (+3.33,-2.67)#79  (+0.08,+3.34)#95  (-3.51,-3.73)#111  (+4.90,+3.58)#127  (-4.08,-2.92)#143
- **M10**: (-0.59,-0.67)#6  (-2.90,-0.66)#22  (+4.66,+1.75)#38  (-4.51,-2.84)#54  (+2.48,+3.47)#70  (+1.00,-3.64)#86  (-4.17,+3.50)#102  (+5.05,-2.94)#118  (-3.48,+1.85)#134
- **M11**: (-3.69,+2.03)#13  (+4.92,-2.87)#29  (-3.99,+3.51)#45  (+1.51,-3.73)#61  (+1.89,+3.39)#77  (-4.65,-2.73)#93  (+4.99,+1.85)#109  (-2.77,-0.50)#125  (-0.36,-0.76)#141
- **M12**: (-4.31,-3.09)#4  (+5.02,+3.56)#20  (-3.33,-3.65)#36  (+0.47,+3.41)#52  (+2.72,-2.64)#68  (-4.95,+1.54)#84  (+4.72,-0.47)#100  (-1.98,-0.91)#116  (-1.41,+2.12)#132
- **M13**: (+4.92,-3.72)#11  (-2.57,+3.25)#27  (-0.59,-2.55)#43  (+3.45,+1.49)#59  (-5.05,-0.13)#75  (+4.25,-0.99)#91  (-1.13,+2.18)#107  (-2.39,-3.15)#123  (+4.42,+3.58)#139
- **M14**: (+4.62,+3.30)#2  (-1.74,-2.36)#18  (-1.63,+1.29)#34  (+4.06,-0.10)#50  (-4.95,-1.30)#66  (+3.59,+2.30)#82  (-0.23,-3.12)#98  (-3.25,+3.68)#114  (+4.81,-3.67)#130
- **M15**: (-0.88,+1.13)#9  (-2.60,+0.17)#25  (+4.53,-1.31)#41  (-4.65,+2.51)#57  (+2.78,-3.26)#73  (+0.69,+3.60)#89  (-3.97,-3.64)#105  (+5.02,+3.21)#121  (-3.69,-2.24)#137

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
