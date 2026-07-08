# As-built spec -- class D180: 15.30 m in a 175 mm envelope

16 x Thorlabs **CM254-100-M01** (1" protected-gold concave, ROC 200 mm, CA radius 11.4 mm, R = 0.999 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **69.632 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 16, every 22.50 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 14 mm |
| assembly envelope | 175 mm dia (R_ring + 18 mm substrate+wall) |
| enclosed gas volume | 0.21 L |
| est. mass (mirrors + Al ring) | ~776 g |
| optics cost | 16 x ~$74 = ~$1184 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +69.632 |   +0.000 |    0.00 |  180.00 |
| M1 |  +64.332 |  +26.647 |   22.50 |  202.50 |
| M2 |  +49.238 |  +49.238 |   45.00 |  225.00 |
| M3 |  +26.647 |  +64.332 |   67.50 |  247.50 |
| M4 |   +0.000 |  +69.632 |   90.00 |  270.00 |
| M5 |  -26.647 |  +64.332 |  112.50 |  292.50 |
| M6 |  -49.238 |  +49.238 |  135.00 |  315.00 |
| M7 |  -64.332 |  +26.647 |  157.50 |  337.50 |
| M8 |  -69.632 |   +0.000 |  180.00 |    0.00 |
| M9 |  -64.332 |  -26.647 |  202.50 |   22.50 |
| M10 |  -49.238 |  -49.238 |  225.00 |   45.00 |
| M11 |  -26.647 |  -64.332 |  247.50 |   67.50 |
| M12 |   -0.000 |  -69.632 |  270.00 |   90.00 |
| M13 |  +26.647 |  -64.332 |  292.50 |  112.50 |
| M14 |  +49.238 |  -49.238 |  315.00 |  135.00 |
| M15 |  +64.332 |  -26.647 |  337.50 |  157.50 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 1.3 mm through M0, centred at (u, v) = (+0.00, -0.04) mm on the mirror face (u = in-plane, v = height) |
| input beam | 1.3 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.280 mm (passes the 1.3 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 74.2 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.31 mm max) |
| launch tilt, in-plane | -28.75 mrad from the M0->M7 chord |
| launch tilt, out-of-plane | +19.08 mrad |
| launch height offset | -0.04 mm |
| exit beam | back through the same hole, 157.4 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **15.298 m** |
| chords | 112 legs, mean 136.59 mm (min 135.22, max 137.89) |
| reflections | 111 (R^111 = 89.49 %) |
| spots per mirror | 7 |
| AOI | mean 11.27 deg, max 12.96 deg |
| beam radius in cell | 0.25 - 0.31 mm |
| throughput @ R = 0.999 | **89.49 %** = 100.00 % (hole in+out) x 89.49 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^111  (R = 0.984 -> 16.69 %, R = 0.97 -> 3.40 %) |
| stability | m_tan = +0.304, m_sag = +0.330 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 15.0 m | 15.30 m | PASS |
| intermediate spots clear hole | +1.62 mm | PASS |
| beam edge inside clear aperture | +6.30 mm | PASS |
| spot separation (fringe safety) | +1.12 mm beyond touching (min sep 1.71 mm) | PASS |
| per-plane stability | tan +0.304 / sag +0.330 | PASS |
| envelope | 175 <= 180 mm | PASS |
| mirror packing web | 1.77 mm | PASS |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.00,-0.04)#0  (+4.13,+2.10)#16  (+1.82,+2.64)#32  (-3.30,+1.19)#48  (-3.32,-1.15)#64  (+1.84,-2.65)#80  (+4.11,-2.16)#96  (+0.00,-0.04)#112
- **M1**: (-2.36,+1.95)#7  (+2.92,-0.27)#23  (+3.64,-2.27)#39  (-1.28,-2.55)#55  (-4.22,-0.92)#71  (-0.60,+1.42)#87  (+3.95,+2.71)#103
- **M2**: (-3.90,-2.73)#14  (+0.71,-1.72)#30  (+4.23,+0.56)#46  (+1.17,+2.41)#62  (-3.69,+2.45)#78  (-2.83,+0.64)#94  (+2.46,-1.67)#110
- **M3**: (-0.12,-0.34)#5  (-4.13,+1.91)#21  (-1.73,+2.71)#37  (+3.39,+1.48)#53  (+3.23,-0.84)#69  (-1.92,-2.54)#85  (-4.10,-2.32)#101
- **M4**: (+2.23,+2.14)#12  (-2.98,+0.01)#28  (-3.58,-2.11)#44  (+1.40,-2.66)#60  (+4.20,-1.23)#76  (+0.48,+1.13)#92  (-3.97,+2.65)#108
- **M5**: (+2.55,-1.42)#3  (+3.85,-2.69)#19  (-0.83,-1.92)#35  (-4.23,+0.29)#51  (-1.06,+2.28)#67  (+3.76,+2.59)#83  (+2.71,+0.95)#99
- **M6**: (+0.24,-0.64)#10  (+4.17,+1.66)#26  (+1.61,+2.70)#42  (-3.45,+1.70)#58  (-3.16,-0.57)#74  (+2.05,-2.44)#90  (+4.05,-2.47)#106
- **M7**: (-4.01,+2.56)#1  (-2.15,+2.33)#17  (+3.08,+0.34)#33  (+3.51,-1.88)#49  (-1.50,-2.68)#65  (-4.19,-1.47)#81  (-0.36,+0.86)#97
- **M8**: (-2.62,-1.16)#8  (-3.81,-2.65)#24  (+0.95,-2.15)#40  (+4.23,-0.05)#56  (+0.95,+2.08)#72  (-3.80,+2.65)#88  (-2.65,+1.21)#104
- **M9**: (-0.36,-0.92)#15  (-4.18,+1.43)#31  (-1.51,+2.70)#47  (+3.52,+1.96)#63  (+3.07,-0.25)#79  (-2.13,-2.28)#95  (-4.03,-2.58)#111
- **M10**: (+4.06,+2.44)#6  (+2.03,+2.45)#22  (-3.15,+0.62)#38  (-3.46,-1.68)#54  (+1.62,-2.72)#70  (+4.16,-1.74)#86  (+0.24,+0.56)#102
- **M11**: (+2.74,-0.87)#13  (+3.75,-2.54)#29  (-1.06,-2.29)#45  (-4.23,-0.33)#61  (-0.83,+1.90)#77  (+3.86,+2.72)#93  (+2.53,+1.48)#109
- **M12**: (-3.99,-2.66)#4  (+0.48,-1.21)#20  (+4.21,+1.14)#36  (+1.39,+2.62)#52  (-3.58,+2.13)#68  (-3.00,+0.03)#84  (+2.26,-2.11)#100
- **M13**: (-4.08,+2.30)#11  (-1.95,+2.58)#27  (+3.24,+0.94)#43  (+3.38,-1.39)#59  (-1.71,-2.68)#75  (-4.15,-1.95)#91  (-0.12,+0.27)#107
- **M14**: (+2.43,+1.73)#2  (-2.81,-0.59)#18  (-3.70,-2.44)#34  (+1.17,-2.47)#50  (+4.22,-0.66)#66  (+0.72,+1.65)#82  (-3.89,+2.72)#98
- **M15**: (+3.93,-2.71)#9  (-0.60,-1.46)#25  (-4.21,+0.88)#41  (-1.29,+2.56)#57  (+3.64,+2.33)#73  (+2.90,+0.36)#89  (-2.33,-1.90)#105

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
