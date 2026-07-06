# As-built spec -- class D170: 16.60 m in a 160 mm envelope

13 x Thorlabs **CM254-150-M01** (1" protected-gold concave, ROC 300 mm, CA radius 11.4 mm, R = 0.999 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **62.085 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 13, every 27.69 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 22 mm |
| assembly envelope | 160 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.27 L |
| est. mass (mirrors + Al ring) | ~676 g |
| optics cost | 13 x ~$74 = ~$962 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +62.085 |   +0.000 |    0.00 |  180.00 |
| M1 |  +54.973 |  +28.852 |   27.69 |  207.69 |
| M2 |  +35.268 |  +51.095 |   55.38 |  235.38 |
| M3 |   +7.484 |  +61.632 |   83.08 |  263.08 |
| M4 |  -22.016 |  +58.050 |  110.77 |  290.77 |
| M5 |  -46.471 |  +41.170 |  138.46 |  318.46 |
| M6 |  -60.281 |  +14.858 |  166.15 |  346.15 |
| M7 |  -60.281 |  -14.858 |  193.85 |   13.85 |
| M8 |  -46.471 |  -41.170 |  221.54 |   41.54 |
| M9 |  -22.016 |  -58.050 |  249.23 |   69.23 |
| M10 |   +7.484 |  -61.632 |  276.92 |   96.92 |
| M11 |  +35.268 |  -51.095 |  304.62 |  124.62 |
| M12 |  +54.973 |  -28.852 |  332.31 |  152.31 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.09) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.289 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.289 mm, located 0.0 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.37 mm max) |
| launch tilt, in-plane | -34.53 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | +49.43 mrad |
| launch height offset | -0.09 mm |
| exit beam | back through the same hole, 142.0 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **16.602 m** |
| chords | 143 legs, mean 116.10 mm (min 112.64, max 119.36) |
| reflections | 142 (R^142 = 86.76 %) |
| spots per mirror | 11 |
| AOI | mean 20.86 deg, max 22.77 deg |
| beam radius in cell | 0.22 - 0.37 mm |
| throughput @ R = 0.999 | **86.76 %** = 100.00 % (hole in+out) x 86.76 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^142  (R = 0.984 -> 10.12 %, R = 0.97 -> 1.32 %) |
| stability | m_tan = +0.586, m_sag = +0.638 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 16.0 m | 16.60 m | PASS |
| intermediate spots clear hole | +2.76 mm | PASS |
| beam edge inside clear aperture | +2.61 mm | PASS |
| spot separation (fringe safety) | +0.53 mm beyond touching (min sep 1.12 mm) | PASS |
| per-plane stability | tan +0.586 / sag +0.638 | PASS |
| envelope | 160 <= 170 mm | PASS |
| mirror packing web | 4.32 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.09)#0  (+1.51,-6.39)#13  (-2.70,-5.22)#26  (+4.00,+2.17)#39  (-4.55,+6.87)#52  (+5.09,+3.56)#65  (-5.09,-3.71)#78  (+4.55,-6.84)#91  (-4.00,-2.00)#104  (+2.70,+5.33)#117  (-1.51,+6.32)#130  (+0.00,-0.09)#143
- **M1**: (+4.81,+4.56)#8  (-4.38,-2.64)#21  (+3.19,-6.92)#34  (-2.17,-3.09)#47  (+0.68,+4.43)#60  (+0.81,+6.72)#73  (-2.11,+1.18)#86  (+3.51,-5.85)#99  (-4.26,-5.97)#112  (+5.01,+1.00)#125  (-5.10,+6.59)#138
- **M2**: (-1.46,+3.39)#3  (+2.96,+6.93)#16  (-3.86,+2.40)#29  (+4.80,-5.12)#42  (-5.06,-6.52)#55  (+5.03,-0.23)#68  (-4.68,+6.11)#81  (+3.65,+5.41)#94  (-2.78,-1.52)#107  (+1.29,-6.78)#120  (+0.11,-4.07)#133
- **M3**: (+4.11,-1.47)#11  (-3.32,+5.45)#24  (+1.86,+6.10)#37  (-0.59,-0.37)#50  (-0.83,-6.43)#63  (+2.36,-4.95)#76  (-3.36,+2.24)#89  (+4.48,+6.95)#102  (-4.93,+3.54)#115  (+5.14,-4.21)#128  (-4.92,-6.86)#141
- **M4**: (-2.82,-5.87)#6  (+4.11,-5.70)#19  (-4.68,+1.02)#32  (+5.11,+6.76)#45  (-5.09,+4.55)#58  (+4.50,-3.14)#71  (-3.82,-6.97)#84  (+2.46,-2.67)#97  (-1.27,+4.66)#110  (-0.24,+6.58)#123  (+1.73,+0.77)#136
- **M5**: (-4.27,+5.40)#1  (+3.05,-1.96)#14  (-1.94,-6.88)#27  (+0.40,-3.78)#40  (+1.06,+3.74)#53  (-2.29,+6.86)#66  (+3.68,+1.91)#79  (-4.33,-5.12)#92  (+5.01,-6.30)#105  (-5.14,-0.22)#118  (+4.77,+6.35)#131
- **M6**: (-3.96,+6.92)#9  (+4.86,+3.03)#22  (-5.07,-4.22)#35  (+4.94,-6.71)#48  (-4.62,-1.42)#61  (+3.56,+5.72)#74  (-2.58,+6.06)#87  (+1.08,-0.72)#100  (+0.36,-6.60)#113  (-1.73,-4.78)#126  (+3.17,+2.72)#139
- **M7**: (-3.17,-2.56)#4  (+1.73,+4.90)#17  (-0.36,+6.54)#30  (-1.08,+0.55)#43  (+2.58,-6.14)#56  (-3.56,-5.62)#69  (+4.62,+1.60)#82  (-4.94,+6.76)#95  (+5.07,+4.08)#108  (-4.86,-3.19)#121  (+3.96,-6.91)#134
- **M8**: (-4.77,-6.27)#12  (+5.14,+0.39)#25  (-5.01,+6.37)#38  (+4.33,+5.01)#51  (-3.67,-2.08)#64  (+2.29,-6.88)#77  (-1.06,-3.59)#90  (-0.40,+3.93)#103  (+1.94,+6.85)#116  (-3.05,+1.80)#129  (+4.27,-5.51)#142
- **M9**: (-1.73,-0.95)#7  (+0.23,-6.63)#20  (+1.27,-4.52)#33  (-2.46,+2.83)#46  (+3.82,+6.97)#59  (-4.50,+2.99)#72  (+5.09,-4.68)#85  (-5.11,-6.72)#98  (+4.68,-0.85)#111  (-4.11,+5.80)#124  (+2.82,+5.78)#137
- **M10**: (+4.92,+6.89)#2  (-5.14,+4.07)#15  (+4.93,-3.69)#28  (-4.48,-6.94)#41  (+3.36,-2.08)#54  (-2.36,+5.07)#67  (+0.83,+6.36)#80  (+0.59,+0.20)#93  (-1.87,-6.18)#106  (+3.32,-5.34)#119  (-4.11,+1.64)#132
- **M11**: (-0.11,+4.21)#10  (-1.29,+6.75)#23  (+2.78,+1.35)#36  (-3.66,-5.52)#49  (+4.68,-6.02)#62  (-5.03,+0.40)#75  (+5.06,+6.58)#88  (-4.80,+5.00)#101  (+3.86,-2.56)#114  (-2.96,-6.95)#127  (+1.46,-3.24)#140
- **M12**: (+5.10,-6.53)#5  (-5.01,-0.83)#18  (+4.26,+6.06)#31  (-3.51,+5.75)#44  (+2.11,-1.35)#57  (-0.81,-6.76)#70  (-0.68,-4.30)#83  (+2.17,+3.24)#96  (-3.20,+6.92)#109  (+4.38,+2.48)#122  (-4.81,-4.69)#135

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
