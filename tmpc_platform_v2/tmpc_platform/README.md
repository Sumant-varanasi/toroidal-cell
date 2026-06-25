# TMPC Optimisation Platform

Research-grade physics-informed optimisation platform for **Toroidal Multipass Cells (TMPC)** for laser absorption spectroscopy at 1.654 µm (CH₄ line).

This is the foundation you build on for the IITD-Abu Dhabi / Aston internship deliverable. It implements:

- Full 3D ray tracing on toroidal surfaces (exact reflection law, Newton-iterated quartic intersection)
- Gaussian beam propagation with separate tangential/sagittal ABCD matrices
- Loss budget: reflectivity, clipping, aperture truncation, hole truncation
- Chord-skip geometry (your v1 discovery, generalised)
- Stability and re-entrance analysis
- Sobol-sampled dataset generator (parallel, 1k–100k+ configs)
- 5 surrogate model families: RandomForest, XGBoost, LightGBM, GP, NeuralNet
- Physics-informed neural network (PyTorch) with monotonicity constraints
- Stacking ensemble meta-learner
- Bayesian optimisation (scikit-optimize) and NSGA-II multi-objective (pymoo)
- Active-learning loop (uncertainty-driven querying)
- SHAP explainability + Sobol global sensitivity indices
- Publication-grade plots (spot patterns, Pareto fronts, importance bars, beam evolution)

---

## Quick start

```bash
# 1. install deps (Windows PowerShell, in your .venv)
pip install -r requirements.txt
pip install streamlit plotly   # for the interactive viewers

# 2. one-shot full run (small for first try)
python -m tmpc_platform.scripts.run_all --n 500

# 3. full research run (slow; uses all cores)
python -m tmpc_platform.scripts.run_all --n 20000 --bo-calls 100 --ga-gen 60

# 4. printable physics summary of the best designs
python -m tmpc_platform.scripts.summarise_best --top 5

# 5. interactive dashboard (live sliders, opens in browser)
streamlit run app.py

# 6. Plotly notebook for paper figures
jupyter notebook notebooks/explore.ipynb
```

---

## Interactive viewers

### Streamlit dashboard — `streamlit run app.py`

Live sliders for N, R_ring, R_t, R_s, chord_skip, w0, wavelength, input tilt, etc. As you drag, the right pane updates:

- Top metric strip: bounces, OPL, throughput, vol. utilisation, max beam w, stability g², AOI mean, AOI max, chord length, clipped y/n
- Rotatable 3D bounce trajectory with colour-coded bounce index
- Per-bounce AOI line plot
- Tangential / sagittal beam radius evolution vs aperture limit
- Loss-mechanism bar chart (reflectivity / clipping / aperture / truncation)
- Full design summary table
- "Compare to dataset" panel: overlays the current config on the dataset OPL-vs-throughput scatter

Use this for design exploration: drag sliders, see how the spot pattern changes, see when the beam clips, see how chord_skip controls the AOI distribution.

### Plotly notebook — `notebooks/explore.ipynb`

Six paper-grade interactive figures, exportable to PDF/PNG via `kaleido`:

1. Rotatable 3D spot pattern of the best Pareto design
2. NSGA-II Pareto front 3D scatter (OPL × throughput × −clipping)
3. Dataset OPL vs throughput coverage, coloured by N, sized by vol. utilisation
4. Per-bounce AOI for the best config
5. Feature-importance bar charts (one per ML target)
6. OPL vs chord_skip sweep for N = 9, 12, 16 with coprime highlighting

### Best-design summary — `python -m tmpc_platform.scripts.summarise_best`

Prints a one-page physics report for the BO best + top-N Pareto configs:

```
========================================================================
  BAYESIAN-OPT BEST DESIGN
========================================================================
GEOMETRY     N=15   chord_skip=7   R_ring=75.9 mm   H=28.7 mm
MIRROR       R_t=130.4 mm   R_s=178.4 mm   aperture=8.6 mm   R=0.9990
BEAM         lambda=1654.0 nm   w0=1.398 mm   z_off=-2.50 mm

BOUNCES           120
OPL            18.082  m       (chord/bounce = 150.99 mm)
AOI mean         6.20  deg
AOI max          6.40  deg
Beam w_max      2.154  mm     (aperture 8.56 mm)
Vol. util.      18.15  %
Stability g²   0.0249        STABLE

LOSS BUDGET
  reflectivity loss  11.313 %
  clipping loss       0.000 %
  aperture loss       0.000 %
  truncation loss     9.985 %
  total throughput   79.832 %

AOI distribution: [text histogram]
```

---

Outputs land in `results/`:

```
results/
├── dataset.csv               <- 1 row per simulated configuration
├── models/                   <- joblib + pt files for every surrogate + ensemble + PINN
│   └── metrics.csv           <- R² and MAE per model & target
├── optim/
│   ├── bo_trace.csv          <- Bayesian opt iterations
│   ├── bo_best.csv           <- best config from BO
│   └── pareto.csv            <- non-dominated NSGA-II solutions
├── explain/
│   ├── shap_values__*.npy
│   ├── importance__*.csv
│   └── sobol_S1__*.csv
└── plots/                    <- all figures (.png)
```

---

## Run stages individually

