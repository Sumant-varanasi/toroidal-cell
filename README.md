# Toroidal Multipass Cell (TMPC) Platform

A Python toolkit for **designing, simulating, tolerancing, and visualising
Toroidal Multipass Cells** (TMPC) for laser absorption spectroscopy at 1.654 µm
(CH₄). The project pairs a custom 3-D ray tracer with an astigmatic
Gaussian-beam model, a full Monte-Carlo tolerance engine, multi-objective design
exploration, and interactive 3-D / photorealistic visualisation.

Multipass cells fold a long optical path into a compact volume by bouncing a
laser many times between mirrors — the more path, the more sensitive the gas
sensor. This repository explores toroidal-mirror geometries that support both
Herriott-style *ring* patterns and Tuzson/Graf-style *spiral* (up-down)
patterns, and provides the tooling to pick, tolerance, and validate a real
design.

The current, definitive model lives in
**[`_CURRENT/tmpc_platform_v5/`](_CURRENT/tmpc_platform_v5/)** — a self-contained
superset of the earlier iterations.

## Headline result — verified drone cell designs (July 2026)

**[`_CURRENT/drone_20m/`](_CURRENT/drone_20m/README.md)** holds a menu of
**fully verified drone-mountable designs using only catalog Thorlabs 1″ gold
mirrors** (N = 8–16, exact 3-D ray trace, Optiland-cross-validated, every
physical check enforced):

| envelope | OPL | throughput @ R=0.985 | build |
|---|---|---|---|
| Ø180 mm | **24.8 m** | 7.1 % | 16 × CM254-200-M01 |
| Ø180 mm | **20.4 m** | **11.5 %** | 16 × CM254-150-M01 (preset `drone_20m`) |
| Ø159 mm | **20.6 m** | 7.9 % | 13 × CM254-050-M01 (preset `drone_16cm`) |
| Ø143 mm | 13.6 m | 13.8 % | 12 × CM254-250-M01 |

(Published toroidal cells of this size class demonstrate ~10 m.) Each design
ships with an as-built spec — machined mirror placements, mode-matching lens
setting, launch tilts, detector pickoff, per-mirror spot maps — plus
Monte-Carlo tolerances and an ROC-compensation assembly rule.

<p align="center">
  <img src="_CURRENT/tmpc_platform_v5/examples/figures/bo_best_one_inch_cell3d.png" width="48%" alt="3D ray path + beam tube">
  <img src="_CURRENT/tmpc_platform_v5/examples/figures/bo_best_one_inch_experiment.png" width="48%" alt="As-built experiment render">
</p>

*Left: the true ray-traced path with the beam rendered as a tube. Right: the
same cell as an "as-built" assembly — gold 1" mirrors, mounts, breadboard, and
the laser bouncing through it.*

---

## Repository layout

The definitive model is consolidated under **`_CURRENT/`** for easy access; the
older iterations remain at the repo root for reference.

| Path | Description |
| --- | --- |
| **`_CURRENT/`** | **Everything current** — the definitive model, gathered together |
| **`_CURRENT/tmpc_platform_v5/`** | **Latest platform.** Full physics, tolerancing, optimisation and visualisation. |
| `_CURRENT/tmpc_platform_v5/examples/` | Rendered figure gallery (3-D views, as-built renders, spot constellations, tolerance plots). |
| `tmpc_platform_v4/`, `tmpc_platform_v2/`, `tmpc_platform/` | Earlier iterations, kept for reference. |
| `run.py` | Standalone Optiland cross-validation of the ray tracer. |
| `test.py` | Quick checks / scratch script. |
| `.venv/`, `requirements.txt` | Shared Python runtime and pinned dependencies. |
| `file_toroidal_cell/`, `toroidal-cell/`, `files (1)/`, `files (2)/` | Historical archives and generated artefacts (CSVs, figures). |

See the **[figure gallery](_CURRENT/tmpc_platform_v5/examples/README.md)** for the
full set of rendered outputs.

<p align="center">
  <img src="_CURRENT/tmpc_platform_v5/examples/figures/toroidal_lissajous_constellations.png" width="70%" alt="Per-mirror spot constellations">
</p>

*Per-mirror spot pattern for a toroidal (R_t ≠ R_s) design — the astigmatic
Lissajous footprints on each mirror face.*

---

## What v5 does

