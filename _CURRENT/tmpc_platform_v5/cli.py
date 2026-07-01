"""Single CLI entrypoint with subcommands.

Subcommands:
    simulate   one configuration, print summary, optional plots
    tolerance  Monte-Carlo + sensitivity + budget allocation
    dataset    Sobol parameter sweep, write CSV
    optimize   random or Bayesian search
    surrogate  train RandomForest surrogate on a dataset CSV
    sweep      one-axis parameter sweep (e.g. chord_skip 1..N-1)

Run as:
    python -m tmpc_platform_v5 simulate ...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import numpy as np
import pandas as pd

from .physics import (TMPCConfig, simulate_tmpc, GaussianBeam,
                      propagate_through_cell)
from .tolerance import (ToleranceSpec, monte_carlo, summarise_mc,
                        sensitivity, tolerance_budget)
from .summarise import physics_report, tolerance_report
from . import plots as plt_mod


# =============================================================================
# config helpers
# =============================================================================
# single source of truth for cfg defaults (used when no preset is selected)
_CFG_DEFAULTS = {
    "N": 12, "R_ring": 60.0, "H": 40.0, "R_t": 120.0, "R_s": 120.0,
    "mirror_aperture": 8.0, "chord_skip": 5, "w0": 0.5, "M2": 1.0,
    "wavelength": 1.654e-3, "input_offset_z": 0.0, "input_offset_t": 0.0,
    "input_angle": 0.0, "input_angle_sag": 0.0, "reflectivity": 0.999,
    "hole_radius": 1.5, "topology": "ring", "M_halflaps": 8,
    "astigmatic": True,
}
_CFG_FIELDS = list(_CFG_DEFAULTS.keys())


def add_cfg_args(p: argparse.ArgumentParser):
    # Every cfg arg defaults to None (sentinel = "not provided on CLI") so that
    # a preset's values survive unless the user explicitly overrides them.
    p.add_argument("--preset", type=str, default=None,
                   help="named design point (see `tmpc_platform_v5 presets`); "
                        "explicit flags still override it")
    p.add_argument("--N", type=int, default=None, help="mirrors (default 12)")
    p.add_argument("--R_ring", type=float, default=None, help="ring radius mm (60)")
    p.add_argument("--H", type=float, default=None, help="cell height mm (40)")
    p.add_argument("--R_t", type=float, default=None, help="tangential ROC mm (120)")
    p.add_argument("--R_s", type=float, default=None, help="sagittal ROC mm (120)")
    p.add_argument("--mirror_aperture", type=float, default=None,
                   help="clear-aperture RADIUS mm (8)")
    p.add_argument("--chord_skip", type=int, default=None, help="mirrors/bounce (5)")
    p.add_argument("--n_passes", type=int, default=None, help="bounces (8*N)")
    p.add_argument("--w0", type=float, default=None, help="waist radius mm (0.5)")
    p.add_argument("--M2", type=float, default=None, help="beam-quality factor (1.0)")
    p.add_argument("--wavelength", type=float, default=None,
                   help="wavelength mm (1.654e-3 = 1654 nm)")
    p.add_argument("--input_offset_z", type=float, default=None,
                   help="launch sagittal (vertical) start-spot offset mm (0)")
    p.add_argument("--input_offset_t", type=float, default=None,
                   help="launch tangential (in-plane) start-spot offset mm (0)")
    p.add_argument("--input_angle", type=float, default=None,
                   help="launch tilt about sagittal axis (in-plane) rad (0)")
    p.add_argument("--input_angle_sag", type=float, default=None,
                   help="launch tilt about tangential axis (out-of-plane) rad (0)")
    p.add_argument("--reflectivity", type=float, default=None, help="per-mirror R (0.999)")
    p.add_argument("--hole_radius", type=float, default=None,
                   help="entrance/exit hole radius mm (1.5)")
    p.add_argument("--topology", choices=["ring", "spiral"], default=None,
                   help="cell topology (ring)")
    p.add_argument("--M_halflaps", type=int, default=None,
                   help="spiral: half-laps before top retroreflector (8)")
    p.add_argument("--no-astigmatic", dest="astigmatic",
                   action="store_const", const=False, default=None,
                   help="disable off-axis astigmatic focal lengths (paraxial)")
    p.add_argument("--config-json", type=str, default=None,
                   help="optional JSON file with cfg overrides (wins over all)")


def cfg_from_args(args) -> TMPCConfig:
    # 1) base: a preset's full kwargs, else the documented defaults
    if getattr(args, "preset", None):
        from .presets import get_preset
        base = get_preset(args.preset)
        kw = {f: getattr(base, f) for f in _CFG_FIELDS}
    else:
        kw = dict(_CFG_DEFAULTS)
    # 2) overlay only flags the user actually provided (non-None sentinel)
    for f in _CFG_FIELDS:
        v = getattr(args, f, None)
        if v is not None:
            kw[f] = v
    # 3) JSON overrides win
    if getattr(args, "config_json", None):
        with open(args.config_json) as fh:
            kw.update(json.load(fh))
    cfg = TMPCConfig(**{k: v for k, v in kw.items()
                        if k in TMPCConfig.__dataclass_fields__})
    cfg.n_passes = args.n_passes if getattr(args, "n_passes", None) else 8 * cfg.N
    return cfg


def spec_from_args(args) -> ToleranceSpec:
    tp = getattr(args, "tol_preset", None)
    if tp == "loose":
        return ToleranceSpec.loose()
    if tp == "research":
        return ToleranceSpec.research_grade()
    if tp == "flight":
        return ToleranceSpec.flight_grade()
    return ToleranceSpec(
        sigma_d_lateral=args.sigma_d_lateral,
        sigma_d_axial=args.sigma_d_axial,
        sigma_tilt=args.sigma_tilt,
        sigma_dR=args.sigma_dR,
        sigma_R_ring=args.sigma_R_ring,
        sigma_H=args.sigma_H,
        sigma_input_pos=args.sigma_input_pos,
        sigma_input_tilt=args.sigma_input_tilt,
        sigma_refl=args.sigma_refl,
        sigma_lambda=args.sigma_lambda,
    )


def add_tol_args(p: argparse.ArgumentParser):
    p.add_argument("--tol-preset", dest="tol_preset",
                   choices=["loose", "research", "flight"], default="research",
                   help="tolerance grade preset")
    p.add_argument("--sigma_d_lateral", type=float, default=0.050)
    p.add_argument("--sigma_d_axial",   type=float, default=0.10)
    p.add_argument("--sigma_tilt",      type=float, default=0.5,
                   help="per-mirror tilt sigma [mrad]")
    p.add_argument("--sigma_dR",        type=float, default=1.0)
    p.add_argument("--sigma_R_ring",    type=float, default=0.10)
    p.add_argument("--sigma_H",         type=float, default=0.10)
    p.add_argument("--sigma_input_pos", type=float, default=0.050)
    p.add_argument("--sigma_input_tilt", type=float, default=0.5,
                   help="launch-direction sigma [mrad]")
    p.add_argument("--sigma_refl",   type=float, default=0.001)
    p.add_argument("--sigma_lambda", type=float, default=1e-7)


# =============================================================================
# subcommands
# =============================================================================
def cmd_simulate(args):
    cfg = cfg_from_args(args)
    print(physics_report(cfg, title="DESIGN SUMMARY"))
    if args.plot_dir:
        res = simulate_tmpc(cfg)
        plt_mod.plot_spot_pattern(res.spot_pattern, cfg,
                                  os.path.join(args.plot_dir, "spot_pattern.png"))
        # use the REAL astigmatic beam radii the simulator already computed
        plt_mod.plot_beam_evolution(res.w_tangential, res.w_sagittal,
                                    cfg.mirror_aperture,
                                    os.path.join(args.plot_dir, "beam.png"))
        plt_mod.plot_losses(res.loss_budget,
                            os.path.join(args.plot_dir, "losses.png"))
        print(f"\nPlots saved under {args.plot_dir}")


def cmd_tolerance(args):
    cfg = cfg_from_args(args)
    spec = spec_from_args(args)
    print(f"Running {args.n_trials} Monte-Carlo trials...")
    mc = monte_carlo(cfg, spec, n_trials=args.n_trials,
                     seed=args.seed, n_workers=args.workers)
    summary = summarise_mc(mc, throughput_threshold=args.yield_threshold)
    print(f"Computing one-at-a-time sensitivity (metric={args.metric})...")
    sens = sensitivity(cfg, spec, metric=args.metric)
    print("Allocating RSS tolerance budget...")
    budget = tolerance_budget(sens, delta_target=args.delta_target)

    print(physics_report(cfg, title="NOMINAL DESIGN"))
    print(tolerance_report(summary, sens, budget, metric=args.metric))

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        mc.to_csv(os.path.join(args.out_dir, "mc.csv"), index=False)
        summary.to_csv(os.path.join(args.out_dir, "mc_summary.csv"), index=False)
        sens.to_csv(os.path.join(args.out_dir, "sensitivity.csv"), index=False)
        budget.to_csv(os.path.join(args.out_dir, "budget.csv"), index=False)
        plt_mod.plot_mc_histograms(mc, os.path.join(args.out_dir, "mc_hist.png"))
        plt_mod.plot_sensitivity_bars(sens, os.path.join(args.out_dir,
                                                         "sensitivity.png"),
                                      metric=args.metric)
        plt_mod.plot_tolerance_budget(budget, os.path.join(args.out_dir,
                                                           "budget.png"))
        plt_mod.plot_exit_pointing(mc, os.path.join(args.out_dir,
                                                    "exit_pointing.png"))
        print(f"\nWrote CSVs + plots to {args.out_dir}")


def cmd_dataset(args):
    from .dataset import generate_dataset
    generate_dataset(n_samples=args.n, n_workers=args.workers,
                     out_path=args.out, seed=args.seed,
                     thorlabs=args.thorlabs, thorlabs_family=args.family)


def cmd_optimize(args):
    from .optimize import random_search, bayesian_optimize, make_objective
    obj = make_objective(args.target)
    if args.engine == "bayes":
        r = bayesian_optimize(obj, n_calls=args.n_calls, seed=args.seed)
    else:
        r = random_search(obj, n_trials=args.n_calls, seed=args.seed)
    print(f"Best {args.target} = {r['best_value']:.4g}")
    print("Best config:")
    for k, v in r["best_cfg"].items():
        print(f"  {k:<18s} {v}")
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        r["trace"].to_csv(args.out, index=False)
        print(f"trace -> {args.out}")


def cmd_surrogate(args):
    from .surrogate import train_surrogates
    df = pd.read_csv(args.dataset)
    out = train_surrogates(df, n_estimators=args.trees, seed=args.seed)
    print("Metrics:")
    print(out["metrics"].to_string(index=False))
    print("\nFeature importance:")
    print(out["importance"].to_string(index=False))


def cmd_sweep(args):
    cfg = cfg_from_args(args)
    rows = []
    if args.param == "chord_skip":
        values = list(range(1, cfg.N))
    elif args.param in ("N",):
        values = list(range(int(args.lo), int(args.hi) + 1))
    else:
        values = list(np.linspace(args.lo, args.hi, args.n))
    for v in values:
        kw = {args.param: v}
        c = TMPCConfig(**{**cfg.__dict__, **kw})
        c.n_passes = 8 * c.N
        try:
            res = simulate_tmpc(c)
            row = {args.param: v, **res.as_dict()}
        except Exception as e:
            row = {args.param: v, "error": str(e)}
        rows.append(row)
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    if args.out:
        df.to_csv(args.out, index=False)
        print(f"-> {args.out}")


def cmd_visualize(args):
    from . import viz3d
    cfg = cfg_from_args(args)
    res = simulate_tmpc(cfg)
    os.makedirs(args.out_dir, exist_ok=True)
    label = (args.preset or "design")
    paths = viz3d.write_visualisation_bundle(res, cfg, args.out_dir,
                                             name=args.name, label=label)
    print(physics_report(cfg, title="VISUALISED DESIGN"))
    print("Interactive HTML written:")
    for k, v in paths.items():
        print(f"  {k:<26s} {v}")


def cmd_render(args):
    from . import render
    cfg = cfg_from_args(args)
    res = simulate_tmpc(cfg)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out = render.render_experiment(res, cfg, args.out, family=args.family,
                                   show_beam=not args.no_beam)
    print(f"As-built experiment render -> {out}")


def cmd_validate(args):
    from . import validate
    cfg = cfg_from_args(args)
    print(validate.validation_report(cfg))


def cmd_pareto(args):
    from . import pareto
    df = pareto.pareto_search(n_samples=args.n, seed=args.seed,
                              objectives=tuple(args.objectives),
                              verbose=True)
    front = df[df["on_pareto"]]
    print(f"\n{len(df)} evaluated, {len(front)} on the Pareto front "
          f"over {args.objectives}")
    cols = [c for c in ["N", "chord_skip", "R_ring", "R_t", "R_s",
                        "opl_m", "throughput", "clipped", "on_pareto"]
            if c in df.columns]
    print(pareto.top_designs(df, k=args.top, by=args.objectives[0])[cols]
          .to_string(index=False))
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        df.to_csv(args.out, index=False)
        print(f"-> {args.out}")
        try:
            plt_mod.plot_pareto(front, os.path.splitext(args.out)[0] + ".png",
                                args.objectives[0], args.objectives[1])
        except Exception as e:
            print(f"(pareto plot skipped: {e})")


def cmd_presets(args):
    from . import presets
    print("Available presets:\n")
    for name in presets.list_presets():
        cfg = presets.get_preset(name)
        print(f"  {name:<20s} {presets.preset_label(name)}")
        print(f"  {'':<20s} N={cfg.N} topology={cfg.topology} "
              f"R_ring={cfg.R_ring} R_t={cfg.R_t} R_s={cfg.R_s} "
              f"chord_skip={cfg.chord_skip}")


# =============================================================================
# main
# =============================================================================
def main(argv=None):
    # Crash-proof console output on Windows (cp1252 can't encode some glyphs).
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(prog="tmpc_platform_v5",
                                description="TMPC simulator + tolerance analysis")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("simulate", help="run one config")
    add_cfg_args(s)
    s.add_argument("--plot-dir", default=None,
                   help="if given, write spot/beam/loss plots here")
    s.set_defaults(fn=cmd_simulate)

    s = sub.add_parser("tolerance", help="MC + sensitivity + budget")
    add_cfg_args(s)
    add_tol_args(s)
    s.add_argument("--n-trials", type=int, default=200)
    s.add_argument("--workers", type=int, default=1)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--metric", default="throughput",
                   choices=["throughput", "opl_m", "bounces", "w_max_mm",
                            "stability_g", "aoi_mean",
                            "exit_drift_mrad", "spot_walk_mm"])
    s.add_argument("--delta-target", type=float, default=0.05,
                   help="target dY for RSS budget allocation")
    s.add_argument("--yield-threshold", type=float, default=0.5)
    s.add_argument("--out-dir", default=None)
    s.set_defaults(fn=cmd_tolerance)

    s = sub.add_parser("dataset", help="parallel Sobol parameter sweep")
    s.add_argument("--n", type=int, default=500)
    s.add_argument("--out", default="results/dataset.csv")
    s.add_argument("--workers", type=int, default=None)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--thorlabs", action="store_true")
    s.add_argument("--family", default="half_inch",
                   choices=["half_inch", "one_inch"])
    s.set_defaults(fn=cmd_dataset)

    s = sub.add_parser("optimize", help="random or Bayesian search")
    s.add_argument("--engine", choices=["random", "bayes"], default="bayes")
    s.add_argument("--target", default="throughput",
                   choices=["throughput", "opl_m", "quality", "bounces"])
    s.add_argument("--n-calls", type=int, default=60)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", default=None)
    s.set_defaults(fn=cmd_optimize)

    s = sub.add_parser("surrogate", help="train RF on a dataset CSV")
    s.add_argument("--dataset", required=True)
    s.add_argument("--trees", type=int, default=200)
    s.add_argument("--seed", type=int, default=0)
    s.set_defaults(fn=cmd_surrogate)

    s = sub.add_parser("sweep", help="one-axis parameter sweep")
    add_cfg_args(s)
    s.add_argument("--param", required=True)
    s.add_argument("--lo", type=float, default=1.0)
    s.add_argument("--hi", type=float, default=10.0)
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--out", default=None)
    s.set_defaults(fn=cmd_sweep)

    s = sub.add_parser("visualize",
                       help="interactive 3D cell view + beam tube + spot constellations (HTML)")
    add_cfg_args(s)
    s.add_argument("--out-dir", default="results/viz")
    s.add_argument("--name", default="design")
    s.set_defaults(fn=cmd_visualize)

    s = sub.add_parser("render",
                       help="photoreal 'as-built experiment' 3D render (HTML)")
    add_cfg_args(s)
    s.add_argument("--out", default="results/render/experiment.html")
    s.add_argument("--family", default="one_inch",
                   choices=["half_inch", "one_inch"])
    s.add_argument("--no-beam", action="store_true")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("validate",
                       help="analytic + ABCD + Optiland cross-validation")
    add_cfg_args(s)
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("pareto", help="dependency-free multi-objective Pareto front")
    s.add_argument("--n", type=int, default=512)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--objectives", nargs=2, default=["opl_m", "throughput"])
    s.add_argument("--top", type=int, default=10)
    s.add_argument("--out", default=None)
    s.set_defaults(fn=cmd_pareto)

    s = sub.add_parser("presets", help="list named design points")
    s.set_defaults(fn=cmd_presets)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