```bash
python -m tmpc_platform.scripts.01_generate_dataset --n 5000 --workers 8
python -m tmpc_platform.scripts.02_train_models
python -m tmpc_platform.scripts.03_optimize --bo-calls 60 --ga-gen 40
python -m tmpc_platform.scripts.03_optimize --use-surrogate  # >100× faster
python -m tmpc_platform.scripts.04_explain
python -m tmpc_platform.scripts.05_visualize
```

---

## Use the simulator directly

```python
from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc

cfg = TMPCConfig(N=9, R_ring=50, H=40, R_t=100, R_s=100,
                 chord_skip=4, w0=0.5, n_passes=64)
res = simulate_tmpc(cfg)
print(f"OPL = {res.opl*1e-3:.2f} m   bounces = {res.bounces}   "
      f"throughput = {res.throughput:.3f}   "
      f"vol util = {res.volume_utilisation:.2f}")
```

## Use a trained surrogate

```python
import joblib, numpy as np
from tmpc_platform.ml_models.training import FEATURES

model = joblib.load("results/models/RandomForest__opl_m.joblib")
X = np.array([[12, 60, 40, 120, 110, 3, 0.4, 0.999]])  # FEATURES order
print("predicted OPL [m]:", model.predict(X)[0])
```

## Multi-objective optimisation example

```python
from tmpc_platform.optimization import nsga2_optimize
from tmpc_platform.scripts.optimize_helpers import sim_obj

res = nsga2_optimize(
    objectives=[lambda c: sim_obj(c, "opl_m"),
                lambda c: sim_obj(c, "throughput"),
                lambda c: sim_obj(c, "clipping")],
    pop_size=60, n_gen=40,
    maximize_flags=[True, True, True],
)
print(res["pareto"].head())
```

---

## Architecture

```
tmpc_platform/
├── physics_engine/        toroidal surfaces, ray tracer, Gaussian beam, losses, stability
├── dataset_generation/    Sobol / LHS samplers, parallel evaluator
├── ml_models/             surrogates, PINN, stacking ensemble, training helpers
├── optimization/          Bayesian opt, GA / NSGA-II, active learning
├── explainability/        SHAP, Sobol sensitivity indices
├── visualization/         all plots (saved as PNGs)
├── scripts/               01–05 stage scripts + run_all
├── tests/                 pytest smoke tests
├── configs/               YAML configs
└── results/               outputs land here
```

---

## Validation hooks (what to add next)

The platform is built so you can plug in higher-fidelity validators as you go:

1. **Optiland comparison** — wrap an `optiland`-based simulator with the same `TMPCConfig` interface and run it on a small subset of the dataset for ground-truth comparison. Drop the wrapper into `physics_engine/validators.py`.
2. **Zemax / 3DOptix export** — emit `.zos` or `.optix` from a `TMPCConfig`. Useful for the conference paper figures.
3. **Thorlabs mirror catalogue** — restrict R_t, R_s, aperture to discrete Thorlabs SKUs by adding a discrete-search wrapper around the optimiser.
4. **Drone vibration analysis** — add a `mechanical/vibration.py` module that applies random per-mirror tilt jitter and recomputes throughput vs. RMS tilt angle. This feeds the noise-floor analysis the brief asks for.
5. **CAD export** — emit Fusion 360 parameter tables (CSV) from the Pareto front so CAD work tracks the optimisation directly.

---

## Notes on physics fidelity

- The toroidal surface uses the exact implicit equation `(√((R_t-z)² + x²) - (R_t-R_s))² + y² = R_s²` with analytic gradient; ray intersection is found by Newton iteration from a paraxial seed. This is accurate for small angles and converges in ≤5 iterations for the regime of interest.
- Gaussian beam propagation is ABCD-matrix-based, separately in tangential and sagittal planes — the standard treatment for astigmatic toroidal optics.
- Loss budget combines reflectivity, hard clipping (`w_max ≥ aperture`), soft Gaussian truncation, and entrance/exit hole truncation.
- The default `n_passes = 8N` matches your Tuzson/Graf baseline.
- Stability is computed from the symmetric ring g-product `(1 - chord/R_t)²`.
- Re-entrance score = `period(N, chord_skip) / N` ∈ (0, 1], maximal when `gcd(N, chord_skip) = 1`.

## Notes on ML

- Targets: OPL [m], throughput, quality (composite), stability_g.
- Train/test split is fixed seed for reproducibility.
- The PINN adds a monotonicity penalty: more bounces ⇒ longer OPL ⇒ lower throughput. This regularises predictions in low-density regions of the design space.
- Stacking ensemble is a Ridge meta-learner over all base predictions for a target.

---

## Reproducing the conference paper plots

After `run_all`, look in `results/plots/` for:

- `spot_pattern_best.png` — the best Pareto config's 3-D bounce trace and unfolded pattern
- `roc_vs_opl.png` — OPL vs tangential ROC, coloured by throughput
- `stability_landscape.png` — g² stability across (R_t, R_ring)
- `beam_evolution.png` — tangential and sagittal beam radii over the cell
- `pareto_front.png` — non-dominated OPL × throughput × −clipping front
- `metrics_table.png` — surrogate model comparison
- `importance__*.png` — SHAP / permutation feature importance

---

## License & IP

Per IITD-Abu Dhabi / Aston joint brief, all IP belongs to Aston. Internal use only.
