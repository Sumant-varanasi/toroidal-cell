# Toroidal Multipass Cell (TMPC) Design Package

## Folder structure
```
toroidal-cell/
  tmpc/           library (imported by scripts)
  analysis/       runnable scripts
  results/        outputs (CSVs and PNG plots)
```

## Setup
```
pip install numpy scipy matplotlib optiland
```

## Run from the project root
```
cd toroidal-cell
python analysis/01_baseline.py
python analysis/02_sweeps.py
python analysis/03_optimize.py
python analysis/04_generate_csvs.py
python analysis/05_optiland_validate.py
python analysis/06_3d_visualisation.py
python analysis/07_chord_skip_comparison.py
```

## Scripts at a glance
- 01_baseline.py              — v1 reference design
- 02_sweeps.py                — parameter sweeps
- 03_optimize.py              — SciPy + GA + PSO optimisation
- 04_generate_csvs.py         — Phase 6 CSV deliverables
- 05_optiland_validate.py     — independent validation against Optiland
- 06_3d_visualisation.py      — 3D figures of the cell, spots, one-mirror close-up
- 07_chord_skip_comparison.py — perimeter-walk vs diagonal-cross geometry (NEW)

## NEW: chord_skip parameter

The `TMPCConfig` now takes a `chord_skip` parameter that controls which
mirror the beam hops to at each bounce:

```python
cfg = TMPCConfig(N=8, R=50e-3, H=40e-3, M_halfLaps=66, w0=1e-3,
                 chord_skip=3)   # diagonal crossings instead of perimeter walk
```

For N=8:
- `chord_skip=1` (default) — beam walks the perimeter, OPL = 20 m, AOI = 67.5°, vol = 23%
- `chord_skip=3`           — beam crosses diagonally, OPL = 49 m, AOI = 22.5°, vol = 81%

The diagonal pattern matches Tuzson/Graf/Chang toroidal-MPC literature,
samples the cell interior properly, and reduces astigmatism dramatically.
See `results/plots/fig_chord_skip_topdown.png` and
`results/plots/fig_chord_skip_metrics.png`.
