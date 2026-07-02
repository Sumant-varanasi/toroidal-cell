# As-built spec -- class D180: 20.34 m in a 171 mm envelope

12 x Thorlabs **CM254-075-M01** (1" protected-gold concave, ROC 150 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **67.489 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 12, every 30.00 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 23 mm |
| assembly envelope | 171 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.33 L |
| est. mass (mirrors + Al ring) | ~685 g |
| optics cost | 12 x ~$74 = ~$888 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +67.489 |   +0.000 |    0.00 |  180.00 |
| M1 |  +58.447 |  +33.745 |   30.00 |  210.00 |
| M2 |  +33.745 |  +58.447 |   60.00 |  240.00 |
| M3 |   +0.000 |  +67.489 |   90.00 |  270.00 |
| M4 |  -33.745 |  +58.447 |  120.00 |  300.00 |
| M5 |  -58.447 |  +33.745 |  150.00 |  330.00 |
| M6 |  -67.489 |   +0.000 |  180.00 |    0.00 |
| M7 |  -58.447 |  -33.745 |  210.00 |   30.00 |
| M8 |  -33.745 |  -58.447 |  240.00 |   60.00 |
| M9 |   -0.000 |  -67.489 |  270.00 |   90.00 |
| M10 |  +33.745 |  -58.447 |  300.00 |  120.00 |
| M11 |  +58.447 |  -33.745 |  330.00 |  150.00 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.03) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.236 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 47.6 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.31 mm max) |
| launch tilt, in-plane | -39.13 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +56.40 mrad |
| launch height offset | -0.03 mm |
| exit beam | back through the same hole, 149.4 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **20.339 m** |
| chords | 156 legs, mean 130.38 mm (min 128.09, max 132.50) |
| reflections | 155 (R^155 = 9.61 %) |
| spots per mirror | 13 |
| AOI | mean 15.15 deg, max 17.49 deg |
| beam radius in cell | 0.23 - 0.31 mm |
| throughput @ R = 0.985 | **9.61 %** = 100.00 % (hole in+out) x 9.61 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^155  (R = 0.984 -> 8.21 %, R = 0.97 -> 0.89 %) |
| stability | m_tan = +0.099, m_sag = +0.161 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 18.0 m | 20.34 m | PASS |
| intermediate spots clear hole | +0.56 mm | PASS |
| beam edge inside clear aperture | +2.14 mm | PASS |
| spot separation (fringe safety) | +0.36 mm beyond touching (min sep 0.90 mm) | PASS |
| per-plane stability | tan +0.099 / sag +0.161 | PASS |
| envelope | 171 <= 180 mm | PASS |
| mirror packing web | 9.53 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.03)#0  (-4.90,-6.89)#12  (-3.58,+4.76)#24  (+2.53,+3.27)#36  (+5.21,-7.29)#48  (+1.27,+1.81)#60  (-4.32,+6.08)#72  (-4.40,-5.94)#84  (+1.31,-1.66)#96  (+5.23,+7.24)#108  (+2.46,-3.48)#120  (-3.50,-4.90)#132  (-4.96,+6.79)#144  (-0.00,-0.03)#156
- **M1**: (-4.58,+5.12)#5  (+0.69,-6.66)#17  (+5.20,-0.14)#29  (+2.92,+6.95)#41  (-3.13,-4.64)#53  (-5.08,-3.75)#65  (-0.55,+7.13)#77  (+4.74,-1.62)#89  (+3.91,-6.17)#101  (-2.00,+5.88)#113  (-5.30,+2.13)#125  (-1.75,-7.21)#137  (+4.00,+3.25)#149
- **M2**: (+4.44,+7.26)#10  (+4.24,-2.98)#22  (-1.46,-5.30)#34  (-5.28,+6.59)#46  (-2.28,+0.63)#58  (+3.68,-6.93)#70  (+4.85,+4.51)#82  (-0.20,+3.91)#94  (-5.00,-7.18)#106  (-3.39,+1.09)#118  (+2.70,+6.21)#130  (+5.18,-5.77)#142  (+1.08,-2.29)#154
- **M3**: (+5.07,-6.44)#3  (+0.30,+5.53)#15  (-4.83,+2.67)#27  (-3.71,-7.26)#39  (+2.14,+2.66)#51  (+5.32,+5.39)#63  (+1.56,-6.53)#75  (-4.20,-0.93)#87  (-4.47,+7.09)#99  (+0.89,-4.16)#111  (+5.27,-4.03)#123  (+2.72,+7.15)#135  (-3.30,-0.87)#147
- **M4**: (-3.82,-7.05)#8  (-4.83,+0.49)#20  (+0.48,+6.51)#32  (+5.03,-5.38)#44  (+3.22,-2.82)#56  (-2.82,+7.34)#68  (-5.25,-2.23)#80  (-0.77,-5.60)#92  (+4.51,+6.39)#104  (+4.14,+1.09)#116  (-1.66,-7.20)#128  (-5.35,+3.85)#140  (-2.01,+4.38)#152
- **M5**: (-5.21,+7.24)#1  (-1.44,-3.60)#13  (+4.36,-4.49)#25  (+4.38,+7.00)#37  (-1.18,-0.31)#49  (-5.18,-6.78)#61  (-2.63,+4.98)#73  (+3.50,+2.99)#85  (+4.95,-7.32)#97  (+0.10,+2.08)#109  (-4.87,+5.91)#121  (-3.64,-6.09)#133  (+2.41,-1.35)#145
- **M6**: (+2.93,+6.03)#6  (+5.19,+1.63)#18  (+0.64,-7.29)#30  (-4.74,+3.37)#42  (-3.90,+4.89)#54  (+1.82,-6.79)#66  (+5.33,+0.15)#78  (+1.89,+6.85)#90  (-4.00,-4.85)#102  (-4.66,-3.48)#114  (+0.62,+7.17)#126  (+5.15,-1.91)#138  (+3.03,-6.01)#150
- **M7**: (+2.38,+1.53)#11  (-3.56,+6.23)#23  (-4.95,-5.78)#35  (+0.15,-1.98)#47  (+4.96,+7.26)#59  (+3.43,-3.23)#71  (-2.54,-5.10)#83  (-5.25,+6.69)#95  (-1.17,+0.30)#107  (+4.43,-6.85)#119  (+4.28,+4.73)#131  (-1.36,+3.67)#143  (-5.24,-7.22)#155
- **M8**: (-2.10,-4.42)#4  (-5.26,-4.00)#16  (-1.69,+7.07)#28  (+4.11,-1.32)#40  (+4.60,-6.31)#52  (-0.87,+5.71)#64  (-5.19,+2.40)#76  (-2.80,-7.24)#88  (+3.15,+2.96)#100  (+5.12,+5.21)#112  (+0.41,-6.65)#124  (-4.82,-0.65)#136  (-3.76,+7.00)#148
- **M9**: (-3.27,+0.95)#9  (+2.76,-7.00)#21  (+5.18,+4.28)#33  (+0.98,+4.15)#45  (-4.52,-7.12)#57  (-4.21,+0.79)#69  (+1.63,+6.36)#81  (+5.23,-5.58)#93  (+2.20,-2.56)#105  (-3.72,+7.35)#117  (-4.89,-2.50)#129  (+0.40,-5.38)#141  (+4.98,+6.54)#153
- **M10**: (+1.02,+2.35)#2  (+5.27,+5.57)#14  (+2.63,-6.40)#26  (-3.37,-1.20)#38  (-4.96,+7.17)#50  (-0.28,-3.88)#62  (+4.93,-4.26)#74  (+3.64,+7.08)#86  (-2.30,-0.59)#98  (-5.21,-6.65)#110  (-1.55,+5.20)#122  (+4.30,+2.72)#134  (+4.44,-7.34)#146
- **M11**: (+4.08,-3.07)#7  (-1.77,+7.32)#19  (-5.35,-1.96)#31  (-1.90,-5.81)#43  (+3.82,+6.22)#55  (+4.78,+1.36)#67  (-0.52,-7.25)#79  (-5.17,+3.61)#91  (-3.03,+4.64)#103  (+2.86,-6.91)#115  (+5.20,+0.43)#127  (+0.76,+6.75)#139  (-4.67,-5.06)#151

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
