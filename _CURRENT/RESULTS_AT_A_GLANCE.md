# Results at a glance — verified designs, lengths, and costs

One-page outline of the project's verified results (July 2026). Every number
below comes from the exact 3-D ray trace + Monte-Carlo verification in
[`drone_20m/`](drone_20m/README.md); costs are catalog / vendor-quote figures
from the [build package](drone_20m/designs/build_package.md) and the
[manufacturing study](drone_20m/designs/manufacturing.md).

## 1. The design menu — path length vs size vs cost

| design (preset / spec) | path length (OPL) | envelope | throughput @ R=0.999 | mirrors | optics cost | build tier |
|---|---|---|---|---|---|---|
| **Max path** `drone_29m` | **28.99 m** | Ø183 mm | 76.6 % | 12 × CM254-750 | ~$888 | flight (glued, 0.1 mrad) |
| **Tri-gas flagship** (26 m spec) | **25.72 m** | Ø185 mm | 83.9 % | 16 × CM254-200 | ~$1,184 | flight; robust at CH₄+NH₃+H₂ |
| Long `drone_25m` | 24.77 m | Ø180 mm | 83.9 % | 16 × CM254-200 | ~$1,184 | flight |
| H₂-native (2121.8 nm) | 23.83 m | Ø174 mm | 83.9 % | 16 × CM254-200 | ~$1,184 | flight @ H₂ |
| **Compact star** `drone_14cm` | 20.66 m | **Ø141 mm** | 81.6 % | 12 × CM254-500 | ~$888 | flight |
| **Headline standard build** `drone_20m` | **20.38 m** | Ø180 mm | 86.7 % | 16 × CM254-150 | ~$1,184 | **standard lab** (kinematic, 0.5 mrad) |
| Two-inch sparse | 19.04 m | Ø182 mm | 86.0 % | 8 × CM508 | ~$1,100 | flight; survives even desktop FDM print |
| Balanced | 16.60 m | Ø160 mm | 86.8 % | 13 × CM254-150 | ~$962 | flight |
| Budget sparse (7 spots/mirror) | 15.30 m | Ø175 mm | **89.5 %** | 16 × CM254-100 | ~$1,184 | flight; 100 % completion down to SLA print |
| Small | 14.85 m | Ø133 mm | 82.8 % | 10 × CM254-150 | ~$740 | flight |
| Small max-T | 13.64 m | Ø143 mm | 87.7 % | 12 × CM254-250 | ~$888 | flight |
| Half-inch mini | 9.11 m | Ø129 mm / **75 mL** | **90.8 %** | 14 × CM127-050 | ~$700 | flight (0.8 mm mini-collimator) |
| Half-inch low-volume | 7.54 m | Ø122 mm / **40 mL** | 54.9 % | 16 × CM127-050 | ~$800 | flight; PVR 190 m/L |

Ceilings beyond the passive menu (active-alignment tier, ~$400–700 of
heater + piezo + quad detector): **38.6 m in Ø169 mm** single-SKU, and
**51.7 m in Ø180 mm** with the mixed-SKU alternating ring (nominal,
verified trace).

Context: the published toroidal record in this size class is ~10 m
demonstrated; the closest commercial cell (IRsweep IRcell-S15) folds
15.12 m into Ø194 mm using a diamond-turned monolith — the 20.38 m
headline design beats that by +35 % path in a smaller disc using ~$1.2k
of catalog mirrors.

## 2. What a cell costs to build

**Optics + housing subtotal ≈ US$2.3–2.9k per cell, excluding lasers**
(full BOM in [build_package.md](drone_20m/designs/build_package.md)):

| item | cost |
|---|---|
| Concave gold mirrors (Thorlabs catalog) | 1″ ~$74 ea · ½″ ~$50 ea · 2″ ~$140 ea → $700–1,184/set |
| Drilling the coupling hole in mirror M0 | ~$80 (service) |
| Ring housing, Al 6061 CNC (standard tol.) | $250–600 one-off (≈half offshore) |
| Ring housing, precision CNC + lapped seats | $600–1,200 (required for dense 204-chord designs) |
| Hybrid printed body + machined seats | $150–350 |
| Polymer print only (SLA / MJF / FDM) | $60–150 / $80–250 / $20–60 (sparse designs only) |
| Wedged window | ~$90 (UVFS, CH₄+NH₃) / ~$150 (sapphire, CH₄+H₂) |
| Fibre collimator + mode-match lens | ~$120 (or $400 reflective OAP, athermal all-λ) |
| Detector | ~$150 InGaAs (CH₄/NH₃) / ~$250 extended InGaAs + lens (H₂) |
| Heater + RTD trim loop, dampers, fittings, adhesive | ~$210 |
| DFB laser (the dominant cost) | ~$2k CH₄ (1654 nm) · ~$2k NH₃ (1512 nm) · ~$4k H₂ (2122 nm) |
| Active-alignment upgrade (Tier 3) | +$400–700 → buys 25.7 → 38.6 m (+50 % path) |

Cost findings worth quoting: at one-off quantities **CNC aluminium costs
the same class as a good polymer print** ($250–600 vs $80–250), and a
fully-printed $200 cell fails three independent ways (as-printed accuracy,
CTE/moisture drift, lid modes inside the rotor band). The honest "$200
cell": the sparse 144-chord design in a hybrid printed body — as a lab
demonstrator. The drone instrument is a $250–1,200 CNC Al part either way.

## 3. Headline performance numbers

- **20.38 m** in Ø180 mm at **86.7 %** throughput (R = 0.999), 144 chords —
  builds with standard lab tolerances; **zero clipping in 400 MC trials**,
  OPL 20.35 ± 0.03 m, spot-walk p95 = 0.89 mm vs 1.46 mm hole clearance.
- **Detection limits** at 20.4 m, 10⁻⁴ NEA: **129 ppb CH₄, 92 ppb NH₃**,
  0.17–0.31 %v H₂ (tens of ppm with WMS at 10⁻⁶).
- **Thermal window**: `drone_20m` holds all checks over **±26 K** on a plain
  6061 ring; ROC-error compensation is a linear ring trim (0.72 mm per 1 %).
- **Gas volume**: 200–330 mL for the 1″ menu; 40–75 mL for the half-inch
  family (path-per-volume up to 190 m/L robust, 518 m/L active-tier).
- Mass: Ø180 Al housing ~1.1–1.3 kg pocketed (1.7 kg solid), lid first
  mode 1.24 kHz — outside the 60–700 Hz rotor band.

Sources: [design menu](drone_20m/README.md) ·
[feature frontier](drone_20m/designs/feature_frontier.md) ·
[manufacturing & cost study](drone_20m/designs/manufacturing.md) ·
[BOM / build package](drone_20m/designs/build_package.md) ·
per-design spec sheets in [designs/](drone_20m/designs/) (each carries its
own optics-cost line).
