# _CURRENT — the definitive TMPC model

This folder gathers the **current, required** code for the Toroidal Multipass
Cell project so it's easy to find without wading through the older iterations
(`tmpc_platform/`, `tmpc_platform_v2/`, `tmpc_platform_v4/`) that still live at
the repository root for reference.

Everything you need for day-to-day work is here:

| Path | What it is |
|---|---|
| `tmpc_platform_v5/` | The definitive model — physics, tolerances, optimisation, 3-D viz, CLI, tests |
| `tmpc_platform_v5/examples/` | Regenerable figure gallery (3-D views, renders, tolerance plots) |
| `tmpc_platform_v5/README.md` | Full documentation, Python API, and module map |

## Running it

The model is a self-contained Python package invoked with `-m`. Run the
commands **from inside this `_CURRENT/` folder** so `tmpc_platform_v5` resolves,
using the shared virtualenv that lives one level up at `../.venv`:

```bash
# from _CURRENT/
PY=../.venv/Scripts/python.exe

$PY -m tmpc_platform_v5 presets                                   # list designs
$PY -m tmpc_platform_v5 simulate  --preset bo_best_one_inch       # physics report
$PY -m tmpc_platform_v5 tolerance --preset bo_best_one_inch --out-dir results/tol
$PY -m tmpc_platform_v5 visualize --preset bo_best_one_inch --out-dir results/viz
$PY -m tmpc_platform_v5 render    --preset bo_best_one_inch --out results/exp.html
$PY -m tmpc_platform_v5 validate  --preset bo_best_one_inch
$PY -m tmpc_platform_v5 pareto    --n 512
```

Dependencies are already installed in `../.venv`; the full freeze is in
`../requirements.txt`.

## Tests

```bash
# from _CURRENT/
../.venv/Scripts/python.exe -m pytest tmpc_platform_v5/tests -q
```
