# Response map — Dr. Benoy's review points → deliverables

*(One page for the reply email. Every number is exact-trace and/or
Monte-Carlo verified; files live in `_CURRENT/drone_20m/designs/`.)*

| Your point | Answer in one line | Where |
|---|---|---|
| "Compare against the IRSweep gas cell... what is the downside?" | IRcell-S15: 15.12 m / Ø194 / 128 mL; ours: 20.38 m / Ø180 (+35 % path, smaller disc, 86.7 % verified throughput, catalog mirrors). Honest downside: our sealed volume is 200–330 mL vs their 31–128 mL — chord-skip sweeps the whole disc; per-litre we match the toroidal family with 2–5× the path. | [irsweep_comparison.md](irsweep_comparison.md) |
| "Compare overlap factor... Are your beams overlapping?" | No. Worst same-mirror pair sits 2.8–5.8 beam radii apart → field coupling −34…−148 dB (exact, all pairs, all designs). We propose the graded d/w̄ criterion as a figure of merit — the literature only has the binary rule. IRcell-4M superposes beams by design (hence its Teflon mask); IRcell-S segment edge sits at 3.45 w — our designs straddle-to-beat that. | [irsweep_comparison.md §3](irsweep_comparison.md) + `figures/overlap_coupling.png` |
| "Will the OD noise be worse?" | Mechanism-by-mechanism: no mask, no beam superposition, hole ≥2× beam dia (McManus criterion), wedged windows (23× measured suppression precedent), polished catalog mirrors (no diamond-turning tool marks — Graf's residual fringe source). Expected NEA in the segmented-cell class (2×10⁻⁵), i.e. better than masked toroids. Chord-parasite FSRs (0.034–0.064 cm⁻¹) sit ON the H₂ linewidth, which is exactly why the separation margin matters — quantified. | [irsweep_comparison.md §4](irsweep_comparison.md), [multigas.md §3b](multigas.md) |
| "Compare with other works also" | Full table: Tuzson 2013 toroid, Graf 2018 SC-MPC (page 2434 — 2665 is a typo worth fixing in our sources), Chang 2020 multi-layer, IRcell family, Aerodyne benchmark. | [irsweep_comparison.md §2](irsweep_comparison.md) |
| "Do for hydrogen 2121.8 nm and ammonia 1512.2 nm" | Geometry is λ-independent (spots scale √λ). NH₃: entire menu robust as-built. H₂ (hardest case): six designs robust; dedicated searches raised the tri-gas ceiling to **25.72 m/Ø185** (doubly confirmed). LODs @20 m, 10⁻⁴ NEA: CH₄ 129 ppb, NH₃ 92 ppb, H₂ 0.17–0.31 %v (≈5 % LEL — a usable leak alarm; tens of ppm with WMS at 10⁻⁶). Lasers/detectors specced per gas. Note: our 1653.7 nm line is 2ν₃ R(3), not R(4). | [multigas.md](multigas.md), `figures/trigas_matrix.png` |
| "Compare the volume of the disc... toroidal cells are supposed to be low volume" | Dedicated half-inch (CM127) family: flight-robust 7.54 m/Ø122/**40 mL** (PVR 190 m/L) and — with a 0.8 mm collimator (decision needed) — **9.11 m/Ø129/75 mL at 90.8 %** (2.3× IRcell-S4 path). Active-tier showcase: 19.3 m/Ø93/**37 mL** = PVR 518 m/L (4× best commercial). Gas exchange 1–9 s pumped, ~25 ms open-flow. | [low_volume_menu.md](low_volume_menu.md), `figures/volume_pvr_comparison.png` |
| "Choose the cell window... CaF₂ is too brittle... wedged and angled" | **WW10530-C** (Ø1/2″ UVFS wedged, AR 1050–1700 nm) for NH₃+CH₄; **WW30530-D** (Ø1/2″ **sapphire** wedged, AR 1.65–3.0 µm) for CH₄+H₂. Sapphire vs CaF₂: ~10× hardness, ~12–19× rupture strength, ~4–6× fracture toughness. 30 arcmin wedge + 3–5° mount: ghost walk-off ≈30× beam divergence; residual FSR ~1 cm⁻¹ = fittable baseline. | [window_selection.md](window_selection.md) |
| "Holed mirrors vs entry/exit from sides" | The hole is a transverse-selective aperture; a side slot selects only azimuth and leaks the beam at its first return (N chords). Side entry caps the Ø180 ring at 2.3 m; the hole is worth exactly k = 9–19×. Side gaps are geometrically available (1.7–12.7 mm) — the objection is optical, not mechanical. | [entry_exit_comparison.md](entry_exit_comparison.md) |
| "Design in Fusion 360... 3D printing or CNC... weight and vibration... construction tolerance... $200 printed cell" | Parametric CAD (STEP for Fusion 360 + STL) generated from the verified design rows for 4 housings. Process-mapped Monte-Carlo: dense designs need precision CNC; the sparse 20.4 m/15.3 m designs complete 100 % even on standard CNC / printed+machined seats (one trim). A fully printed cell fails three ways (accuracy, CTE+moisture, lid modes 330–670 Hz inside the rotor band) — and one-off CNC Al costs the same as a good print ($250–600). Masses 0.9–1.3 kg pocketed; Al lid modes 1.2–2 kHz (above band); dampers outside + rigid inside per the flight-proven Empa result. | [manufacturing.md](manufacturing.md), [cad/](cad/), `figures/construction_tolerance.png` |
| (implied) "will it survive operation?" | Vibration-to-signal budget (elastic ring tilt 0.01–0.1 µrad/g, margin >10³ — coupling is via launch/detector chain, mitigated in the CAD), polarization audit (launch sagittal: 96–99.9 % eigenaxis purity; no analyzers after the cell), thermal windows ±18–30 K with the trim heater as anti-dew, contamination self-monitoring via T = R^(n−1). | [operational_audit.md](operational_audit.md), [active_tier_requirements.md](active_tier_requirements.md) |

**New results since the draft you read** (all verified): tri-gas ceiling
25.72 m/Ø185; 15.30 m/Ø175 at 89.5 % with 7 spots/mirror (the
budget-build corner); half-inch low-volume family down to 37–75 mL;
converged robust frontier (deeper searches add nothing — the menu is the
architecture's true boundary); mixed-SKU rings (two alternating catalog
ROCs) close re-entrant patterns to nominal 60–69 m in the same envelope,
including combinations where *neither* uniform ROC closes — spot-crowding
currently keeps them at the active/experimental tier (study in
progress).

**Two decisions requested:** (1) the 0.8 mm collimator for the half-inch
mini family (the 1″ menu keeps the 1.3 mm standard); (2) confirm author
list ordering for the revision: S. Varanasi, T. Benoy (co-first), [two
team members], R. Lennox, E. Rebrov.

---

# Round 2 — the five tolerance-framework documents (2026-07-08) → deliverables

*(Source docs archived in [prof_inputs/](prof_inputs/). Everything below
is executed, exact-trace/Monte-Carlo verified, and in paper v2.3.)*

| Your directive | Answer in one line | Where |
|---|---|---|
| "Construction tolerance can be mitigated by alignment — be careful how you present this" | Reframed as the three-tier chain: C_build = capture-range check (recoverable), R_align = residual, D_op = post-alignment drift (the real in-use tolerance). Paper §2.8 states the chain, §6.1/6.4 report as-built survival explicitly as the strictest zero-adjustment reading with the robust vs robust-after-trim tiers separated. | paper §2.8, §6.3–6.4 |
| "Final algorithm: input spot/angle drift must still exit the hole with decent clearance — check this for each of your designs" | Executed per design by per-DOF bisection: capture envelopes 0.37–1.14 mm position, 3.0–18.8 mrad angle — ≥2.2×/5.5× beyond the summed easy+Al-flexure and medium+hybrid drone demand for every menu design. Angle capture is 1–2 orders above demand (re-entrance tolerates tilt; position drift moves the pattern ~1:1 toward the rim). | [capture_envelope.md](capture_envelope.md), paper §6.3 + Fig. 13 |
| MC yield > 99.9 % for drone/product | 5000-trial composed-vector MC (uniform inside R_align + D_op, per mirror + launch chain): tri-gas 25.7 m, sparse 15.3 m and two-inch 19.0 m pass 5000/5000 (Wilson LB 99.92 %) on the Al-flexure architecture; H2/mini/compact at field grade 99.3–99.7 %; boundary designs 92–96 % (as expected of ceilings). | [mc5000_drone_yield.csv](mc5000_drone_yield.csv), paper §6.3 Table 9 |
| "Choose one material combination for drone; no Ti/Invar; aluminium reasonable" | **Aluminium 6061 monolithic ring** (drone baseline) — meets the product criterion without exotic metals; the one soft axis (common-mode ring-radius drift) is the thermal mode, governed by trim law + thermal window, not by CTE upgrades. | [materials_decision.md](materials_decision.md) |
| "Generic low-cost design capable of 3D printing with plastic/PEEK" | **Hybrid printed shell + machined Al mirror cartridge** (plastic never defines an optical datum): 33–46 % structure-mass saving, 6 mm CF-PA12 lids ≥674 Hz, carried best by the sparse two-inch 19.0 m design at 95.0 % hybrid drone yield (research grade; product grade in plastic needs CF drift or a relaxed-clearance generation). CAD shipped for hybrid 19m-2inch + 14 cm. | [materials_decision.md](materials_decision.md), [hybrid_materials.csv](hybrid_materials.csv), [cad/](cad/) |
| "Implement the COMSOL ray-tracing validation protocol — no experiment needed; this will easily be a paper" | Full package shipped: per-design mirror/launch geometry CSVs in platform coordinates, perturbation envelopes, the protocol's step-7 worst-case run log executed natively (333 runs — reference answer sheet for COMSOL to reproduce), and a chief-ray comparison harness with the same <10 µm criterion the Optiland cross-check met at 0.000 µm. Worst-case finding: the only recurring coherent failure is d_ax = uniform ring-radius shift = the thermal breathing mode (governed, not random). | [comsol_validation_package.md](comsol_validation_package.md), [comsol/](comsol/), `compare_comsol.py` |

**Resolved this round:** co-authors Naman Shreyas Rindani + Ayachi
Padmanabh Mishra (IITD-AD) are in the author block; Lennox → Eblana
Photonics; affiliation 2 → Warwick (department to confirm).
