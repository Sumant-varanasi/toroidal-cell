"""Static + interactive light-path figures for the drone presets.

Writes, per preset, into drone_20m/designs/figures/:
    <preset>_cell3d.png / .html        3-D mirror ring + traced beam path
    <preset>_cell3d_static.png         matplotlib 3-D fallback view
    <preset>_experiment.png / .html    photoreal as-built render
    <preset>_constellations.png/.html  per-mirror spot patterns
    <preset>_spot_pattern.png          top-down path/spot figure
    <preset>_beam_evolution.png        beam radius vs bounce

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/make_figures.py
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.presets import get_preset                   # noqa: E402
from tmpc_platform_v5 import plots as P                           # noqa: E402
from tmpc_platform_v5 import viz3d, render                        # noqa: E402

FIG = os.path.join(_HERE, "designs", "figures")
os.makedirs(FIG, exist_ok=True)


def _png(fig, path, width=1100, height=800):
    try:
        fig.write_image(path, width=width, height=height, scale=1)
        print(f"  png -> {os.path.basename(path)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"  (png export skipped for {os.path.basename(path)}: {e})")


def figures(preset: str):
    cfg = get_preset(preset)
    res = simulate_tmpc(cfg)
    print(f"[{preset}] bounces={res.bounces} OPL={res.opl*1e-3:.2f} m")

    P.plot_spot_pattern(res.spot_pattern, cfg,
                        os.path.join(FIG, f"{preset}_spot_pattern.png"))
    P.plot_beam_evolution(res.w_tangential, res.w_sagittal,
                          cfg.mirror_aperture,
                          os.path.join(FIG, f"{preset}_beam_evolution.png"))
    P.plot_cell_3d(res, cfg,
                   os.path.join(FIG, f"{preset}_cell3d_static.png"))

    cell = viz3d.build_cell_figure(res, cfg, label=preset)
    cell.write_html(os.path.join(FIG, f"{preset}_cell3d.html"),
                    include_plotlyjs="cdn", full_html=True)
    _png(cell, os.path.join(FIG, f"{preset}_cell3d.png"))

    const = viz3d.build_constellations(cfg, res.spot_pattern,
                                       res.mirror_sequence, "raytrace")
    const.write_html(os.path.join(FIG, f"{preset}_constellations.html"),
                     include_plotlyjs="cdn", full_html=True)
    _png(const, os.path.join(FIG, f"{preset}_constellations.png"),
         width=1100, height=900)

    exp_html = os.path.join(FIG, f"{preset}_experiment.html")
    _, exp_fig = render.render_experiment(res, cfg, exp_html,
                                          family="one_inch",
                                          return_fig=True)
    _png(exp_fig, os.path.join(FIG, f"{preset}_experiment.png"),
         width=1100, height=850)


def main():
    for preset in ("drone_20m", "drone_25m", "drone_22m", "drone_16cm",
                   "drone_29m", "drone_14cm"):
        figures(preset)
    print(f"\nFigures written to {FIG}")


if __name__ == "__main__":
    main()
