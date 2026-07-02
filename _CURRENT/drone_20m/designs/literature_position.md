# Literature position — verified drone TMPC designs (July 2026)

Update of the June literature comparison: the June numbers were
unconstrained-simulation results at an assumed R = 0.999; everything in the
"this work" columns below is a **fully verified catalog-mirror design**
(exact 3-D ray trace, all physical checks, Optiland cross-validated,
Monte-Carlo toleranced) at the realistic R = 0.985 gold coating.

| Metric | Tuzson 2013 | Graf 2018 | Chang 2020 (3-layer) | Dong 2016 (non-toroidal) | **This work `drone_16cm`** | **This work `drone_20m`** | **This work `drone_25m`** |
|---|---|---|---|---|---|---|---|
| Cell diameter | ~100 mm | — (<200 g) | 100 mm | 170×65×55 mm | **159 mm** | **180 mm** | **180 mm** |
| OPL demonstrated/verified | 4.1 m | 10 m | 10 m (30 m theory) | 54.6 m | **20.6 m** | **20.4 m** | **24.8 m** |
| OPL per cell diameter | 41 | — | 100 | 321* | **130** | 113 | **138** |
| Throughput | — | — | — | — | 7.9 % (R=0.985) | **11.5 %** | 7.1 % |
| Mean AOI | — | — | — | — | 7.1° | 11.3° | 11.3° |
| Mirrors | monolithic diamond-turned | segmented diamond-turned | ring surface | 2 custom spherical | **13 × catalog $74** | **16 × catalog $74** | 16 × catalog |
| Fringe control | — | interference-free folding | masks (<0.5 %) | dense pattern | spot-separation ≥ Σw + 0.42 mm verified | ≥ Σw + 0.36 mm | ≥ Σw + 0.41 mm |
| Alignment DOF | entry angle | fabrication | layer count | mirror alignment | ring radius (machined) + lens focus | same | same |
| Est. optics + housing mass | — | <200 g | — | — | ~700 g | ~790 g | ~800 g |

\* Dong's astigmatic Herriott cell is the strongest compact competitor but
uses custom mirrors and sub-mm-critical two-mirror alignment; the toroidal
ring trades peak OPL density for one-piece machinability and catalog optics.

**Claims supported by this work:**
1. 2× the demonstrated OPL of any published toroidal cell in the ≤180 mm
   class, using only catalog 1″ gold mirrors (~$1000 of optics).
2. The chord-skip parameter (s ≈ N/2) is what buys near-diameter chords at
   7–13° AOI — the geometric core of the result.
3. Re-entrance is engineered, not found: dual-plane phase closure tuned by
   the machined ring radius (~1.2 rad/mm), with a linear ROC-error
   compensation rule (e.g. 0.72 mm ring trim per 1 % ROC error for
   `drone_20m`) that absorbs the catalog ±1 % focal tolerance.
4. Mode-matched injection through a 1.3 mm coupling hole makes the hole
   losses negligible, so throughput = R^(chords−1) exactly — 11.5 % at the
   measured-coating value 0.985 for the 20.4 m design.
5. Fringe safety is a verified geometric property (worst spot pair over all
   mirrors ≥ sum of 1/e² radii + margin), not a post-hoc mask fix.

**Verified boundary of the approach** (N ≤ 16, 1″ catalog mirrors, all
checks): smallest feasible envelope Ø141 mm (13.4 m). Near-misses just
outside: 18.0 m in Ø140 mm fails only by an intermediate spot grazing the
hole by 0.56 mm — an open lever is placing the hole at a different
constellation slot (tangential launch offset).
