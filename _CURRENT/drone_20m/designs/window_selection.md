# Cell window selection — wedged, angled, AR-coated, drone-proof

*(Dr. Benoy, 2026-07-08: "Choose the cell window (wedged ½ inch AR coated
CaF₂ or other materials? CaF₂ is too brittle. Find another material which
is AR coated (same as Thorlabs) and less brittle, for drones. The windows
must be wedged and angled.")*

## Recommendation (short version)

* **NH₃ 1512 nm + CH₄ 1654 nm:** Thorlabs **WW10530-C** — Ø1/2″ UV fused
  silica wedged window, 30 arcmin wedge, -C BBAR 1050–1700 nm
  (R_avg < 0.5 %/surface). Fused silica is ~4× harder and ~2× tougher
  than CaF₂ and is the standard rugged NIR window.
* **H₂ 2121.8 nm (and as the one-window-fits-CH₄+H₂ option):** Thorlabs
  **WW30530-D** — Ø1/2″ **sapphire** wedged window, 30 arcmin, -D BBAR
  1.65–3.0 µm (R_avg < 1.0 %/surface). Sapphire is the most break-proof
  window material in the catalog — the correct drone choice where the
  coating band allows.
* Mount every window **tilted 3–5°** on the mirror-0 boss (the CAD
  already provides the flat); wedge apex horizontal so both residual
  ghosts walk out of plane.
* CaF₂ (and BaF₂) are rejected on numbers, not vibes — see the table.

No single catalog wedged window is AR-coated across 1512→2122 nm; the
per-gas pair above covers all three lines with two stock parts (the
sapphire -D covers CH₄+H₂ in one part; UVFS -C covers NH₃+CH₄).

## 1. Mechanical robustness — why CaF₂ is out and sapphire is in

Handbook values (Thorlabs/Crystran substrate data):

| material | Knoop hardness [kg/mm²] | rupture modulus [MPa] | fracture toughness [MPa·√m] | verdict for a drone |
|---|---|---|---|---|
| **sapphire** | **1370–2200** | **~450–700** | **~2.0** | best available; scratch-proof, thermal-shock tolerant |
| UV fused silica | ~500–600 | ~50–110 | ~0.75 | good; the rugged default below 2.1 µm |
| N-BK7 | 610 | ~50 | ~0.85 | good; cheapest, fine at 1512/1654 |
| MgF₂ | 415 | ~50 | ~0.9 | acceptable; mainly a UV material |
| **CaF₂** | **158** | **~37** | **~0.3–0.5** | soft, cleaves, thermal-shock sensitive — the professor's concern is quantitatively right |
| BaF₂ | 82 | ~27 | ~0.27 | worse than CaF₂ in every column |
| ZnSe | 120 | ~55 | ~0.5 | soft, toxic dust; mid-IR only |

Sapphire beats CaF₂ by ~10× in hardness, ~12–19× in rupture strength and
~4–6× in fracture toughness; fused silica beats it by ~4× / ~2–3× / ~2×.
(The IRcell offers BaF₂/CaF₂/sapphire/N-BK7/ZnSe windows — sapphire is
the drone pick there too.)

## 2. Optical fit at our three lines

| window | 1512.2 nm | 1653.7 nm | 2121.8 nm | notes |
|---|---|---|---|---|
| WW10530-C (UVFS, -C 1050–1700 nm) | ✅ R<0.5 % | ✅ (inside band) | ✖ — substrate OH absorption band near 2.2 µm; Thorlabs quotes UVFS to 2.1 µm | the NH₃/CH₄ window |
| WW30530-D (sapphire, -D 1.65–3.0 µm) | ✖ (below band) | ✅ 1653.7 nm sits just inside the 1.65 µm band edge — verify the coating curve on order | ✅ R<1.0 % | the H₂ (and CH₄+H₂ combo) window |
| WW30530 uncoated sapphire | 0.15–4.5 µm, ~7 %/surface Fresnel | same | same | fallback single window for all three gases at ~14 % loss — acceptable only if channel-swapping outweighs loss |
| wedged CaF₂ (e.g. WW51050 family) | ✅ optically | ✅ | ✅ | rejected mechanically (above) |

Notes: (a) IR-grade fused silica (Infrasil) would also cover 2122 nm but
Thorlabs' *wedged* window families are N-BK7/UVFS/CaF₂/MgF₂/BaF₂/ZnSe/
sapphire/Si/Ge — sapphire is the stocked wedged+AR route for 2.1 µm.
(b) Order sapphire **c-cut** (axis ⊥ faces, the Thorlabs standard) so the
3–5° mounting tilt introduces no polarization/birefringence structure.
(c) Ø1/2″ wedged windows are ~3 mm thick (Ø1″ = 5 mm) — confirm on the
spec sheet at order time.

## 3. Wedge + tilt geometry (etalon suppression, quantified)

The 30 arcmin (8.73 mrad) wedge makes the two window surfaces
non-parallel, so the back-surface reflection leaves at 2nα from the
front-surface ghost and neither can resonate with the transmitted beam:

* ghost walk-off angle 2nα: UVFS 25 mrad, sapphire 30 mrad — ~30–70×
  the collimated-beam divergence (0.4–0.8 mrad), so the specular ghost
  is spatially disjoint from the mode within ~50 mm of propagation
  (>3 mm displacement at the collimator, vs w ≈ 0.65 mm).
* transmitted-beam deviation (n−1)α: UVFS 3.9 mrad, sapphire 6.4 mrad —
  constant; absorbed once in the launch alignment (the spec sheets'
  launch tilts already carry mrad-scale entries).
* mounting tilt 3–5° on top of the wedge takes the *front-surface*
  reflection off the collimator axis too (window mounted on the
  mirror-0 boss, both entry and exit beams pass the same Ø12.7 mm
  window — at ~10 mm behind the hole the two beams are ~4 mm apart at
  22–30° included angle, comfortably inside the clear aperture).
* residual etalon FSR if any parallel-surface leakage remained: 3 mm
  UVFS → 1.15 cm⁻¹; 3 mm sapphire → 0.96 cm⁻¹ — 10–50× wider than the
  absorption features (CH₄/NH₃ FWHM ≈ 0.1–0.2 cm⁻¹ at 1 atm; H₂
  0.03–0.04 cm⁻¹), i.e. any residue appears as slow baseline curvature
  that the fit removes, not line-shaped noise.
* measured precedent: wedged vs plane-parallel windows in a 1650 nm CH₄
  cell reduced the 2f fringe amplitude ~23× (Masiyano, Cranfield thesis);
  Webster's Brewster-plate benchmark is ~30×.

## 4. Assembly notes

1. Window seats on the machined boss behind mirror 0 (see
   [cad/](cad/) STEP models), sealing the conical beam port; one window
   serves both entry and exit beams; the detector and collimator sit
   outside the sealed volume.
2. Seal with an FKM O-ring (NH₃-compatible; avoid NBR for ammonia work),
   captured by a printed or machined bezel — the bezel is a safe part to
   3D print.
3. Orient the wedge apex in the sagittal plane and the 3–5° tilt in the
   tangential plane so ghost walk-offs and the beam-fold plane don't
   coincide.
4. For the H₂ channel the narrow (sub-Doppler) line makes *long-OPD*
   parasites the risk, not the mm-scale window — the cell's enforced
   spot separation is the relevant defence; the window choice is then
   purely a transmission/robustness decision, which sapphire wins.

Sources: Thorlabs wedged-window family pages (WW10530/WW30530 series,
coating bands -C 1050–1700 nm R<0.5 %, -D 1.65–3.0 µm R<1.0 %, sapphire
uncoated 0.15–4.5 µm); Thorlabs/Crystran substrate mechanical data;
Masiyano (Cranfield, 2009) measured wedged-window suppression; IRcell
datasheet window options for the comparator.
