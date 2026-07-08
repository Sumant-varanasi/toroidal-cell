# Low-volume TMPC family — half-inch (CM127) mirrors, Ø90–130 mm

*(Answers the professor's point that "toroidal cells are supposed to be
low volume cells for H2 and methane leak measurements" with a dedicated
design family, 2026-07-08. Search: `search_drone20m.py` with
`TMPC_FAMILY=half_inch`, classes Ø90–130.)*

Half-inch Thorlabs protected-gold concave mirrors (CM127-xxx-M01, ~$50
each, 5.7 mm clear-aperture radius) shrink the ring — and the gas volume
— by roughly 4× against the 1″ family. The full search + 100-trial
Monte-Carlo tiering gives:

## The verified low-volume menu

| design | mirrors | OPL | T @0.999 | envelope | V_min | PVR | tier |
|---|---|---|---|---|---|---|---|
| **mini leak-sniffer** | 14 × CM127-050 (ROC 100) | **9.11 m** | **90.8 %** | Ø129 | 75 mL | 121 m/L | **flight-robust as-built** (with 0.8 mm hole — see below) |
| smallest robust | 16 × CM127-050 | 7.54 m | 54.9 %* | Ø122 | **40 mL** | **190 m/L** | flight-robust as-built (1.3 mm hole) |
| PVR showcase | 14 × CM127-050 | **19.31 m** | 64.7 % | **Ø93** | **37 mL** | **518 m/L** | active alignment (in-situ trim) |
| near-misses | CM127-050 ×16 n=112 (7.95 m Ø98, 89.5 %), ×14 n=98 with 1.3 mm hole (9.11 m) | | | | | | fail 100-trial MC by 1 percentage point of spot-merge trials |

*the 7.54 m row's throughput includes an exit-truncation loss in the
as-searched launch; a mode-matched relaunch recovers most of it — treat
54.9 % as the floor.

## Where this sits against the commercial low-volume cell

| | IRcell-S4 (best commercial small cell) | mini leak-sniffer (ours) | PVR showcase (ours) |
|---|---|---|---|
| OPL | 4.03 m | **9.11 m (2.3×)** | 19.31 m (4.8×) |
| envelope | Ø106 × 32 mm | Ø129 × ~22 mm | **Ø93 × ~22 mm** |
| gas volume | 31 mL | 75 mL | **37 mL** |
| PVR | 130 m/L | 121 m/L | **518 m/L** |
| throughput | not published (~60 % broadband) | **90.8 %** | 64.7 % |
| mirrors | custom diamond-turned monolith | **catalog, ~$50 × 14** | catalog |
| build class | commercial product | flight-grade CNC, as-built | needs in-situ trim |

The honest reading: at *equal build effort* (passive, as-built) we more
than double the commercial small cell's path at matched PVR with
catalog parts; the 4× PVR / 4.8× path corner exists but only with
active alignment (ring-temperature + launch trim) — the same tier that
holds our 38.6 m 1″ record.

## The hole is the half-inch bottleneck (collimator decision for Dr. Benoy)

The project-standard 1.3 mm beam / 1.3 mm hole occupies a third of the
half-inch aperture diameter (exclusion zone ≈ Ø4 mm of 11.4 mm), which
is what killed several otherwise-robust designs (hole-clearance p05
between −0.04 and −0.6 mm). A **0.8 mm beam + 0.8 mm hole** — i.e. a
smaller collimator than the current spec, still trivially available as
a catalog fiber collimator — was re-searched (`TMPC_W0/TMPC_HOLE_R` env
overrides) and **promotes the 9.11 m / Ø129 / 90.8 % design to
flight-robust as-built** (hole clearance p05: −0.04 → +0.52 mm). The
19.3 m Ø93 star does *not* benefit: its limit is spot crowding on the
small aperture, not the hole.

**Decision needed:** approve the smaller collimator for the half-inch
family only (the 1″ menu keeps the 1.3 mm standard; both use the same
fiber-DFB source, different collimation package).

## Gas exchange (the point of low volume on a drone)

| design | V_min | τ @0.5 SLM | @1 SLM | @2 SLM | open-flow transit* |
|---|---|---|---|---|---|
| 9.1 m mini Ø129 | 75 mL | 9.0 s | 4.5 s | 2.3 s | ~26 ms |
| 7.5 m Ø122 | 40 mL | 4.8 s | 2.4 s | 1.2 s | ~25 ms |
| 19.3 m Ø93 showcase | 37 mL | 4.4 s | 2.2 s | 1.1 s | ~19 ms |
| (1″ drone_14cm, for scale) | 200 mL | 24 s | 12 s | 6 s | ~28 ms |

*open ring (lids slotted/mesh, IRcell-S-style flow-through) at 5 m/s
drone airspeed — the cell clears in one body-length of flight, i.e.
plume mapping at the flight-controller rate; the pumped numbers are for
the sealed configuration.

## Physics notes

* Spot sizes do **not** shrink with the mirror: w is set by chord length
  and ROC, so the half aperture crowds patterns ~4× harder — dense
  patterns (k ≥ 11) die at build tolerances that the 1″ family shrugs
  off. The robust half-inch designs are all sparse (k = 5–7).
* Packing floor: Ø93 envelope at N = 14 (found), D90 class returned
  zero feasible — Ø93 is the geometric floor of the catalog half-inch
  chord-skip family with this hole.
* Menus: [robust_menu_halfinch_flight.csv](robust_menu_halfinch_flight.csv),
  [robust_menu_minihole_flight.csv](robust_menu_minihole_flight.csv)
  (+ research-grade variants); raw searches in `results_halfinch*/`.