**Physics** (`physics.py`, `beam.py`) — exact 3-D ray tracing on toroidal mirror
surfaces (analytic normal, Newton-iterated intersection) with per-bounce
angle-of-incidence and hard-aperture clipping. Two topologies are supported: a
*ring* (Herriott-style rotating polygon) and a *spiral* (up-down) cell. Beam
propagation uses a realistic astigmatic M²-corrected Gaussian model in which the
tangential and sagittal radii evolve independently. A loss budget, isotropic and
per-plane stability, re-entrance score, volume utilisation, and spot-pattern
diagnostics are all computed.

**Tolerances** (`tolerance.py`) — per-mirror and global truncated-normal
perturbations, a Monte-Carlo yield study with continuous walk-off metrics,
one-at-a-time sensitivity analysis, and an RSS tolerance-budget allocator.
Presets range from loose to flight-grade, with thermal and vibration factories.

**Visualisation** (`viz3d.py`, `render.py`, `plots.py`) — interactive Plotly 3-D
cell views with the real ray path and beam tube, per-mirror spot constellations,
a photoreal "as-built" render, and publication-ready matplotlib figures.

**Design exploration & validation** — Sobol/LHS sampling with Thorlabs catalogue
snapping, parallel dataset generation, random + Bayesian optimisation, a
RandomForest surrogate, a dependency-free Pareto front, and validation via
analytic cross-checks, ABCD-vs-raytrace residuals, and optional Optiland
cross-validation.

---

## Installation

```bash
git clone https://github.com/Sumant-varanasi/toroidal-cell.git
cd toroidal-cell
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Core dependencies are NumPy, SciPy, pandas and matplotlib. Optional features use
`plotly`, `optiland`, `scikit-optimize` and `scikit-learn`; these are
soft-imported and skipped with a clear message if absent.

> The model is invoked as a package (`python -m tmpc_platform_v5 …`), so run the
> commands **from inside `_CURRENT/`** where the package lives. The examples
> below use the shared virtualenv one level up at `../.venv`.

---

## Quick start (CLI)

```bash
cd _CURRENT
PY=../.venv/Scripts/python.exe   # Linux/macOS: ../.venv/bin/python

# list named design points and simulate one
$PY -m tmpc_platform_v5 presets
$PY -m tmpc_platform_v5 simulate --preset longest_opl

# one design from raw parameters, full physics report
$PY -m tmpc_platform_v5 simulate --N 12 --R_ring 60 --R_t 120 --R_s 180 --chord_skip 5

# Monte-Carlo tolerance study (sensitivity + RSS budget + plots)
$PY -m tmpc_platform_v5 tolerance --preset bo_best_one_inch --tol-preset research --n-trials 300

# interactive 3-D + spot constellations, and an "as-built" render
$PY -m tmpc_platform_v5 visualize --preset toroidal_lissajous --out-dir results/viz
$PY -m tmpc_platform_v5 render --preset bo_best_one_inch --out results/render/exp.html

# physics validation (analytic + ABCD + Optiland if installed), and a Pareto front
$PY -m tmpc_platform_v5 validate --N 8 --chord_skip 1
$PY -m tmpc_platform_v5 pareto --n 512
```

## Quick start (Python API)

```python
from tmpc_platform_v5 import TMPCConfig, simulate_tmpc, ToleranceSpec, full_report

cfg = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=180,
                 chord_skip=5, w0=0.5, M2=1.1, input_offset_z=-2.0)
cfg.n_passes = 8 * cfg.N
res = simulate_tmpc(cfg)
print(res.bounces, res.opl, res.throughput, res.stability_tan, res.stability_sag)

# full tolerance report (Monte-Carlo + sensitivity + budget)
rep = full_report(cfg, ToleranceSpec.research_grade(), n_trials=300, metric="exit_drift_mrad")
print(rep["summary"], rep["sensitivity"], rep["budget"])
```

## Conventions

All lengths are in millimetres, wavelength in mm (`1.654e-3` = 1654 nm), and
angles in radians unless a name ends in `_deg`/`_mrad`.

## Validating the ray tracer

`run.py` rebuilds the same cell geometry in the open-source
[Optiland](https://github.com/HarrisonKramer/optiland) package and compares
per-bounce spot positions, chord length, and angle of incidence against the
custom NumPy tracer.

---

> IP note: per the IITD-Abu Dhabi / Aston joint brief, all IP belongs to Aston.
> Internal use only.
