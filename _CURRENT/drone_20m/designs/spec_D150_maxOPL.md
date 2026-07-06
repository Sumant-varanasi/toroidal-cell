# As-built spec -- class D150: 13.64 m in a 143 mm envelope

12 x Thorlabs **CM254-250-M01** (1" protected-gold concave, ROC 500 mm, CA radius 11.4 mm, R = 0.985 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **53.485 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
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
| M0 |  +53.485 |   +0.000 |    0.00 |  180.00 |
| M1 |  +46.319 |  +26.742 |   30.00 |  210.00 |
| M2 |  +26.742 |  +46.319 |   60.00 |  240.00 |
| M3 |   +0.000 |  +53.485 |   90.00 |  270.00 |
| M4 |  -26.742 |  +46.319 |  120.00 |  300.00 |
| M5 |  -46.319 |  +26.742 |  150.00 |  330.00 |
| M6 |  -53.485 |   +0.000 |  180.00 |    0.00 |
| M7 |  -46.319 |  -26.742 |  210.00 |   30.00 |
| M8 |  -26.742 |  -46.319 |  240.00 |   60.00 |
| M9 |   -0.000 |  -53.485 |  270.00 |   90.00 |
| M10 |  +26.742 |  -46.319 |  300.00 |  120.00 |
| M11 |  +46.319 |  -26.742 |  330.00 |  150.00 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.06) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.248 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 55.6 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.43 mm max) |
| launch tilt, in-plane | -31.63 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +27.55 mrad |
| launch height offset | -0.06 mm |
| exit beam | back through the same hole, 153.6 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **13.639 m** |
| chords | 132 legs, mean 103.32 mm (min 100.57, max 105.96) |
| reflections | 131 (R^131 = 13.81 %) |
| spots per mirror | 11 |
| AOI | mean 15.05 deg, max 16.85 deg |
| beam radius in cell | 0.22 - 0.43 mm |
| throughput @ R = 0.985 | **13.81 %** = 100.00 % (hole in+out) x 13.81 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^131  (R = 0.984 -> 12.09 %, R = 0.97 -> 1.85 %) |
| stability | m_tan = +0.786, m_sag = +0.800 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 12.0 m | 13.64 m | PASS |
| intermediate spots clear hole | +0.46 mm | PASS |
| beam edge inside clear aperture | +3.96 mm | PASS |
| spot separation (fringe safety) | +0.59 mm beyond touching (min sep 1.33 mm) | PASS |
| per-plane stability | tan +0.786 / sag +0.800 | PASS |
| envelope | 143 <= 150 mm | PASS |
| mirror packing web | 2.29 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.06)#0  (+5.40,+4.48)#12  (-1.56,+1.29)#24  (-4.94,-4.13)#36  (+2.93,-2.47)#48  (+4.16,+3.39)#60  (-4.16,+3.39)#72  (-2.93,-2.47)#84  (+4.94,-4.13)#96  (+1.56,+1.29)#108  (-5.40,+4.48)#120  (+0.00,-0.06)#132
- **M1**: (+1.02,-0.26)#5  (+5.17,-4.52)#17  (-2.53,-0.97)#29  (-4.41,+4.25)#41  (+3.74,+2.20)#53  (+3.41,-3.60)#65  (-4.76,-3.16)#77  (-2.02,+2.73)#89  (+5.28,+3.99)#101  (+0.53,-1.61)#113  (-5.44,-4.41)#125
- **M2**: (+2.01,+0.58)#10  (+4.74,+4.53)#22  (-3.41,+0.63)#34  (-3.73,-4.34)#46  (+4.42,-1.91)#58  (+2.53,+3.79)#70  (-5.18,+2.92)#82  (-1.03,-2.98)#94  (+5.44,-3.82)#106  (-0.52,+1.93)#118  (-5.28,+4.33)#130
- **M3**: (-4.93,+4.26)#3  (+2.92,-0.90)#15  (+4.15,-4.53)#27  (-4.16,-0.30)#39  (-2.92,+4.42)#51  (+4.95,+1.62)#63  (+1.56,-3.96)#75  (-5.41,-2.67)#87  (-0.01,+3.22)#99  (+5.41,+3.64)#111  (-1.55,-2.23)#123
- **M4**: (-4.41,-4.13)#8  (+3.74,+1.21)#20  (+3.40,+4.49)#32  (-4.76,-0.03)#44  (-2.01,-4.47)#56  (+5.30,-1.32)#68  (+0.53,+4.11)#80  (-5.45,+2.40)#92  (+1.01,-3.43)#104  (+5.17,-3.43)#116  (-2.52,+2.52)#128
- **M5**: (-3.40,+2.70)#1  (-3.72,+3.99)#13  (+4.42,-1.52)#25  (+2.52,-4.43)#37  (-5.18,+0.36)#49  (-1.02,+4.51)#61  (+5.46,+1.00)#73  (-0.52,-4.24)#85  (-5.29,-2.11)#97  (+2.00,+3.64)#109  (+4.75,+3.21)#121
- **M6**: (-4.15,-2.96)#6  (-2.91,-3.82)#18  (+4.94,+1.82)#30  (+1.55,+4.35)#42  (-5.42,-0.68)#54  (+0.00,-4.52)#66  (+5.42,-0.68)#78  (-1.55,+4.35)#90  (-4.94,+1.82)#102  (+2.91,-3.82)#114  (+4.15,-2.96)#126
- **M7**: (-4.75,+3.21)#11  (-2.00,+3.64)#23  (+5.29,-2.11)#35  (+0.52,-4.24)#47  (-5.46,+1.00)#59  (+1.02,+4.51)#71  (+5.18,+0.36)#83  (-2.52,-4.43)#95  (-4.42,-1.52)#107  (+3.72,+3.99)#119  (+3.40,+2.70)#131
- **M8**: (+2.52,+2.52)#4  (-5.17,-3.43)#16  (-1.01,-3.43)#28  (+5.45,+2.40)#40  (-0.53,+4.11)#52  (-5.30,-1.32)#64  (+2.01,-4.47)#76  (+4.76,-0.03)#88  (-3.40,+4.49)#100  (-3.74,+1.21)#112  (+4.41,-4.13)#124
- **M9**: (+1.55,-2.23)#9  (-5.41,+3.64)#21  (+0.01,+3.22)#33  (+5.41,-2.67)#45  (-1.56,-3.96)#57  (-4.95,+1.62)#69  (+2.92,+4.42)#81  (+4.16,-0.30)#93  (-4.15,-4.53)#105  (-2.92,-0.90)#117  (+4.93,+4.26)#129
- **M10**: (+5.28,+4.33)#2  (+0.52,+1.93)#14  (-5.44,-3.82)#26  (+1.03,-2.98)#38  (+5.18,+2.92)#50  (-2.53,+3.79)#62  (-4.42,-1.91)#74  (+3.73,-4.34)#86  (+3.41,+0.63)#98  (-4.74,+4.53)#110  (-2.01,+0.58)#122
- **M11**: (+5.44,-4.41)#7  (-0.53,-1.61)#19  (-5.28,+3.99)#31  (+2.02,+2.73)#43  (+4.76,-3.16)#55  (-3.41,-3.60)#67  (-3.74,+2.20)#79  (+4.41,+4.25)#91  (+2.53,-0.97)#103  (-5.17,-4.52)#115  (-1.02,-0.26)#127

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
