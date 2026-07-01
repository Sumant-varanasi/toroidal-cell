"""TMPC platform v5 — toroidal multipass cell simulator with tolerance analysis.

Capabilities (everything v4 does, plus tolerances):
    physics.py    : toroidal surface, ray tracer, Gaussian beam, losses,
                    stability, full multipass simulation
    tolerance.py  : fabrication / alignment / thermal / vibration / launch
                    perturbations, Monte-Carlo sweep, one-at-a-time
                    sensitivities, RSS tolerance budget allocation
    samplers.py   : Sobol / LHS sampling, Thorlabs catalogue snapping
    dataset.py    : parallel Sobol dataset generator (CSV out)
    optimize.py   : random + Bayesian (skopt) optimisation
    surrogate.py  : RandomForest surrogate over the physics simulator
    plots.py      : publication-grade matplotlib figures
    summarise.py  : one-page text physics + tolerance report
    cli.py        : single entrypoint with subcommands

Quick example
-------------
>>> from tmpc_platform_v5 import TMPCConfig, simulate_tmpc, ToleranceSpec, monte_carlo
>>> cfg = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=120, chord_skip=5, w0=0.5)
>>> res = simulate_tmpc(cfg)
>>> print(res.bounces, res.opl * 1e-3, res.throughput)
>>> tol_df = monte_carlo(cfg, ToleranceSpec.research_grade(), n_trials=200)
>>> print(tol_df["throughput"].describe())
"""
from .physics import (
    ToroidalSurface, Ray, reflect, trace_ray,
    GaussianBeam, abcd_propagate, propagate_through_cell,
    LossBudget, compute_losses,
    stability_parameter, is_stable, reentrance_score,
    TMPCConfig, SimResult, MirrorPerturbation, GlobalPerturbation,
    simulate_tmpc, build_mirror_ring, spot_diagnostics, mirror_footprints,
)
from .beam import (
    AstigBeam, astigmatic_focal_lengths, propagate_astigmatic,
    envelope_along_path, unit_cell_stability,
)
from .tolerance import (
    ToleranceSpec, sample_perturbations,
    monte_carlo, summarise_mc,
    sensitivity, tolerance_budget,
    thermal_perturbation, thermal_mirror_perturbations, vibration_spec,
    full_report,
)

__version__ = "0.5.0"

__all__ = [
    "ToroidalSurface", "Ray", "reflect", "trace_ray",
    "GaussianBeam", "abcd_propagate", "propagate_through_cell",
    "LossBudget", "compute_losses",
    "stability_parameter", "is_stable", "reentrance_score",
    "TMPCConfig", "SimResult", "MirrorPerturbation", "GlobalPerturbation",
    "simulate_tmpc", "build_mirror_ring", "spot_diagnostics", "mirror_footprints",
    "AstigBeam", "astigmatic_focal_lengths", "propagate_astigmatic",
    "envelope_along_path", "unit_cell_stability",
    "ToleranceSpec", "sample_perturbations",
    "monte_carlo", "summarise_mc",
    "sensitivity", "tolerance_budget",
    "thermal_perturbation", "thermal_mirror_perturbations", "vibration_spec",
    "full_report",
]
