"""Regenerate the example figure gallery under tmpc_platform_v5/examples/figures.

Run from the repo root with the project venv:
    ./.venv/Scripts/python.exe -m tmpc_platform_v5.examples.generate_gallery

Produces static PNGs (render inline on GitHub) plus the interactive HTML
viewers, for two showcase designs:
  - bo_best_one_inch   (realistic optimised one-inch-mirror cell)
  - toroidal_lissajous (R_t != R_s -> astigmatic Lissajous spot pattern)
and a tolerance study + Pareto front.
"""
from __future__ import annotations

import os

import numpy as np

from tmpc_platform_v5 import (simulate_tmpc, AstigBeam, envelope_along_path,
                              ToleranceSpec, monte_carlo, sensitivity,
                              tolerance_budget)
from tmpc_platform_v5.presets import get_preset
from tmpc_platform_v5 import plots as P
from tmpc_platform_v5 import viz3d, render, pareto

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)


def _png_from_plotly(fig, path, width=1100, height=800):
    """Export a static PNG snapshot of a Plotly figure (needs kaleido)."""
    try:
        fig.write_image(path, width=width, height=height, scale=1)
        return True
    except Exception as e:
        print(f"  (kaleido PNG export skipped for {os.path.basename(path)}: {e})")
        return False


def static_figures(preset: str):
    cfg = get_preset(preset)
    res = simulate_tmpc(cfg)
    print(f"[{preset}] bounces={res.bounces} OPL={res.opl*1e-3:.2f} m "
          f"T={res.throughput*100:.1f}%")

    # matplotlib PNGs
    P.plot_spot_pattern(res.spot_pattern, cfg,
                        os.path.join(FIG, f"{preset}_spot_pattern.png"))
    P.plot_beam_evolution(res.w_tangential, res.w_sagittal, cfg.mirror_aperture,
                          os.path.join(FIG, f"{preset}_beam_evolution.png"))
    P.plot_losses(res.loss_budget, os.path.join(FIG, f"{preset}_losses.png"))
    P.plot_cell_3d(res, cfg, os.path.join(FIG, f"{preset}_cell3d_static.png"))

    # interactive HTML + PNG snapshots of the 3D views
    cell = viz3d.build_cell_figure(res, cfg, label=preset)
    cell.write_html(os.path.join(FIG, f"{preset}_cell3d.html"),
                    include_plotlyjs="cdn", full_html=True)
    _png_from_plotly(cell, os.path.join(FIG, f"{preset}_cell3d.png"))

    const = viz3d.build_constellations(cfg, res.spot_pattern,
                                       res.mirror_sequence, "raytrace")
    const.write_html(os.path.join(FIG, f"{preset}_constellations.html"),
                     include_plotlyjs="cdn", full_html=True)
    _png_from_plotly(const, os.path.join(FIG, f"{preset}_constellations.png"),
                     width=1100, height=900)

    exp_html = os.path.join(FIG, f"{preset}_experiment.html")
    _, exp_fig = render.render_experiment(res, cfg, exp_html, family="one_inch",
                                          return_fig=True)
    _png_from_plotly(exp_fig, os.path.join(FIG, f"{preset}_experiment.png"),
                     width=1100, height=850)
    return cfg, res


def tolerance_figures(preset: str, n_trials: int = 200):
    cfg = get_preset(preset)
    spec = ToleranceSpec.research_grade()
    print(f"[{preset}] tolerance MC ({n_trials} trials)...")
    mc = monte_carlo(cfg, spec, n_trials=n_trials, seed=0)
    sens = sensitivity(cfg, spec, metric="exit_drift_mrad", n_trials_per_param=30)
    bud = tolerance_budget(sens, delta_target=1.0)
    P.plot_mc_histograms(mc, os.path.join(FIG, f"{preset}_tol_mc_hist.png"))
    P.plot_sensitivity_bars(sens, os.path.join(FIG, f"{preset}_tol_sensitivity.png"),
                            metric="exit_drift_mrad")
    P.plot_tolerance_budget(bud, os.path.join(FIG, f"{preset}_tol_budget.png"))
    P.plot_exit_pointing(mc, os.path.join(FIG, f"{preset}_tol_exit_pointing.png"))


def pareto_figure(n_samples: int = 256):
    print(f"[pareto] search n={n_samples}...")
    df = pareto.pareto_search(n_samples=n_samples, seed=0,
                              objectives=("opl_m", "throughput"), verbose=False)
    front = df[df["on_pareto"]]
    P.plot_pareto(front, os.path.join(FIG, "pareto_front.png"),
                  x="opl_m", y="throughput")


def main():
    static_figures("bo_best_one_inch")
    static_figures("toroidal_lissajous")
    tolerance_figures("bo_best_one_inch", n_trials=200)
    pareto_figure(256)
    print(f"\nGallery written to {FIG}")


if __name__ == "__main__":
    main()
