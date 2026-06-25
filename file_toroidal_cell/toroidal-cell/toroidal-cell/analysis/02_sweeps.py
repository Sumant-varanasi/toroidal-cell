"""
02_sweeps.py
============

Run every parameter sweep called out in the v1 reference doc, write
each as a CSV, and produce summary plots.

Sweep axes (from the reference doc):
    N      in {4, 6, 8, 12, 16, 24}                  (mirror count)
    R      in {30, 50, 75, 100} mm                   (ring radius)
    ROC    in {inf, 500, 1000, 2000} mm              (mirror curvature)
    R_ring in {0.97, 0.99, 0.995, 0.999}             (reflectivity)
    w0     in {0.5, 1.0, 1.5} mm                     (input waist)

For each combination we trace the cell, record OPL, throughput,
internal volume, beam metrics, and stability (where ROC is finite).
"""
from __future__ import annotations
import os, sys, math
import itertools
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from tmpc.geometry import (
    TMPCConfig, trace_cell, incident_angle_deg,
    distinct_spots_per_mirror, min_spot_separation, spots_overlap,
    mirror_fill_fraction, max_radial_extent,
)
from tmpc.losses import LossModel, per_pass_throughput
from tmpc.gaussian import (
    abcd_unit_cell, stability, mirror_focal_lengths,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PLOTS = os.path.abspath(os.path.join(HERE, "..", "results", "plots"))
CSVS  = os.path.abspath(os.path.join(HERE, "..", "results", "csv"))


# ---------------------------------------------------------------------------
def make_cfg(N: int, R_m: float, H_m: float, ROC_m: float,
              M_halfLaps: int, w0_m: float) -> TMPCConfig:
    return TMPCConfig(
        N=N, R=R_m, H=H_m, ROC=ROC_m, M_halfLaps=M_halfLaps, w0=w0_m,
    )


def evaluate(cfg: TMPCConfig, R_ring: float) -> dict:
    data = trace_cell(cfg)
    n_refl = int(data["pass_no"][-1])
    OPL = float(data["path_length"][-1])
    aperture = cfg.D_mirror / 2.0
    _, cumul = per_pass_throughput(
        data["spot_radius"], aperture,
        R_ring=R_ring, R_top=R_ring, top_bounce_index=n_refl // 2,
    )
    transmission = float(cumul[-1])
    w_max = max_radial_extent(data, cfg)
    sep   = min_spot_separation(data, cfg.N)
    fill  = mirror_fill_fraction(data, cfg)
    over  = spots_overlap(data, cfg)
    # Internal gas volume estimate: pi (R + D/2)^2 * H  (cylinder bounding
    # the ring of mirrors; treat as upper bound)
    V_int = math.pi * (cfg.R + cfg.D_mirror / 2.0) ** 2 * cfg.H * 1e6  # mL
    # Stability per plane if ROC is finite
    theta_i = math.radians(incident_angle_deg(cfg))
    if math.isfinite(cfg.ROC):
        leg_len = cfg.L_chord / math.cos(cfg.alpha_rad)
        Mt = abcd_unit_cell(leg_len, cfg.ROC, theta_i, plane="tangential")
        Ms = abcd_unit_cell(leg_len, cfg.ROC, theta_i, plane="sagittal")
        stab_t = stability(Mt)
        stab_s = stability(Ms)
        stable = (abs(stab_t) <= 1.0) and (abs(stab_s) <= 1.0)
    else:
        stab_t = stab_s = float("nan")
        stable = True   # flat mirrors are unconditionally stable for
                        # a finite path (no focusing instability)
    return {
        "N": cfg.N,
        "R_mm": cfg.R * 1e3,
        "H_mm": cfg.H * 1e3,
        "ROC_mm": cfg.ROC * 1e3 if math.isfinite(cfg.ROC) else float("inf"),
        "M_halfLaps": cfg.M_halfLaps,
        "w0_mm": cfg.w0 * 1e3,
        "R_ring": R_ring,
        "n_reflections": n_refl,
        "chord_mm": cfg.L_chord * 1e3,
        "AOI_deg": incident_angle_deg(cfg),
        "alpha_deg": math.degrees(cfg.alpha_rad),
        "OPL_m": OPL,
        "transmission": transmission,
        "w_max_mm": w_max * 1e3,
        "min_spot_sep_mm": sep * 1e3,
        "mirror_fill_frac": fill,
        "spots_overlap": int(over),
        "V_internal_mL": V_int,
        "stab_tangential": stab_t,
        "stab_sagittal":   stab_s,
        "stable":          int(stable),
        "utility_OPL_x_T": OPL * transmission,
    }


# ---------------------------------------------------------------------------
def sweep_N() -> pd.DataFrame:
    rows = []
    Ns = [4, 6, 8, 12, 16, 24]
    for N in Ns:
        # keep total reflections roughly 528 by adjusting M_halfLaps so
        # j_up = N M / 2 ~ 264
        M = max(2, 2 * round(264 / N))
        if (N * M) % 2 != 0:
            M += 1
        cfg = make_cfg(N=N, R_m=50e-3, H_m=40e-3, ROC_m=math.inf,
                        M_halfLaps=M, w0_m=1.0e-3)
        rows.append(evaluate(cfg, R_ring=0.99))
    return pd.DataFrame(rows)


def sweep_R() -> pd.DataFrame:
    rows = []
    Rs = [30e-3, 50e-3, 75e-3, 100e-3]
    for Rm in Rs:
        cfg = make_cfg(N=8, R_m=Rm, H_m=40e-3, ROC_m=math.inf,
                        M_halfLaps=66, w0_m=1.0e-3)
        rows.append(evaluate(cfg, R_ring=0.99))
    return pd.DataFrame(rows)


def sweep_ROC() -> pd.DataFrame:
    rows = []
    ROCs = [math.inf, 2.0, 1.0, 0.5]   # m
    for ROCm in ROCs:
        cfg = make_cfg(N=8, R_m=50e-3, H_m=40e-3, ROC_m=ROCm,
                        M_halfLaps=66, w0_m=1.0e-3)
        rows.append(evaluate(cfg, R_ring=0.99))
    return pd.DataFrame(rows)


def sweep_R_ring() -> pd.DataFrame:
    rows = []
    for Rv in [0.97, 0.99, 0.995, 0.999]:
        cfg = make_cfg(N=8, R_m=50e-3, H_m=40e-3, ROC_m=math.inf,
                        M_halfLaps=66, w0_m=1.0e-3)
        rows.append(evaluate(cfg, R_ring=Rv))
    return pd.DataFrame(rows)


def sweep_w0() -> pd.DataFrame:
    rows = []
    for w0m in [0.5e-3, 1.0e-3, 1.5e-3]:
        cfg = make_cfg(N=8, R_m=50e-3, H_m=40e-3, ROC_m=math.inf,
                        M_halfLaps=66, w0_m=w0m)
        rows.append(evaluate(cfg, R_ring=0.99))
    return pd.DataFrame(rows)


def sweep_N_x_R() -> pd.DataFrame:
    rows = []
    for N in [4, 6, 8, 12, 16, 24]:
        for Rm in [30e-3, 50e-3, 75e-3, 100e-3]:
            M = max(2, 2 * round(264 / N))
            if (N * M) % 2 != 0:
                M += 1
            cfg = make_cfg(N=N, R_m=Rm, H_m=40e-3, ROC_m=math.inf,
                            M_halfLaps=M, w0_m=1.0e-3)
            rows.append(evaluate(cfg, R_ring=0.99))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def make_plot(df: pd.DataFrame, x: str, y: str, path: str,
              log_y: bool = False, title: str | None = None,
              group: str | None = None) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.4))
    if group is None:
        ax.plot(df[x], df[y], "o-", color="#225588", lw=1.6, ms=6)
    else:
        for g, sub in df.groupby(group):
            ax.plot(sub[x], sub[y], "o-", lw=1.4, ms=5, label=f"{group}={g}")
        ax.legend(fontsize=9)
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} vs {x}")
    ax.grid(True, which="both" if log_y else "major", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def make_heatmap(df: pd.DataFrame, x: str, y: str, z: str,
                 path: str, log_z: bool = False, title: str | None = None
                 ) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = df[x].values
    ys = df[y].values
    zs = df[z].values
    if log_z:
        zs = np.log10(np.clip(zs, 1e-30, None))
        clabel = f"log10({z})"
    else:
        clabel = z
    sc = ax.scatter(xs, ys, c=zs, s=120, cmap="viridis",
                    edgecolors="black", lw=0.4)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{z} vs ({x}, {y})")
    plt.colorbar(sc, ax=ax, label=clabel)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def main() -> None:
    print("Running parameter sweeps...")

    df_N = sweep_N();   df_N.to_csv(os.path.join(CSVS, "sweep_N.csv"), index=False)
    print("  sweep_N done.")
    df_R = sweep_R();   df_R.to_csv(os.path.join(CSVS, "sweep_R.csv"), index=False)
    print("  sweep_R done.")
    df_ROC = sweep_ROC(); df_ROC.to_csv(os.path.join(CSVS, "sweep_ROC.csv"), index=False)
    print("  sweep_ROC done.")
    df_Rr = sweep_R_ring(); df_Rr.to_csv(os.path.join(CSVS, "sweep_R_ring.csv"), index=False)
    print("  sweep_R_ring done.")
    df_w  = sweep_w0(); df_w.to_csv(os.path.join(CSVS, "sweep_w0.csv"), index=False)
    print("  sweep_w0 done.")
    df_NR = sweep_N_x_R(); df_NR.to_csv(os.path.join(CSVS, "sweep_N_x_R.csv"), index=False)
    print("  sweep_N_x_R done.")

    # -------- summary plots ------------------------------------------------
    make_plot(df_N, "N", "OPL_m",
              os.path.join(PLOTS, "fig_sweep_N_OPL.png"),
              title="OPL vs mirror count N  (R=50 mm, M~264 reflections)")
    make_plot(df_N, "N", "transmission",
              os.path.join(PLOTS, "fig_sweep_N_T.png"), log_y=True,
              title="Throughput vs mirror count N  (R_ring=0.99)")
    make_plot(df_N, "N", "AOI_deg",
              os.path.join(PLOTS, "fig_sweep_N_AOI.png"),
              title="Angle of incidence vs mirror count N  (pi/2 - pi/N)")

    make_plot(df_R, "R_mm", "OPL_m",
              os.path.join(PLOTS, "fig_sweep_R_OPL.png"),
              title="OPL vs ring radius R  (N=8, M=66 half-laps)")
    make_plot(df_R, "R_mm", "V_internal_mL",
              os.path.join(PLOTS, "fig_sweep_R_volume.png"),
              title="Cell volume bound vs ring radius R")

    make_plot(df_Rr, "R_ring", "transmission",
              os.path.join(PLOTS, "fig_sweep_Rring_T.png"), log_y=True,
              title=f"Transmission vs mirror reflectivity  "
                    f"(N=8, R=50 mm, n_refl=528)")

    make_plot(df_w, "w0_mm", "w_max_mm",
              os.path.join(PLOTS, "fig_sweep_w0_wmax.png"),
              title="Max in-cell spot radius vs input waist  (1/e^2)")
    make_plot(df_w, "w0_mm", "mirror_fill_frac",
              os.path.join(PLOTS, "fig_sweep_w0_fill.png"),
              title="Mirror fill fraction vs input waist")

    make_plot(df_ROC, "ROC_mm", "stab_tangential",
              os.path.join(PLOTS, "fig_sweep_ROC_stability.png"),
              title="Stability parameter (tangential plane) vs ROC")

    make_heatmap(df_NR, "N", "R_mm", "OPL_m",
                 os.path.join(PLOTS, "fig_heatmap_N_R_OPL.png"),
                 title="OPL [m] vs (N, R)")
    make_heatmap(df_NR, "N", "R_mm", "utility_OPL_x_T",
                 os.path.join(PLOTS, "fig_heatmap_N_R_utility.png"),
                 title="OPL × throughput vs (N, R)  (R_ring=0.99)")

    print(f"\nSweep CSVs in {CSVS}")
    print(f"Sweep plots in {PLOTS}")


if __name__ == "__main__":
    main()
