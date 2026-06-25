# Toroidal Multipass Cell (TMPC) Design Package

Student 3 internship project — Aston / IIT Delhi Abu Dhabi.

## Folder structure

```
toroidal-cell/
  tmpc/                  ← library (imported by the scripts; don't run directly)
  analysis/              ← runnable scripts (run from this folder's PARENT)
  results/               ← outputs from previous runs (CSVs + PNG plots)
    csv/
    plots/
```

## One-time setup

```
pip install numpy scipy matplotlib optiland
```

(Optiland is only required for `05_optiland_validate.py`.)

## How to run

Always run from the project root (`toroidal-cell/`), NOT from inside `analysis/`:

```
cd toroidal-cell
python analysis/01_baseline.py
python analysis/02_sweeps.py
python analysis/03_optimize.py
python analysis/04_generate_csvs.py
python analysis/05_optiland_validate.py
```

Each script writes into `results/csv/` and `results/plots/`, overwriting whatever was there before.

## What each script does

| Script | Purpose | Runtime |
|---|---|---|
| `01_baseline.py` | Trace the v1 reference design. Produces the headline numbers and figures. | ~5 s |
| `02_sweeps.py` | Sweep one parameter at a time (N, R, ROC, R_ring, w0). | ~30 s |
| `03_optimize.py` | Run three optimisers (SciPy, GA, PSO). | ~1-2 min |
| `04_generate_csvs.py` | Write out the Phase 6 CSV deliverables. | ~5 s |
| `05_optiland_validate.py` | Independent validation against the Optiland package. | ~10 s |

## Pre-computed outputs

`results/csv/` and `results/plots/` already contain outputs from a previous run, so
you can browse them without running anything.

## Key figures to look at first

- `results/plots/fig_topdown_v1.png` — the cell geometry from above
- `results/plots/fig_beam_evolution_v1.png` — beam size growing along the spiral
- `results/plots/fig_throughput_v1.png` — power decay
- `results/plots/fig_reflectivity_budget.png` — why R_ring=0.999 is required
- `results/plots/fig_optiland_validation.png` — proof the tracer is correct

## Key CSVs to look at first

- `results/csv/baseline_summary.csv` — the v1 headline numbers
- `results/csv/optimization_summary.csv` — best results from each optimiser
