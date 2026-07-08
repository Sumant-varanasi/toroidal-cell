# Mixed-SKU rings: two alternating catalog ROCs in one cell

*(User-requested exploration, 2026-07-08: "different combinations of
mirrors". Tools: `mixed_sku_explore.py` (analytic unit-cell prescreen +
exact-trace refinement) and `mixed_sku_pass2.py` (separation-aware
re-optimization). Data: [mixed_sku_results.csv](mixed_sku_results.csv),
[mixed_sku_pass2.csv](mixed_sku_pass2.csv).)*

## The idea

Every published chord-skip/toroidal design — and our whole menu — uses
one mirror type for the full ring. With even N and odd skip s the beam
alternates A,B,A,B... between two mirror populations, so a two-SKU ring
is a legal re-entrant system whose transverse phase per two bounces
follows the alternating unit cell

    cos θ₂ = ½ tr[ M(f_B) P(L) M(f_A) P(L) ],   per plane,

giving the architecture a **second closure knob**: (N, s, k)
combinations that no single catalog ROC can close may close for a pair.
(The formula reduces exactly to the uniform cos 2θ₁ for f_A = f_B —
verified against the known drone_20m closure.)

## What the exploration found

27 combos (N ∈ {12, 14, 16} × nine adjacent/wide catalog ROC pairs),
analytic 2 µm R_ring prescreen (the closure valleys are ~5 µm wide —
coarser scans alias at high k), exact Nelder-Mead refinement of launch
and ring at each analytic root:

* **Mixed rings close, exactly.** Dozens of candidates reached exit
  miss = 0.000–0.01 mm with clean hole clearance (0.3–2.5 mm) at
  nominal paths of **30–69 m** — far beyond the uniform architecture's
  38.6 m geometric ceiling in the same ≤Ø190 envelopes.
* **Several of the longest closures are mix-only.** Uniform
  counterfactual (same N, s, k, ±1.5–2 mm R window): the four longest
  (68.9, 68.4, 64.7, 64.6 m) close for *neither* ROC alone.
* **Spot crowding is the binding constraint.** All those k = 19–33
  patterns pack 19–33 spots per 1″ mirror; pass 1 landed at separation
  margins of −0.5…−2.1 mm, and the separation-aware pass 2 (extended to
  the full top-40, 43.7–68.4 m) recovered them to −0.3…−0.7 — except
  exactly one. On 1″ apertures the feasible mixed design is a singular
  point in the closure map, not a family.

## The verified design: 51.7 m in Ø180 with catalog mirrors

| parameter | value |
|---|---|
| ring | N = 12, skip 5, R_ring = 71.928 mm, envelope Ø180 |
| mirrors | alternating **CM254-250-M01 (ROC 500)** / **CM254-375-M01 (ROC 750)**, 6 + 6 |
| pattern | k = 31 spots/mirror, **372 chords**, OPL **51.66 m** |
| throughput | 69.0 % at R = 0.999 (T = R³⁷¹) |
| checks | exit miss 2.3 µm; hole clearance +2.46 mm; worst-pair separation **+0.03 mm**; aperture clear |
| launch | w₀ = 0.333 mm at 0.64 × half-chord; tilts 30.8/40.1 mrad |
| counterfactual | k = 31 closure **does not exist** for uniform ROC 500 nor ROC 750 in the R window — mix-only |

Honest tier placement: the +0.03 mm worst-pair margin is a hair — build
error walks spots by ~0.3–0.5 mm even at flight grade, so this is an
**active-alignment-tier** design (same tier as the uniform 38.6 m
record) and CH₄/NH₃-only (H₂'s +13 % spot growth erases the margin).
Within that tier it is the new architecture record: **51.7 m vs 38.6 m
uniform (+34 %) in the same Ø180 envelope, still all-catalog parts**
(one SKU drilled, two SKUs purchased).

## Why the others stay crowded (and what would free them)

At k = 29–33 the pattern density on a 1″ aperture is at the packing
limit: mean nearest-neighbour spacing approaches 2w and the Lissajous
worst pair goes negative. The levers, in order of leverage:

1. **2″ mirrors** — the same mixed closures on CM508 apertures double
   every separation; the 55–69 m closures found here would clear by
   millimetres (consistent with the established "2″ beats the 39 m
   ceiling" note — mixing multiplies that route).
2. **Separation-in-the-loop from the start** — pass 2 bolted separation
   onto converged closures; a mixed-native search with the walk-budget
   objective (as in the uniform v8 harness) would trade a few metres
   for margin the way drone_20m's family did.
3. **Lower-k mixed hunts** — low-k mixed closures are sparse in the
   R-window (that scarcity is itself a finding: mixing shifts θ₂ enough
   that k ≤ 13 roots mostly leave the catalog ring-radius range).

## Take-away for the paper

Mixed-SKU rings are a genuinely new degree of freedom for re-entrant
ring cells: the alternating unit cell closes patterns single-ROC rings
cannot, extending the verified nominal ceiling of the catalog-parts
architecture from 38.6 m to **51.7 m in Ø180**, with a clear,
quantified path (aperture, margin-aware search) to making such designs
build-robust. Even as an active-tier result it strengthens the paper's
central claim: chord-skip + closure-tuning turns a pile of catalog
mirrors into a design space, and that space is larger than one SKU.
