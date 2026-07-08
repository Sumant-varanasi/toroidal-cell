# Dr. Benoy's tolerance-framework documents (2026-07-08)

*(Five .docx attachments from the "Draft paper of Sumant (Toroidal cell)" and
"Final algorithm" email threads, Thomas.Benoy@warwick.ac.uk → Sumant, cc Naman
Rindani + Ayachi Mishra. Full extracted text in this folder, one .txt per
document. Originals in Sumant's mailbox / `C:\Users\ASUS\Downloads\*.docx`.)*

## The five documents

| file | sent | covering note |
|---|---|---|
| `multipass_gas_cell_tolerance_analysis_alignment_regimes` | 08 Jul 01:04 | "Check this for each of your designs." |
| `multipass_gas_cell_tolerance_analysis_post_alignment_drift` | 08 Jul 17:16 | "You can mitigate manufacturing tolerance by alignment to some extent. So be careful when you present this in your papers." + find a generic low-cost 3D-printable plastic/PEEK design; pick one material combination for drone; no Ti/Invar (expensive), aluminium reasonable. |
| `multipass_gas_cell_full_integrated_comparison` | 08 Jul 20:00 ("Final algorithm") | "Try to include this model into your papers. Basically, for an input spot pattern drift or angle drift in the beam exits the second mirror hole with decent clearance it's good !! This is what you have also modelled I assume." |
| `multipass_gas_cell_tolerance_ieee_style_paper` | 08 Jul 20:11 | "This is same as before but in paper format. Adapt this justification into your papers." |
| `comsol_ray_tracing_validation_protocol_mirror_only` | 08 Jul 20:52 | "This is the final comsol ray tracing validation protocol you need to implement to validate your drone ray tracing model. No need experiment. This will easily be a paper. No need to model the cell body." |

All five are written for the two-concave-mirror Herriott geometry at L = 300 mm,
but the covering notes instruct us to apply the *framework* to every toroidal
design and adapt the justification into our paper.

## The framework (his "final algorithm")

Three-tier error budget, six-DOF vectors `v = [dx,dy,dz,dθx,dθy,dθz]`:

1. **Construction tolerance** = manufacturing/fixing accuracy `C_build`.
   **Recoverable by alignment** if within the alignment capture range → it is a
   *capture-range / build-feasibility check*, NOT part of final in-use drift.
2. **Alignment tolerance** = residual after the user aligns, `R_align =
   F_resolution × F_ease × F_user × F_feedback`. Three regimes (Easy = monolithic
   /dowel-pinned + visible feedback; Medium = lockable cartridge/shimmed; Hard =
   free-space folding mirrors / blind). COMSOL-sweep residual vectors (Table III
   of the protocol): Easy 0.02 mm / 0.05 mrad, Medium 0.05 mm / 0.15 mrad, Hard
   0.12 mm / 0.40 mrad (dx / dθx,y per axis).
3. **Operational drift** `D_op` = post-alignment thermal + vibration + pressure +
   thermal-cycling. **This is the dominant real in-use tolerance.**

Final in-use vector `T = R_align + D_op` (construction excluded when
recoverable). Metrics kept separate: `Pxy = √(dx²+dy²)` (mm),
`Θxy = √(dθx²+dθy²)` (mrad); combined only for clearance checks:
`X_combined = Pxy + L·Θxy` (0.3·Θ at L = 300 mm). Acceptance = the beam still
exits the exit hole with decent clearance under input spot/angle drift.

**Destination envelopes** (max total drift the design must accommodate;
ordered drone > field > lab because environment dominates):
lab 0.20 mm / 0.67 mrad · field 0.35 mm / 1.17 mrad · drone 0.60 mm / 2.0 mrad
(equivalent input spot at L = 300 mm — for our cells convert via our own
launch-to-exit sensitivity, not the 0.3 factor).

**Drone operational-drift vectors he assigns per mount architecture**
(max post-alignment, drone row, protocol Table VI — these are directly
comparable to our Monte-Carlo σ's):

| architecture | dx,dy (mm) | dz (mm) | dθx,y (mrad) | combined spot (mm) |
|---|---|---|---|---|
| Al isostatic flexure | 0.050 | 0.080 | 0.15 | 0.134 |
| Ti flexure cartridge | 0.045 | 0.070 | 0.13 | 0.119 |
| Invar insert | 0.040 | 0.060 | 0.10 | 0.099 |
| Hybrid plastic body + Al mirror cartridge | 0.120 | 0.180 | 0.40 | 0.339 |
| Injection-moulded + inserts | 0.250 | 0.350 | 1.00 | 0.778 |
| CNC PEEK/Delrin | 0.300 | 0.400 | 1.20 | 0.933 |
| 3D-printed plastic (PA12/PLA) | 0.700 | 0.900 | 3.00 | 2.263 |
| Bosch rail / O-ring datum / ext. kinematic | — | — | — | not recommended |

**COMSOL protocol** (10 steps): mirror-only model (Ray Optics Module, specular
mirrors + aperture/hole masks, no cell body), nominal trace → input sweeps
(x_in, y_in, θx, θy) → capture-range check with C_build → apply R_align regime →
apply D_op vectors per environment/material → per-DOF worst-case sweeps →
Monte-Carlo (250 screen / 1000–5000 final) → pass/fail. **Yield thresholds:
>99 % lab, >99.5 % field, >99.9 % drone.** Run-log template given (Table VII).
Materials/CTE table supplied (Al 23, SS 16, Ti 8.6, Invar 1.5, PEEK 45–50,
PA12 100–160 ppm/K; EPO-TEK 353ND three-dot bonding only; O-ring = seal only).

## What this changes for the TMPC paper (mapping to our assets)

1. **Reframe our construction-tolerance section.** Our process-grade MC treats
   as-built error as final — in his framework that is the *zero-adjustment
   lower bound* plus a *capture-range check*, and the honest headline in-use
   number is `R_align + D_op`. Our "flight-grade" MC σ's (0.05 mm / 0.1–0.2
   mrad) sit almost exactly on his drone Al-flexure drift vector — cite his
   envelope table as the source and add the (small) pressure + cycling terms.
   Present per design: (a) works-as-built grade (no alignment, our current MC),
   (b) capture-range check vs alignment regime, (c) in-use robustness under
   `R_align + D_op`. His caution "manufacturing tolerance can be mitigated by
   alignment — be careful how you present this" is aimed exactly at claims like
   "fails at FDM grade": FDM *construction* is recoverable by one alignment
   session; it is FDM *operational drift* (creep/CTE) that kills drone use.
2. **Input-drift capture envelope per design** ("check this for each of your
   designs"): compute max input spot offset and max input angle drift that
   still exits the hole with clearance — one number pair per design vs his
   destination envelopes. Our launch-drift MC already samples this; a dedicated
   per-DOF sweep makes it a table/figure his model asks for.
3. **99.9 % drone yield**: re-run flagship MC at 5000 trials (400-trial runs
   cannot resolve 99.9 %).
4. **Materials decision** (his explicit ask): one combination for drone =
   **aluminium body + aluminium isostatic-flexure mirror seats** (no Ti/Invar —
   expensive); low-cost route = **hybrid plastic (PA12/PEEK) outer body +
   aluminium mirror-cartridge ring**; all-plastic datum only for lab/prototype.
   Our Ø182 two-inch N=8 sparse design is the natural "generic low-cost
   3D-printable" candidate — largest clearances in the menu; verify it against
   the hybrid drift vector (0.12 mm / 0.40 mrad).
5. **COMSOL validation package** replaces the lab experiment for the
   ray-tracing-validation paper ("No need experiment... easily be a paper"):
   port the 10-step protocol to the toroidal N-mirror ring (our
   `MirrorPerturbation` machinery already implements every step natively),
   prepare COMSOL parameter tables + comparison harness (import COMSOL spot
   CSV → diff vs our tracer, like the Optiland cross-check at 0.000 µm).
6. **Author list resolved**: Varanasi¹, Benoy²(co-first,*), **Naman Shreyas
   Rindani¹, Ayachi Padmanabh Mishra¹**, Lennox³ (Eblana Photonics), Rebrov²
   (Warwick). Benoy now writes from Warwick — affiliation² set to Warwick,
   department to confirm (was Aston).
7. **Timeline** (from the 07-07 review mail): three papers by end of July,
   Q1-journal target; Warwick lab window 21–31 July still reserved for spot-
   pattern validation via the components-ordering thread (kinematic mounts,
   fibre source available; we supply mirrors + mounts) — but the COMSOL route
   supersedes the *need* for experiment in the validation paper.
