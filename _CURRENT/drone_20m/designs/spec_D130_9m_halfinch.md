# As-built spec -- class D130: 9.11 m in a 129 mm envelope

14 x Thorlabs **CM127-050-M01** (1" protected-gold concave, ROC 100 mm, CA radius 5.7 mm, R = 0.999 @ 1654 nm)

## 1. Machined ring housing

| item | value |
|---|---|
| mirror-face ring radius R_ring | **51.599 mm** (closure-critical: machine to +/-0.05 mm, then tune by ring temperature / shims) |
| mirrors | N = 14, every 25.71 deg |
| pocket normal | radial, facing cell centre |
| cell height (inner) | 13 mm |
| assembly envelope | 129 mm dia (R_ring + 13 mm substrate+wall) |
| enclosed gas volume | 0.11 L |
| est. mass (mirrors + Al ring) | ~616 g |
| optics cost | 14 x ~$74 = ~$1036 |

Mirror placement (cell frame, z = 0 mid-height plane):

| mirror | x [mm] | y [mm] | azimuth [deg] | normal azimuth [deg] |
|---|---|---|---|---|
| M0 |  +51.599 |   +0.000 |    0.00 |  180.00 |
| M1 |  +46.489 |  +22.388 |   25.71 |  205.71 |
| M2 |  +32.172 |  +40.342 |   51.43 |  231.43 |
| M3 |  +11.482 |  +50.306 |   77.14 |  257.14 |
| M4 |  -11.482 |  +50.306 |  102.86 |  282.86 |
| M5 |  -32.172 |  +40.342 |  128.57 |  308.57 |
| M6 |  -46.489 |  +22.388 |  154.29 |  334.29 |
| M7 |  -51.599 |   +0.000 |  180.00 |    0.00 |
| M8 |  -46.489 |  -22.388 |  205.71 |   25.71 |
| M9 |  -32.172 |  -40.342 |  231.43 |   51.43 |
| M10 |  -11.482 |  -50.306 |  257.14 |   77.14 |
| M11 |  +11.482 |  -50.306 |  282.86 |  102.86 |
| M12 |  +32.172 |  -40.342 |  308.57 |  128.57 |
| M13 |  +46.489 |  -22.388 |  334.29 |  154.29 |

## 2. Injection / extraction optics (behind mirror M0)

| item | value |
|---|---|
| entrance hole | radius 0.8 mm through M0, centred at (u, v) = (+0.02, +2.45) mm on the mirror face (u = in-plane, v = height) |
| input beam | 0.8 mm collimated (laser collimator), mode-matched down by a small lens |
| beam at the hole | 1/e^2 radius 0.260 mm (passes the 0.8 mm hole with 100.00 % transmission) |
| in-cell waist | 0.200 mm, located 63.1 mm past the hole (mode-matching lens focus; cell eigenmode ride, beam stays 0.33 mm max) |
| launch tilt, in-plane | +44.57 mrad from the M0->M5 chord |
| launch tilt, out-of-plane | -9.68 mrad |
| launch height offset | +2.45 mm |
| exit beam | back through the same hole, 123.5 deg from the injection axis -- place the detector on that line behind M0 |

## 3. Path accounting

| item | value |
|---|---|
| OPL (hole -> hole) | **9.112 m** |
| chords | 98 legs, mean 92.98 mm (min 90.13, max 95.60) |
| reflections | 97 (R^97 = 90.75 %) |
| spots per mirror | 7 |
| AOI | mean 25.71 deg, max 28.27 deg |
| beam radius in cell | 0.18 - 0.33 mm |
| throughput @ R = 0.999 | **90.75 %** = 100.00 % (hole in+out) x 90.75 % (mirrors) |
| throughput, parametric | T(R) = 1.0000 x R^97  (R = 0.984 -> 20.92 %, R = 0.97 -> 5.21 %) |
| stability | m_tan = -0.033, m_sag = +0.163 (|m| <= 1) |

## 4. Physical-check matrix (exact 3-D ray trace)

| check | margin | verdict |
|---|---|---|
| exits through entrance hole | miss 0.000 mm (tol 0.5) | PASS |
| OPL >= 8.0 m | 9.11 m | PASS |
| intermediate spots clear hole | +1.07 mm | PASS |
| beam edge inside clear aperture | +0.42 mm | PASS |
| spot separation (fringe safety) | +0.65 mm beyond touching (min sep 1.20 mm) | PASS |
| per-plane stability | tan -0.033 / sag +0.163 | PASS |
| envelope | 129 <= 130 mm | PASS |
| mirror packing web | -2.44 mm | FAIL |

## 5. Spot constellations (mirror-face coordinates, mm)

u = in-plane (tangential), v = height (sagittal); visit order in parentheses. M0 also shows the hole (H).

- **M0** [H = entrance hole at #0]: (+0.02,+2.45)#0  (+1.93,+1.41)#14  (-3.53,-0.76)#28  (+4.44,-2.26)#42  (-4.44,-2.26)#56  (+3.55,-0.76)#70  (-1.96,+1.41)#84  (+0.02,+2.45)#98
- **M1**: (-4.54,-0.78)#3  (+3.90,+1.14)#17  (-2.47,+2.50)#31  (+0.58,+1.97)#45  (+1.40,+0.18)#59  (-3.13,-1.82)#73  (+4.25,-2.52)#87
- **M2**: (+0.86,-1.69)#6  (-2.69,-2.48)#20  (+4.00,-1.67)#34  (-4.55,+0.49)#48  (+4.17,+2.08)#62  (-2.95,+2.40)#76  (+1.15,+1.00)#90
- **M3**: (+4.36,+2.45)#9  (-3.38,+1.10)#23  (+1.72,-0.90)#37  (+0.28,-2.41)#51  (-2.21,-2.11)#65  (+3.71,-0.52)#79  (-4.48,+1.63)#93
- **M4**: (-1.68,-0.57)#12  (+3.35,+1.41)#26  (-4.35,+2.49)#40  (+4.48,+1.88)#54  (-3.73,-0.17)#68  (+2.24,-1.91)#82  (-0.31,-2.50)#96
- **M5**: (+4.55,+0.14)#1  (-4.02,-1.92)#15  (+2.71,-2.47)#29  (-0.89,-1.41)#43  (-1.12,+0.67)#57  (+2.93,+2.27)#71  (-4.16,+2.25)#85
- **M6**: (-0.55,+2.16)#4  (+2.44,+2.41)#18  (-3.88,+0.83)#32  (+4.54,-1.11)#46  (-4.26,-2.48)#60  (+3.15,-2.04)#74  (-1.44,-0.18)#88
- **M7**: (-4.45,-2.08)#7  (+3.55,-0.43)#21  (-1.96,+1.69)#35  (+0.02,+2.47)#49  (+1.93,+1.69)#63  (-3.53,-0.43)#77  (+4.44,-2.08)#91
- **M8**: (+1.40,-0.18)#10  (-3.12,-2.04)#24  (+4.25,-2.48)#38  (-4.54,-1.11)#52  (+3.90,+0.83)#66  (-2.47,+2.41)#80  (+0.58,+2.16)#94
- **M9**: (+4.17,+2.25)#13  (-2.95,+2.27)#27  (+1.15,+0.67)#41  (+0.86,-1.41)#55  (-2.69,-2.47)#69  (+4.00,-1.92)#83  (-4.55,+0.14)#97
- **M10**: (+0.27,-2.50)#2  (-2.21,-1.91)#16  (+3.71,-0.17)#30  (-4.48,+1.88)#44  (+4.36,+2.49)#58  (-3.37,+1.41)#72  (+1.71,-0.57)#86
- **M11**: (+4.48,+1.63)#5  (-3.73,-0.52)#19  (+2.24,-2.11)#33  (-0.31,-2.41)#47  (-1.69,-0.90)#61  (+3.35,+1.10)#75  (-4.35,+2.45)#89
- **M12**: (-1.12,+1.00)#8  (+2.92,+2.40)#22  (-4.16,+2.08)#36  (+4.55,+0.49)#50  (-4.02,-1.67)#64  (+2.72,-2.48)#78  (-0.89,-1.69)#92
- **M13**: (-4.27,-2.52)#11  (+3.15,-1.82)#25  (-1.43,+0.18)#39  (-0.55,+1.97)#53  (+2.44,+2.50)#67  (-3.89,+1.14)#81  (+4.54,-0.78)#95

Generated by drone_20m/spec_asbuilt.py from the exact ray-traced design; tolerances from the Monte-Carlo study in the same folder.
