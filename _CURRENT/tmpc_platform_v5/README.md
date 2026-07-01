# TMPC Platform v5 — definitive toroidal-multipass-cell model

A single, self-contained platform for designing, simulating, **tolerancing**, and
**visualising** Toroidal Multipass Cells (TMPC) for laser absorption spectroscopy
at 1.654 µm (CH₄). It is the superset of every earlier version in this repo, plus
the things they were missing: realistic astigmatic beam propagation, a full
tolerance/Monte-Carlo engine, two cell topologies, and true 3-D + "as-built"
visualisation.

> Use the project virtual-env interpreter: `./.venv/Scripts/python.exe`
> (it has numpy, scipy, pandas, matplotlib, plotly, scikit-learn,
> scikit-optimize, optiland). Run all commands from the repo root so
> `import tmpc_platform_v5` resolves.

**See the [figure gallery](examples/README.md)** for rendered 3-D cell views,
as-built renders, spot constellations, and tolerance-analysis plots.

---

## What it does (capability map)

**Physics (`physics.py`, `beam.py`)**
- Exact 3-D ray tracing on toroidal mirror surfaces (implicit torus, analytic
  normal, Newton-iterated intersection) with per-bounce angle-of-incidence and
  hard-aperture clipping.
- Two topologies:
  - `ring` — Herriott-style rotating polygon, beam advances `chord_skip` mirrors
    per bounce (real ray-traced helix when launched off-plane).
  - `spiral` — Tuzson/Graf up-down cell: enter a hole at z = −H/2, spiral up,
    hit a top retroreflector, spiral back down, exit. AOI = π/2 − π/N.
- **Realistic astigmatic Gaussian beam**: off-axis focal lengths
  `f_tan = R·cosθ/2`, `f_sag = R/(2cosθ)`, M²-corrected, propagated with the
  *actual* per-bounce AOI and chord lengths — tangential and sagittal radii
  evolve independently.
- Loss budget (reflectivity / clipping / aperture / hole truncation), isotropic
  and **per-plane astigmatic stability** (m_tan, m_sag), re-entrance score,
  volume utilisation, and spot-pattern diagnostics (distinct-spot separation,
  overlap, mirror fill fraction).
- Arbitrary launch: tangential & sagittal **start-spot offset** and two
  independent **launch tilts**.

**Tolerances (`tolerance.py`)** — the headline addition
- Per-mirror perturbations (decenter ×3, tilt ×2, ROC errors, aperture loss) and
  global perturbations (ring radius, height, launch position/tilt, reflectivity,
  wavelength), all truncated-normal.
- **Monte-Carlo** yield study with continuous walk-off metrics
  (`exit_drift_mrad`, `spot_walk_mm`) that don't suffer the step-function
  flatness of throughput.
- **One-at-a-time sensitivity** (mini-MC isolation) and an **RSS tolerance-budget
  allocator** with per-tolerance weighting.
- Presets: `loose` / `research_grade` / `flight_grade`; environmental factories
  for thermal (CTE-driven) and vibration studies.

**Visualisation (`viz3d.py`, `render.py`, `plots.py`)**
- Interactive 3-D cell view (Plotly): toroidal mirror meshes, the real ray path,
  bounce-coloured spots, a **real elliptical beam tube** swept along the path,
  input & exit rays.
- Per-mirror **spot constellations** (raytrace + ABCD/Lissajous prediction).
- **"As-built experiment" render**: gold mirror substrates, mounts, breadboard,
  entrance/exit holes, emissive laser beam, specular lighting.
- Matplotlib figures: spot pattern, astigmatic beam evolution, loss budget,
  static 3-D cell, Pareto front, MC histograms, sensitivity bars, tolerance
  budget, exit-pointing walk-off.

**Design exploration**
- `samplers.py` Sobol/LHS + Thorlabs catalogue snapping.
- `dataset.py` parallel Sobol dataset generator.
- `optimize.py` random + Bayesian (skopt) optimisation.
- `surrogate.py` RandomForest surrogate + permutation importance.
- `pareto.py` dependency-free multi-objective Pareto front.

