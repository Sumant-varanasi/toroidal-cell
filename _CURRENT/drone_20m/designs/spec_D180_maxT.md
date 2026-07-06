# As-built spec -- class D180: 20.34 m in a 171 mm envelope

12 x Thorlabs **CM254-075-M01** (1" protected-gold concave, ROC 150 mm, CA radius 11.4 mm, R = 0.999 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **67.493 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 12, every 30.00 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 25 mm |
| assembly envelope | 171 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.36 L |
| est. mass (mirrors + Al ring) | ~685 g |
| optics cost | 12 x ~$74 = ~$888 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +67.493 |   +0.000 |    0.00 |  180.00 |
| M1 |  +58.451 |  +33.747 |   30.00 |  210.00 |
| M2 |  +33.747 |  +58.451 |   60.00 |  240.00 |
| M3 |   +0.000 |  +67.493 |   90.00 |  270.00 |
| M4 |  -33.747 |  +58.451 |  120.00 |  300.00 |
| M5 |  -58.451 |  +33.747 |  150.00 |  330.00 |
| M6 |  -67.493 |   +0.000 |  180.00 |    0.00 |
| M7 |  -58.451 |  -33.747 |  210.00 |   30.00 |
| M8 |  -33.747 |  -58.451 |  240.00 |   60.00 |
| M9 |   -0.000 |  -67.493 |  270.00 |   90.00 |
| M10 |  +33.747 |  -58.451 |  300.00 |  120.00 |
| M11 |  +58.451 |  -33.747 |  330.00 |  150.00 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.04) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.208 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 22.3 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.38 mm max) |
| launch tilt, in-plane | -47.03 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +62.56 mrad |
| launch height offset | -0.04 mm |
| exit beam | back through the same hole, 149.2 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **20.340 m** |
| chords | 156 legs, mean 130.39 mm (min 127.60, max 132.92) |
| reflections | 155 (R^155 = 85.63 %) |
| spots per mirror | 13 |
| AOI | mean 15.19 deg, max 18.00 deg |
| beam radius in cell | 0.19 - 0.38 mm |
| throughput @ R = 0.999 | **85.63 %** = 100.00 % (hole in+out) x 85.63 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^155  (R = 0.984 -> 8.21 %, R = 0.97 -> 0.89 %) |
| stability | m_tan = +0.099, m_sag = +0.161 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 18.0 m | 20.34 m | PASS |
| intermediate spots clear hole | +0.87 mm | PASS |
| beam edge inside clear aperture | +0.80 mm | PASS |
| spot separation (fringe safety) | +0.38 mm beyond touching (min sep 1.08 mm) | PASS |
| per-plane stability | tan +0.099 / sag +0.161 | PASS |
| envelope | 171 <= 180 mm | PASS |
| mirror packing web | 9.54 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.04)#0  (-5.90,-7.67)#12  (-4.33,+5.26)#24  (+3.06,+3.61)#36  (+6.26,-8.12)#48  (+1.54,+2.01)#60  (-5.21,+6.77)#72  (-5.31,-6.58)#84  (+1.59,-1.83)#96  (+6.29,+8.05)#108  (+2.98,-3.87)#120  (-4.22,-5.45)#132  (-5.97,+7.54)#144  (+0.00,-0.04)#156
- **M1**: (-5.51,+5.72)#5  (+0.82,-7.39)#17  (+6.28,-0.12)#29  (+3.52,+7.73)#41  (-3.77,-5.17)#53  (-6.13,-4.19)#65  (-0.67,+7.90)#77  (+5.72,-1.84)#89  (+4.71,-6.86)#101  (-2.40,+6.55)#113  (-6.39,+2.39)#125  (-2.11,-7.99)#137  (+4.82,+3.65)#149
- **M2**: (+5.35,+8.07)#10  (+5.12,-3.33)#22  (-1.77,-5.89)#34  (-6.36,+7.32)#46  (-2.75,+0.71)#58  (+4.43,-7.68)#70  (+5.85,+5.04)#82  (-0.25,+4.35)#94  (-6.02,-7.99)#106  (-4.10,+1.19)#118  (+3.26,+6.88)#130  (+6.23,-6.44)#142  (+1.30,-2.55)#154
- **M3**: (+6.10,-7.16)#3  (+0.37,+6.15)#15  (-5.84,+2.98)#27  (-4.47,-8.06)#39  (+2.57,+2.98)#51  (+6.41,+5.98)#63  (+1.88,-7.27)#75  (-5.07,-1.03)#87  (-5.37,+7.89)#99  (+1.06,-4.62)#111  (+6.35,-4.46)#123  (+3.28,+7.96)#135  (-3.99,-0.97)#147
- **M4**: (-4.59,-7.85)#8  (-5.82,+0.51)#20  (+0.59,+7.21)#32  (+6.05,-6.01)#44  (+3.89,-3.13)#56  (-3.39,+8.17)#68  (-6.33,-2.45)#80  (-0.92,-6.21)#92  (+5.43,+7.12)#104  (+5.00,+1.20)#116  (-2.01,-8.00)#128  (-6.45,+4.27)#140  (-2.42,+4.87)#152
- **M5**: (-6.27,+8.06)#1  (-1.75,-3.99)#13  (+5.27,-4.96)#25  (+5.27,+7.80)#37  (-1.42,-0.35)#49  (-6.24,-7.55)#61  (-3.18,+5.51)#73  (+4.23,+3.29)#85  (+5.95,-8.15)#97  (+0.12,+2.32)#109  (-5.87,+6.59)#121  (-4.39,-6.75)#133  (+2.92,-1.47)#145
- **M6**: (+3.53,+6.71)#6  (+6.27,+1.79)#18  (+0.77,-8.10)#30  (-5.71,+3.75)#42  (-4.69,+5.45)#54  (+2.19,-7.54)#66  (+6.43,+0.20)#78  (+2.27,+7.62)#90  (-4.82,-5.40)#102  (-5.61,-3.90)#114  (+0.74,+7.95)#126  (+6.21,-2.16)#138  (+3.65,-6.69)#150
- **M7**: (+2.88,+1.71)#11  (-4.30,+6.93)#23  (-5.97,-6.40)#35  (+0.18,-2.19)#47  (+5.96,+8.07)#59  (+4.15,-3.60)#71  (-3.07,-5.67)#83  (-6.32,+7.44)#95  (-1.41,+0.34)#107  (+5.33,-7.60)#119  (+5.16,+5.28)#131  (-1.65,+4.08)#143  (-6.31,-8.03)#155
- **M8**: (-2.53,-4.92)#4  (-6.34,-4.47)#16  (-2.04,+7.84)#28  (+4.96,-1.50)#40  (+5.54,-7.02)#52  (-1.04,+6.35)#64  (-6.27,+2.69)#76  (-3.37,-8.03)#88  (+3.79,+3.32)#100  (+6.17,+5.78)#112  (+0.50,-7.40)#124  (-5.81,-0.73)#136  (-4.52,+7.78)#148
- **M9**: (-3.95,+1.08)#9  (+3.32,-7.76)#21  (+6.25,+4.79)#33  (+1.17,+4.61)#45  (-5.44,-7.92)#57  (-5.09,+0.84)#69  (+1.97,+7.04)#81  (+6.30,-6.24)#93  (+2.66,-2.84)#105  (-4.48,+8.18)#117  (-5.90,-2.75)#129  (+0.49,-5.96)#141  (+6.00,+7.29)#153
- **M10**: (+1.23,+2.62)#2  (+6.34,+6.18)#14  (+3.17,-7.12)#26  (-4.08,-1.34)#38  (-5.97,+7.98)#50  (-0.35,-4.31)#62  (+5.95,-4.71)#74  (+4.38,+7.88)#86  (-2.77,-0.66)#98  (-6.27,-7.42)#110  (-1.88,+5.76)#122  (+5.19,+2.98)#134  (+5.35,-8.17)#146
- **M11**: (+4.92,-3.41)#7  (-2.13,+8.15)#19  (-6.45,-2.16)#31  (-2.28,-6.45)#43  (+4.59,+6.92)#55  (+5.78,+1.50)#67  (-0.63,-8.06)#79  (-6.23,+4.01)#91  (-3.65,+5.17)#103  (+3.44,-7.67)#115  (+6.28,+0.50)#127  (+0.91,+7.50)#139  (-5.63,-5.63)#151

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
