# Two-inch family — 8 mirrors, 19 m, and the printability boundary

*(Continuation named in the paper's Discussion, executed 2026-07-08.
Search: `TMPC_FAMILY=two_inch`, N ∈ {7, 8} — the only counts that pack
Ø50.8 mm mirrors under the Ø190 envelope; CM508-series protected gold,
22.9 mm clear-aperture radius. SKU availability to be confirmed at
order time.)*

## The verified designs (flight-grade Monte-Carlo, as-built)

| design | mirrors | chords (k) | OPL | T @0.999 | envelope | MC (flight) |
|---|---|---|---|---|---|---|
| **two-inch long** | 8 × CM508-150 (ROC 300) | 152 (19) | **19.04 m** | **86.0 %** | Ø182 | robust: 100 % completion, sep p05 1.02 mm, hole clear 3.36 mm, walk 0.47 mm |
| **two-inch high-T** | 7 × CM508-500 (ROC 1000) | 105 (15) | 11.61 m | **90.1 %** | Ø187 | robust: 100 %, sep p05 1.03, hole clear 5.39 |
| (nominal only) | 8 × CM508-075 | 184 (23) | 23.76 m | 83.3 % | Ø186 | 97 % completion; separation fails — active tier |

Why they matter: the 19.0 m design delivers drone_20m-class path and
throughput with **half the mirror count (8 pockets to machine, ~US$1.1k
of larger-format optics)** and giant clearances (hole margin 3.8 mm,
aperture margin 10.3 mm nominal) — the simplest long cell in the whole
project.

## The construction-tolerance result (the professor's $200 question, part 2)

Process-mapped Monte-Carlo (same grades as the 1″ study):

| process | 19.0 m completion | verdict |
|---|---|---|
| CNC precision | 100 % | **survives as-built** |
| CNC standard | 100 % | completes; needs the one-time trim |
| printed + machined seats | 100 % | completes; needs trim |
| SLA | 100 % | completes; needs trim |
| MJF/SLS | 100 % | completes; needs trim |
| **FDM (PLA)** | **100 %** | completes; needs trim + fringe caution |

**This is the first design in the project — and, to our knowledge, far
beyond anything published — whose full 152-chord path completes in
every trial at every manufacturing grade including desktop FDM.** The
doubled aperture converts directly into completion robustness. The
honest limits: at the printed grades the *spot bookkeeping* still fails
(pairs wander into each other in a fraction of trials, and the exit
needs the standard ring-trim/launch alignment), so a printed build is
"19 m that reliably folds, one alignment session required, fringe floor
to be verified" — not a fringe-guaranteed as-built instrument. For
scale, the published printed-multipass record is 4.2 m [Anal. Chem.
2020]. A printed 19 m ring at ~$50 of plastic plus $1.1k of mirrors is
a compelling demonstrator and teaching instrument; the drone instrument
remains CNC aluminium.

## Boundary note (recorded for the paper's Discussion)

Under the strict Ø190 cap, 2″ mirrors pack only at N = 7–8, so beating
the 1″ 29.0 m robust ceiling would need k ≥ 21 patterns at pattern
amplitudes where the paraxial prescreen no longer locates the closure
valleys (the max-OPL 2″ hunt refined 27 such candidates; all missed by
1.4–8 mm). "Larger apertures beat the ceiling" therefore holds for
relaxed envelopes (bench cells), while inside the drone envelope the 2″
family's wins are simplicity (7–8 pockets), throughput at length
(86–90 %), and build-grade completion robustness.

## Tri-gas verdict

Both flight-robust designs re-qualify **robust as-built at 1512.2 nm
and at 2121.8 nm** (√λ-scaled Monte-Carlo; the 3.3–5.4 mm hole
clearances absorb the +13 % H₂ spot growth trivially) — the 19.04 m /
8-mirror cell is therefore a full tri-gas member, and on a
parts-count/assembly basis the most practical one in the project.

Files: [robust_menu_twoinch_flight.csv](robust_menu_twoinch_flight.csv),
[construction_tolerance_2inch.csv](construction_tolerance_2inch.csv),
[multigas_twoinch_2121.8nm.csv](multigas_twoinch_2121.8nm.csv),
[multigas_twoinch_1512.2nm.csv](multigas_twoinch_1512.2nm.csv);
spec sheet [spec_D190_19m_2inch.md](spec_D190_19m_2inch.md).
