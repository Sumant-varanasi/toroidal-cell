# As-built spec -- class D190: 19.04 m in a 182 mm envelope

8 x Thorlabs **CM508-150-M01** (1" protected-gold concave, ROC 300 mm, CA radius 22.9 mm, R = 0.999 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **67.794 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 8, every 45.00 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 25 mm |
| assembly envelope | 182 mm dia (R_ring + 23 mm substrate+wall) |
| enclosed gas volume | 0.36 L |
| est. mass (mirrors + Al ring) | ~632 g |
| optics cost | 8 x ~$74 = ~$592 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +67.794 |   +0.000 |    0.00 |  180.00 |
| M1 |  +47.937 |  +47.937 |   45.00 |  225.00 |
| M2 |   +0.000 |  +67.794 |   90.00 |  270.00 |
| M3 |  -47.937 |  +47.937 |  135.00 |  315.00 |
| M4 |  -67.794 |   +0.000 |  180.00 |    0.00 |
| M5 |  -47.937 |  -47.937 |  225.00 |   45.00 |
| M6 |   -0.000 |  -67.794 |  270.00 |   90.00 |
| M7 |  +47.937 |  -47.937 |  315.00 |  135.00 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, +0.36) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.315 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.224 mm, located 93.9 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.38 mm max) |
| launch tilt, in-plane | -60.76 mrad from the M0->M3 chord |
| launch tilt, out-of-plane | +53.71 mrad |
| launch height offset | +0.36 mm |
| exit beam | back through the same hole, 141.5 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **19.041 m** |
| chords | 152 legs, mean 125.27 mm (min 118.30, max 131.08) |
| reflections | 151 (R^151 = 85.98 %) |
| spots per mirror | 19 |
| AOI | mean 22.61 deg, max 25.60 deg |
| beam radius in cell | 0.24 - 0.38 mm |
| throughput @ R = 0.999 | **85.98 %** = 100.00 % (hole in+out) x 85.98 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^151  (R = 0.984 -> 8.76 %, R = 0.97 -> 1.01 %) |
| stability | m_tan = +0.547, m_sag = +0.615 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 10.0 m | 19.04 m | PASS |
| intermediate spots clear hole | +3.85 mm | PASS |
| beam edge inside clear aperture | +10.34 mm | PASS |
| spot separation (fringe safety) | +0.95 mm beyond touching (min sep 1.62 mm) | PASS |
| per-plane stability | tan +0.547 / sag +0.615 | PASS |
| envelope | 182 <= 190 mm | PASS |
| mirror packing web | 26.49 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,+0.36)#0  (+9.22,+6.92)#8  (-1.71,+7.39)#16  (-8.64,+0.67)#24  (+2.54,-6.14)#32  (+8.88,-8.04)#40  (-4.92,-2.13)#48  (-7.19,+5.50)#56  (+5.05,+8.09)#64  (+7.43,+3.91)#72  (-7.44,-4.54)#80  (-5.03,-8.13)#88  (+7.20,-4.94)#96  (+4.90,+2.83)#104  (-8.87,+8.19)#112  (-2.53,+5.65)#120  (+8.63,-1.39)#128  (+1.70,-7.69)#136  (-9.22,-6.50)#144  (+0.00,+0.36)#152
- **M1**: (-1.26,+2.88)#3  (+9.03,-4.53)#11  (-0.01,-8.27)#19  (-9.04,-3.90)#27  (+1.27,+3.54)#35  (+9.18,+8.17)#43  (-3.37,+5.22)#51  (-8.02,-2.65)#59  (+3.81,-7.74)#67  (+8.30,-6.54)#75  (-6.30,+1.33)#83  (-6.18,+7.43)#91  (+6.20,+7.10)#99  (+6.28,+0.60)#107  (-8.30,-6.97)#115  (-3.79,-7.50)#123  (+8.02,-1.95)#131  (+3.35,+5.77)#139  (-9.17,+8.01)#147
- **M2**: (-2.53,-5.65)#6  (+8.63,+1.39)#14  (+1.70,+7.69)#22  (-9.22,+6.50)#30  (+0.00,-0.36)#38  (+9.22,-6.92)#46  (-1.71,-7.39)#54  (-8.64,-0.67)#62  (+2.54,+6.14)#70  (+8.88,+8.04)#78  (-4.92,+2.13)#86  (-7.19,-5.50)#94  (+5.05,-8.09)#102  (+7.43,-3.91)#110  (-7.44,+4.54)#118  (-5.03,+8.13)#126  (+7.20,+4.94)#134  (+4.90,-2.83)#142  (-8.87,-8.19)#150
- **M3**: (-8.30,+6.97)#1  (-3.79,+7.50)#9  (+8.02,+1.95)#17  (+3.35,-5.77)#25  (-9.17,-8.01)#33  (-1.26,-2.88)#41  (+9.03,+4.53)#49  (-0.01,+8.27)#57  (-9.04,+3.90)#65  (+1.27,-3.54)#73  (+9.18,-8.17)#81  (-3.37,-5.22)#89  (-8.02,+2.65)#97  (+3.81,+7.74)#105  (+8.30,+6.54)#113  (-6.30,-1.33)#121  (-6.18,-7.43)#129  (+6.20,-7.10)#137  (+6.28,-0.60)#145
- **M4**: (-7.44,-4.54)#4  (-5.03,-8.13)#12  (+7.20,-4.94)#20  (+4.90,+2.83)#28  (-8.87,+8.19)#36  (-2.53,+5.65)#44  (+8.63,-1.39)#52  (+1.70,-7.69)#60  (-9.22,-6.50)#68  (+0.00,+0.36)#76  (+9.22,+6.92)#84  (-1.71,+7.39)#92  (-8.64,+0.67)#100  (+2.54,-6.14)#108  (+8.88,-8.04)#116  (-4.92,-2.13)#124  (-7.19,+5.50)#132  (+5.05,+8.09)#140  (+7.43,+3.91)#148
- **M5**: (-6.30,+1.33)#7  (-6.18,+7.43)#15  (+6.20,+7.10)#23  (+6.28,+0.60)#31  (-8.30,-6.97)#39  (-3.79,-7.50)#47  (+8.02,-1.95)#55  (+3.35,+5.77)#63  (-9.17,+8.01)#71  (-1.26,+2.88)#79  (+9.03,-4.53)#87  (-0.01,-8.27)#95  (-9.04,-3.90)#103  (+1.27,+3.54)#111  (+9.18,+8.17)#119  (-3.37,+5.22)#127  (-8.02,-2.65)#135  (+3.81,-7.74)#143  (+8.30,-6.54)#151
- **M6**: (+8.88,+8.04)#2  (-4.92,+2.13)#10  (-7.19,-5.50)#18  (+5.05,-8.09)#26  (+7.43,-3.91)#34  (-7.44,+4.54)#42  (-5.03,+8.13)#50  (+7.20,+4.94)#58  (+4.90,-2.83)#66  (-8.87,-8.19)#74  (-2.53,-5.65)#82  (+8.63,+1.39)#90  (+1.70,+7.69)#98  (-9.22,+6.50)#106  (+0.00,-0.36)#114  (+9.22,-6.92)#122  (-1.71,-7.39)#130  (-8.64,-0.67)#138  (+2.54,+6.14)#146
- **M7**: (+9.18,-8.17)#5  (-3.37,-5.22)#13  (-8.02,+2.65)#21  (+3.81,+7.74)#29  (+8.30,+6.54)#37  (-6.30,-1.33)#45  (-6.18,-7.43)#53  (+6.20,-7.10)#61  (+6.28,-0.60)#69  (-8.30,+6.97)#77  (-3.79,+7.50)#85  (+8.02,+1.95)#93  (+3.35,-5.77)#101  (-9.17,-8.01)#109  (-1.26,-2.88)#117  (+9.03,+4.53)#125  (-0.01,+8.27)#133  (-9.04,+3.90)#141  (+1.27,-3.54)#149

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
