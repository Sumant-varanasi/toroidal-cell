# As-built spec -- class D190: 20.38 m in a 180 mm envelope

16 x Thorlabs **CM254-150-M01** (1" protected-gold concave, ROC 300 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **72.154 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 16, every 22.50 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 17 mm |
| assembly envelope | 180 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.28 L |
| est. mass (mirrors + Al ring) | ~789 g |
| optics cost | 16 x ~$74 = ~$1184 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +72.154 |   +0.000 |    0.00 |  180.00 |
| M1 |  +66.662 |  +27.612 |   22.50 |  202.50 |
| M2 |  +51.021 |  +51.021 |   45.00 |  225.00 |
| M3 |  +27.612 |  +66.662 |   67.50 |  247.50 |
| M4 |   +0.000 |  +72.154 |   90.00 |  270.00 |
| M5 |  -27.612 |  +66.662 |  112.50 |  292.50 |
| M6 |  -51.021 |  +51.021 |  135.00 |  315.00 |
| M7 |  -66.662 |  +27.612 |  157.50 |  337.50 |
| M8 |  -72.154 |   +0.000 |  180.00 |    0.00 |
| M9 |  -66.662 |  -27.612 |  202.50 |   22.50 |
| M10 |  -51.021 |  -51.021 |  225.00 |   45.00 |
| M11 |  -27.612 |  -66.662 |  247.50 |   67.50 |
| M12 |   -0.000 |  -72.154 |  270.00 |   90.00 |
| M13 |  +27.612 |  -66.662 |  292.50 |  112.50 |
| M14 |  +51.021 |  -51.021 |  315.00 |  135.00 |
| M15 |  +66.662 |  -27.612 |  337.50 |  157.50 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.28) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.297 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.249 mm, located 76.5 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.33 mm max) |
| launch tilt, in-plane | +29.63 mrad from the M0->M7 chord |
| launch tilt, out-of-plane | +28.24 mrad |
| launch height offset | -0.28 mm |
| exit beam | back through the same hole, 157.5 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **20.381 m** |
| chords | 144 legs, mean 141.54 mm (min 139.54, max 143.23) |
| reflections | 143 (R^143 = 11.52 %) |
| spots per mirror | 9 |
| AOI | mean 11.30 deg, max 13.03 deg |
| beam radius in cell | 0.27 - 0.33 mm |
| throughput @ R = 0.985 | **11.52 %** = 100.00 % (hole in+out) x 11.52 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^143  (R = 0.984 -> 9.96 %, R = 0.97 -> 1.28 %) |
| stability | m_tan = +0.519, m_sag = +0.538 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 19.5 m | 20.38 m | PASS |
| intermediate spots clear hole | +1.72 mm | PASS |
| beam edge inside clear aperture | +4.17 mm | PASS |
| spot separation (fringe safety) | +0.51 mm beyond touching (min sep 1.12 mm) | PASS |
| per-plane stability | tan +0.519 / sag +0.538 | PASS |
| envelope | 180 <= 190 mm | PASS |
| mirror packing web | 2.75 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.28)#0  (+3.16,-1.21)#16  (-5.30,+2.77)#32  (+4.75,-3.71)#48  (-1.68,+4.28)#64  (-1.94,-4.49)#80  (+4.39,+4.03)#96  (-5.09,-3.04)#112  (+3.64,+1.91)#128  (+0.00,-0.28)#144
- **M1**: (+3.86,+2.75)#7  (-5.28,-3.91)#23  (+4.18,+4.42)#39  (-0.72,-4.34)#55  (-2.93,+3.92)#71  (+4.89,-3.01)#87  (-4.76,+1.54)#103  (+2.75,-0.17)#119  (+0.91,-1.41)#135
- **M2**: (-5.05,+4.46)#14  (+3.43,-4.46)#30  (+0.25,+3.75)#46  (-3.78,-2.75)#62  (+5.21,+1.53)#78  (-4.27,+0.17)#94  (+1.72,-1.60)#110  (+1.81,+2.89)#126  (-4.87,-4.03)#142
- **M3**: (-4.63,-4.33)#5  (+2.52,+3.79)#21  (+1.19,-2.60)#37  (-4.48,+1.15)#53  (+5.31,+0.19)#69  (-3.63,-1.84)#85  (+0.62,+3.12)#101  (+2.68,-3.95)#117  (-5.17,+4.51)#133
- **M4**: (+1.49,-2.54)#12  (+2.08,+1.06)#28  (-4.98,+0.62)#44  (+5.21,-1.90)#60  (-2.86,+3.23)#76  (-0.50,-4.15)#92  (+3.48,+4.43)#108  (-5.27,-4.30)#124  (+4.55,+3.72)#140
- **M5**: (+0.38,+0.88)#3  (+2.90,+0.65)#19  (-5.26,-2.29)#35  (+4.90,+3.33)#51  (-1.98,-4.12)#67  (-1.59,+4.52)#83  (+4.19,-4.24)#99  (-5.17,+3.45)#115  (+3.90,-2.43)#131
- **M6**: (+3.64,-2.27)#10  (-5.31,+3.59)#26  (+4.39,-4.26)#42  (-1.04,+4.40)#58  (-2.61,-4.19)#74  (+4.75,+3.41)#90  (-4.89,-2.08)#106  (+3.06,+0.77)#122  (+0.61,+0.86)#138
- **M7**: (+4.27,+3.57)#1  (-5.15,-4.35)#17  (+3.70,+4.52)#33  (-0.07,-4.02)#49  (-3.51,+3.20)#65  (+5.13,-2.07)#81  (-4.45,+0.41)#97  (+2.08,+1.02)#113  (+1.51,-2.44)#129
- **M8**: (-4.79,+4.44)#8  (+2.84,-4.09)#24  (+0.88,+3.04)#40  (-4.27,-1.72)#56  (+5.30,+0.39)#72  (-3.86,+1.30)#88  (+0.99,-2.66)#104  (+2.40,+3.66)#120  (-5.10,-4.42)#136
- **M9**: (+1.84,+3.01)#15  (+1.79,-1.61)#31  (-4.84,-0.03)#47  (+5.27,+1.35)#63  (-3.13,-2.81)#79  (-0.13,+3.87)#95  (+3.22,-4.34)#111  (-5.26,+4.45)#127  (+4.72,-4.02)#143
- **M10**: (+0.75,-1.46)#6  (+2.64,-0.08)#22  (-5.19,+1.76)#38  (+5.02,-2.90)#54  (-2.29,+3.89)#70  (-1.23,-4.47)#86  (+3.97,+4.38)#102  (-5.22,-3.80)#118  (+4.14,+2.91)#134
- **M11**: (+3.40,+1.76)#13  (-5.32,-3.21)#29  (+4.58,+4.02)#45  (-1.36,-4.38)#61  (-2.28,+4.38)#77  (+4.58,-3.75)#93  (-5.00,+2.58)#109  (+3.36,-1.35)#125  (+0.31,-0.29)#141
- **M12**: (+4.07,-3.19)#4  (-5.23,+4.17)#20  (+3.94,-4.51)#36  (-0.40,+4.22)#52  (-3.23,-3.59)#68  (+5.02,+2.56)#84  (-4.61,-0.98)#100  (+2.42,-0.43)#116  (+1.21,+1.94)#132
- **M13**: (-4.93,-4.49)#11  (+3.14,+4.31)#27  (+0.57,-3.43)#43  (-4.04,+2.25)#59  (+5.27,-0.97)#75  (-4.07,-0.74)#91  (+1.36,+2.15)#107  (+2.11,-3.30)#123  (-4.99,+4.26)#139
- **M14**: (-4.46,+4.13)#2  (+2.19,-3.43)#18  (+1.50,+2.12)#34  (-4.67,-0.56)#50  (+5.30,-0.78)#66  (-3.39,+2.35)#82  (+0.25,-3.52)#98  (+2.96,+4.18)#114  (-5.23,-4.52)#130
- **M15**: (+1.13,+2.02)#9  (+2.37,-0.50)#25  (-5.10,-1.20)#41  (+5.13,+2.42)#57  (-2.58,-3.59)#73  (-0.87,+4.35)#89  (+3.73,-4.44)#105  (-5.25,+4.08)#121  (+4.35,-3.35)#137

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