**Validation (`validate.py`)**
- Analytic cross-checks (AOI = π/2 − π/N, chord length, spiral closure).
- ABCD-vs-raytrace residual.
- Optiland external cross-validation (soft-imported; skipped if absent).

---

## Quick start (CLI)

```bash
PY=./.venv/Scripts/python.exe

# one design, full physics report
$PY -m tmpc_platform_v5 simulate --N 12 --R_ring 60 --R_t 120 --R_s 180 \
    --chord_skip 5 --w0 0.5 --M2 1.1 --input_offset_z -2

# named design points
$PY -m tmpc_platform_v5 presets
$PY -m tmpc_platform_v5 simulate --preset longest_opl

# TOLERANCE STUDY (Monte-Carlo + sensitivity + RSS budget + plots)
$PY -m tmpc_platform_v5 tolerance --preset bo_best_one_inch \
    --tol-preset research --n-trials 300 --metric exit_drift_mrad \
    --delta-target 1.0 --out-dir results/tol

# INTERACTIVE 3-D + spot constellations (standalone HTML)
$PY -m tmpc_platform_v5 visualize --preset toroidal_lissajous --out-dir results/viz

# "AS-BUILT" experiment render
$PY -m tmpc_platform_v5 render --preset bo_best_one_inch --out results/render/exp.html

# physics validation (analytic + ABCD + Optiland if installed)
$PY -m tmpc_platform_v5 validate --N 8 --chord_skip 1

# multi-objective Pareto front
$PY -m tmpc_platform_v5 pareto --n 512 --objectives opl_m throughput --out results/pareto.csv

# design-space tools
$PY -m tmpc_platform_v5 dataset --n 2000 --thorlabs --family one_inch --out results/ds.csv
$PY -m tmpc_platform_v5 optimize --engine bayes --target opl_m --n-calls 60
$PY -m tmpc_platform_v5 surrogate --dataset results/ds.csv
$PY -m tmpc_platform_v5 sweep --param chord_skip --N 12
```

---

## Quick start (Python API)

```python
from tmpc_platform_v5 import TMPCConfig, simulate_tmpc, ToleranceSpec, full_report

cfg = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=180,
                 chord_skip=5, w0=0.5, M2=1.1, input_offset_z=-2.0)
cfg.n_passes = 8 * cfg.N
res = simulate_tmpc(cfg)
print(res.bounces, res.opl*1e-3, res.throughput, res.stability_tan, res.stability_sag)

# full tolerance report (MC + sensitivity + budget)
rep = full_report(cfg, ToleranceSpec.research_grade(), n_trials=300,
                  metric="exit_drift_mrad")
print(rep["summary"]); print(rep["sensitivity"]); print(rep["budget"])
```

---

## Module layout

```
tmpc_platform_v5/
├── physics.py     toroidal surface, ray tracer, both topologies, simulate_tmpc, diagnostics
├── beam.py        astigmatic M² Gaussian beam, envelope-along-path (beam tube)
├── tolerance.py   perturbations, Monte-Carlo, sensitivity, RSS budget, thermal/vibration
├── samplers.py    Sobol/LHS + Thorlabs catalogue
├── dataset.py     parallel Sobol dataset generator
├── optimize.py    random + Bayesian optimisation
├── surrogate.py   RandomForest surrogate
├── pareto.py      dependency-free Pareto front
├── presets.py     named design points
├── plots.py       matplotlib figures
├── viz3d.py       interactive Plotly 3-D + spot constellations
├── render.py      "as-built" photoreal render
├── validate.py    analytic + ABCD + Optiland validation
├── summarise.py   text reports
├── cli.py         single entrypoint (subcommands)
└── tests/         pytest suite
```

All units are millimetres; wavelength in mm (1.654e-3 = 1654 nm); angles in
radians unless a name says `_deg`/`_mrad`. Optional deps (plotly, optiland,
scikit-optimize, scikit-learn) are soft-imported with clear messages.
