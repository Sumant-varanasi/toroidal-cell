"""
01_baseline.py
==============

Run the v1 reference design (N=8, R=50 mm, H=40 mm, ROC=inf, w0=1 mm,
R_ring sweep) and produce the four headline figures plus a baseline
summary CSV.

Outputs (in ../results/plots/ and ../results/csv/):
    fig_topdown_v1.png           — in-plane chord pattern
    fig_spotpatterns_v1.png      — spot pattern on each ring mirror
    fig_beam_evolution_v1.png    — Gaussian spot radius vs path
    fig_throughput_v1.png        — cumulative transmission vs path
                                    (one curve per R_ring value)
    fig_reflectivity_budget.png  — semi-log throughput-vs-N_bounces
                                    for the standard R values
    baseline_summary.csv         — single-row summary of the v1 design
"""
from __future__ import annotations
import os, sys, math, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from tmpc.geometry import (
    TMPCConfig, trace_cell, incident_angle_deg,
    distinct_spots_per_mirror, min_spot_separation, spots_overlap,
    mirror_fill_fraction, max_radial_extent,
)
from tmpc.losses import LossModel, per_pass_throughput, mirror_loss_breakdown
from tmpc.plotting import (
    plot_topdown, plot_spot_patterns, plot_beam_evolution, plot_throughput,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PLOTS = os.path.abspath(os.path.join(HERE, "..", "results", "plots"))
CSVS  = os.path.abspath(os.path.join(HERE, "..", "results", "csv"))
os.makedirs(PLOTS, exist_ok=True)
os.makedirs(CSVS,  exist_ok=True)


def main() -> None:
    cfg = TMPCConfig()                    # v1 defaults
    data = trace_cell(cfg)

    # -- diagnostics -------------------------------------------------------
    OPL = float(data["path_length"][-1])
    n_refl = int(data["pass_no"][-1])
    w_max  = max_radial_extent(data, cfg)
    sep    = min_spot_separation(data, cfg.N)
    fill   = mirror_fill_fraction(data, cfg)
    overlap = spots_overlap(data, cfg)
    theta_i = incident_angle_deg(cfg)
    alpha_deg = math.degrees(cfg.alpha_rad)

    print(f"OPL design            : {cfg.OPL_design:.4f} m")
    print(f"OPL traced            : {OPL:.4f} m")
    print(f"Reflections (total)   : {n_refl}")
    print(f"Chord length          : {cfg.L_chord*1e3:.3f} mm")
    print(f"AOI                   : {theta_i:.3f} deg")
    print(f"alpha (out-of-plane)  : {alpha_deg:.4f} deg")
    print(f"max spot radius       : {w_max*1e3:.3f} mm  (D/2 = "
          f"{cfg.D_mirror/2*1e3:.2f} mm)")
    print(f"min spot separation   : {sep*1e3:.4f} mm")
    print(f"mirror fill fraction  : {fill:.3f}")
    print(f"spots overlap?        : {overlap}")

    # -- plots -------------------------------------------------------------
    plot_topdown(cfg, data,        os.path.join(PLOTS, "fig_topdown_v1.png"))
    plot_spot_patterns(cfg, data,  os.path.join(PLOTS, "fig_spotpatterns_v1.png"))
    plot_beam_evolution(cfg, data, os.path.join(PLOTS, "fig_beam_evolution_v1.png"))

    # -- throughput at multiple R_ring values -----------------------------
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    R_values = [0.97, 0.99, 0.995, 0.999]
    summary_rows = []
    for Rv in R_values:
        lm = LossModel(R_ring=Rv, R_top=Rv)
        _, cumul = per_pass_throughput(
            data["spot_radius"], cfg.D_mirror / 2.0,
            R_ring=Rv, R_top=Rv, top_bounce_index=n_refl // 2,
        )
        ax.semilogy(data["path_length"], cumul, lw=1.4,
                    label=f"R = {Rv:.3f}  (final = {cumul[-1]:.2e})")
        summary_rows.append({
            "R_ring": Rv,
            "throughput_final": float(cumul[-1]),
            "OPL_m": OPL,
        })
    ax.axhline(1e-3, color="grey", lw=0.7, linestyle=":")
    ax.set_xlabel("cumulative optical path length [m]")
    ax.set_ylabel("transmission")
    ax.set_title("v1 cell — cumulative throughput vs path "
                 f"(N={cfg.N}, R={cfg.R*1e3:.0f} mm, "
                 f"OPL={OPL:.2f} m, n_refl={n_refl})")
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "fig_throughput_v1.png"), dpi=140)
    plt.close(fig)

    # -- reflectivity-budget diagnostic figure -----------------------------
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    n_arr = np.arange(1, 1001)
    for Rv in R_values:
        ax.semilogy(n_arr, Rv ** n_arr, lw=1.3, label=f"R = {Rv}")
    ax.axvline(n_refl, color="black", linestyle="--", lw=1,
               label=f"v1 design  n = {n_refl}")
    ax.set_xlabel("number of reflections")
    ax.set_ylabel("R^n")
    ax.set_title("Reflectivity budget — power surviving after n bounces")
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "fig_reflectivity_budget.png"), dpi=140)
    plt.close(fig)

    # -- baseline summary CSV ---------------------------------------------
    df = pd.DataFrame([
        {
            "Parameter": "N_mirrors",          "Value": cfg.N,
            "Units": "—", "Notes": "ring mirrors",
        },
        {
            "Parameter": "R_ring_radius",      "Value": cfg.R*1e3,
            "Units": "mm", "Notes": "centre of mirror to cell axis",
        },
        {
            "Parameter": "H_cell_height",      "Value": cfg.H*1e3,
            "Units": "mm", "Notes": "axial extent (entry plane to top retro)",
        },
        {
            "Parameter": "D_mirror",           "Value": cfg.D_mirror*1e3,
            "Units": "mm", "Notes": "ring mirror diameter",
        },
        {
            "Parameter": "ROC",                "Value": cfg.ROC,
            "Units": "m", "Notes": "inf = flat (v1)",
        },
        {
            "Parameter": "chord_length",       "Value": cfg.L_chord*1e3,
            "Units": "mm", "Notes": "2 R sin(pi/N)",
        },
        {
            "Parameter": "AOI",                "Value": theta_i,
            "Units": "deg", "Notes": "pi/2 - pi/N",
        },
        {
            "Parameter": "alpha_outOfPlane",   "Value": alpha_deg,
            "Units": "deg", "Notes": "out-of-plane spiral tilt",
        },
        {
            "Parameter": "M_halfLaps",         "Value": cfg.M_halfLaps,
            "Units": "—", "Notes": "half-laps before top retro",
        },
        {
            "Parameter": "j_up",               "Value": cfg.N * cfg.M_halfLaps // 2,
            "Units": "—", "Notes": "upgoing reflections",
        },
        {
            "Parameter": "n_reflections_total", "Value": n_refl,
            "Units": "—", "Notes": "ring bounces (2 j_up); top retro folded in",
        },
        {
            "Parameter": "OPL_traced",         "Value": OPL,
            "Units": "m", "Notes": "cumulative path at exit",
        },
        {
            "Parameter": "wavelength",         "Value": cfg.wavelength*1e6,
            "Units": "um", "Notes": "CH4 R(3) line, 2 nu3 band",
        },
        {
            "Parameter": "w0_input",           "Value": cfg.w0*1e3,
            "Units": "mm", "Notes": "1/e^2 input waist",
        },
        {
            "Parameter": "M2",                 "Value": cfg.M2,
            "Units": "—", "Notes": "beam quality",
        },
        {
            "Parameter": "w_max",              "Value": w_max*1e3,
            "Units": "mm", "Notes": "max spot radius on any mirror",
        },
        {
            "Parameter": "min_spot_sep",       "Value": sep*1e3,
            "Units": "mm", "Notes": "smallest centre-to-centre separation",
        },
        {
            "Parameter": "mirror_fill_frac",   "Value": fill,
            "Units": "—", "Notes": "geometric beam coverage of busiest mirror",
        },
        {
            "Parameter": "spots_overlap_flag", "Value": int(overlap),
            "Units": "—", "Notes": "1 = at least one pair within 2 w_mean",
        },
    ])
    df.to_csv(os.path.join(CSVS, "baseline_summary.csv"), index=False)

    print(f"\nBaseline plots written to {PLOTS}")
    print(f"Baseline summary CSV written to {CSVS}/baseline_summary.csv")


if __name__ == "__main__":
    main()
