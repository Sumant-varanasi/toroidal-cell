# As-built spec -- class D150: 13.64 m in a 143 mm envelope

12 x Thorlabs **CM254-250-M01** (1" protected-gold concave, ROC 500 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **53.486 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 12, every 30.00 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 17 mm |
| assembly envelope | 143 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.15 L |
| est. mass (mirrors + Al ring) | ~612 g |
| optics cost | 12 x ~$74 = ~$888 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +53.486 |   +0.000 |    0.00 |  180.00 |
| M1 |  +46.320 |  +26.743 |   30.00 |  210.00 |
| M2 |  +26.743 |  +46.320 |   60.00 |  240.00 |
| M3 |   +0.000 |  +53.486 |   90.00 |  270.00 |
| M4 |  -26.743 |  +46.320 |  120.00 |  300.00 |
| M5 |  -46.320 |  +26.743 |  150.00 |  330.00 |
| M6 |  -53.486 |   +0.000 |  180.00 |    0.00 |
| M7 |  -46.320 |  -26.743 |  210.00 |   30.00 |
| M8 |  -26.743 |  -46.320 |  240.00 |   60.00 |
| M9 |   -0.000 |  -53.486 |  270.00 |   90.00 |
| M10 |  +26.743 |  -46.320 |  300.00 |  120.00 |
| M11 |  +46.320 |  -26.743 |  330.00 |  150.00 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.06) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.233 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 45.7 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.43 mm max) |
| launch tilt, in-plane | -30.13 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +27.29 mrad |
| launch height offset | -0.06 mm |
| exit beam | back through the same hole, 153.5 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **13.639 m** |
| chords | 132 legs, mean 103.33 mm (min 100.71, max 105.84) |
| reflections | 131 (R^131 = 13.81 %) |
| spots per mirror | 11 |
| AOI | mean 15.05 deg, max 16.76 deg |
| beam radius in cell | 0.22 - 0.43 mm |
| throughput @ R = 0.985 | **13.81 %** = 100.00 % (hole in+out) x 13.81 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^131  (R = 0.984 -> 12.09 %, R = 0.97 -> 1.85 %) |
| stability | m_tan = +0.786, m_sag = +0.800 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 12.0 m | 13.64 m | PASS |
| intermediate spots clear hole | +0.42 mm | PASS |
| beam edge inside clear aperture | +4.18 mm | PASS |
| spot separation (fringe safety) | +0.58 mm beyond touching (min sep 1.32 mm) | PASS |
| per-plane stability | tan +0.786 / sag +0.800 | PASS |
| envelope | 143 <= 150 mm | PASS |
| mirror packing web | 2.29 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.06)#0  (+5.14,+4.43)#12  (-1.49,+1.28)#24  (-4.70,-4.08)#36  (+2.79,-2.45)#48  (+3.96,+3.36)#60  (-3.96,+3.36)#72  (-2.79,-2.45)#84  (+4.70,-4.08)#96  (+1.49,+1.28)#108  (-5.14,+4.43)#120  (+0.00,-0.06)#132
- **M1**: (+0.97,-0.26)#5  (+4.92,-4.47)#17  (-2.41,-0.96)#29  (-4.20,+4.20)#41  (+3.57,+2.18)#53  (+3.24,-3.56)#65  (-4.53,-3.13)#77  (-1.92,+2.71)#89  (+5.03,+3.94)#101  (+0.51,-1.60)#113  (-5.18,-4.37)#125
- **M2**: (+1.91,+0.57)#10  (+4.52,+4.49)#22  (-3.25,+0.63)#34  (-3.56,-4.30)#46  (+4.21,-1.89)#58  (+2.41,+3.75)#70  (-4.93,+2.89)#82  (-0.98,-2.95)#94  (+5.18,-3.78)#106  (-0.49,+1.91)#118  (-5.03,+4.28)#130
- **M3**: (-4.70,+4.21)#3  (+2.78,-0.89)#15  (+3.95,-4.48)#27  (-3.96,-0.30)#39  (-2.78,+4.37)#51  (+4.71,+1.60)#63  (+1.48,-3.92)#75  (-5.15,-2.64)#87  (-0.01,+3.18)#99  (+5.15,+3.60)#111  (-1.47,-2.21)#123
- **M4**: (-4.20,-4.09)#8  (+3.56,+1.20)#20  (+3.23,+4.44)#32  (-4.53,-0.03)#44  (-1.91,-4.43)#56  (+5.04,-1.30)#68  (+0.50,+4.07)#80  (-5.19,+2.37)#92  (+0.96,-3.40)#104  (+4.92,-3.39)#116  (-2.40,+2.50)#128
- **M5**: (-3.24,+2.66)#1  (-3.55,+3.95)#13  (+4.21,-1.51)#25  (+2.40,-4.39)#37  (-4.94,+0.35)#49  (-0.97,+4.46)#61  (+5.20,+0.99)#73  (-0.49,-4.20)#85  (-5.04,-2.09)#97  (+1.90,+3.60)#109  (+4.52,+3.17)#121
- **M6**: (-3.95,-2.93)#6  (-2.77,-3.78)#18  (+4.71,+1.80)#30  (+1.47,+4.30)#42  (-5.16,-0.67)#54  (+0.00,-4.47)#66  (+5.16,-0.67)#78  (-1.47,+4.30)#90  (-4.71,+1.80)#102  (+2.77,-3.78)#114  (+3.95,-2.93)#126
- **M7**: (-4.52,+3.17)#11  (-1.90,+3.60)#23  (+5.04,-2.09)#35  (+0.49,-4.20)#47  (-5.20,+0.99)#59  (+0.97,+4.46)#71  (+4.94,+0.35)#83  (-2.40,-4.39)#95  (-4.21,-1.51)#107  (+3.55,+3.95)#119  (+3.24,+2.66)#131
- **M8**: (+2.40,+2.50)#4  (-4.92,-3.39)#16  (-0.96,-3.40)#28  (+5.19,+2.37)#40  (-0.50,+4.07)#52  (-5.04,-1.30)#64  (+1.91,-4.43)#76  (+4.53,-0.03)#88  (-3.23,+4.44)#100  (-3.56,+1.20)#112  (+4.20,-4.09)#124
- **M9**: (+1.47,-2.21)#9  (-5.15,+3.60)#21  (+0.01,+3.18)#33  (+5.15,-2.64)#45  (-1.48,-3.92)#57  (-4.71,+1.60)#69  (+2.78,+4.37)#81  (+3.96,-0.30)#93  (-3.95,-4.48)#105  (-2.78,-0.89)#117  (+4.70,+4.21)#129
- **M10**: (+5.03,+4.28)#2  (+0.49,+1.91)#14  (-5.18,-3.78)#26  (+0.98,-2.95)#38  (+4.93,+2.89)#50  (-2.41,+3.75)#62  (-4.21,-1.89)#74  (+3.56,-4.30)#86  (+3.25,+0.63)#98  (-4.52,+4.49)#110  (-1.91,+0.57)#122
- **M11**: (+5.18,-4.37)#7  (-0.51,-1.60)#19  (-5.03,+3.94)#31  (+1.92,+2.71)#43  (+4.53,-3.13)#55  (-3.24,-3.56)#67  (-3.57,+2.18)#79  (+4.20,+4.20)#91  (+2.41,-0.96)#103  (-4.92,-4.47)#115  (-0.97,-0.26)#127

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
