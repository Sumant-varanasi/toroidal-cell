"""
03_optimize.py
==============

Run three optimisers (SciPy Powell, GA, PSO) on the toroidal multipass
cell under two operating regimes:

  Regime A  (overlap-tolerant): cell operated as a diffuse absorption
            volume; spots may overlap.  Maximises OPL * throughput.

  Regime B  (overlap-strict):   each pass must occupy a distinct spot
            on the mirror surface.  Adds a penalty term to discourage
            spot overlap.

Decision vector
---------------
x = [R, H, M_halfLaps, w0, R_ring]
N held fixed at 8 for the headline run.

Outputs
-------
results/csv/optimization_summary.csv          comparison of methods, both regimes
results/csv/optimization_data.csv             schema from Phase 6 spec
results/csv/optimization_per_N.csv            best design vs N (regime A)
results/plots/fig_optimiser_compare.png
results/plots/fig_optimiser_per_N.png
"""
from __future__ import annotations
import os, sys, math, time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from tmpc.geometry import TMPCConfig, trace_cell
from tmpc.losses import LossModel, per_pass_throughput
from tmpc.optimize import (
    optimise_scipy, optimise_ga, optimise_pso, _decode, _utility,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PLOTS = os.path.abspath(os.path.join(HERE, "..", "results", "plots"))
CSVS  = os.path.abspath(os.path.join(HERE, "..", "results", "csv"))


def describe(res, name: str, regime: str) -> dict:
    R, H, Mh, w0, Rr = res.x
    return {
        "regime": regime,
        "method": name,
        "R_mm": R * 1e3,
        "H_mm": H * 1e3,
        "M_halfLaps": int(round(Mh)),
        "w0_mm": w0 * 1e3,
        "R_ring": Rr,
        "OPL_m": res.OPL,
        "throughput": res.throughput,
        "utility": res.utility,
        "n_evals": res.n_evals,
    }


def run_regime(regime_name: str, overlap_strict: bool) -> pd.DataFrame:
    print(f"\n== Regime: {regime_name}  (overlap_strict={overlap_strict}) ==")
    rows = []
    t0 = time.time()
    r = optimise_scipy(N=8, maxiter=800, overlap_strict=overlap_strict)
    print(f"  SciPy/Powell: U={r.utility:.3f}, OPL={r.OPL:.2f} m, "
          f"T={r.throughput:.3f}, evals={r.n_evals}, "
          f"time={time.time()-t0:.1f}s")
    rows.append(describe(r, "SciPy/Powell", regime_name))

    t0 = time.time()
    r = optimise_ga(N=8, pop_size=40, n_generations=40, seed=42,
                     overlap_strict=overlap_strict)
    print(f"  GA          : U={r.utility:.3f}, OPL={r.OPL:.2f} m, "
          f"T={r.throughput:.3f}, evals={r.n_evals}, "
          f"time={time.time()-t0:.1f}s")
    rows.append(describe(r, "GA", regime_name))

    t0 = time.time()
    r = optimise_pso(N=8, n_particles=30, n_iters=40, seed=7,
                      overlap_strict=overlap_strict)
    print(f"  PSO         : U={r.utility:.3f}, OPL={r.OPL:.2f} m, "
          f"T={r.throughput:.3f}, evals={r.n_evals}, "
          f"time={time.time()-t0:.1f}s")
    rows.append(describe(r, "PSO", regime_name))
    return pd.DataFrame(rows)


def main() -> None:
    df_A = run_regime("overlap_tolerant",  overlap_strict=False)
    df_B = run_regime("overlap_strict",    overlap_strict=True)
    df_summary = pd.concat([df_A, df_B], ignore_index=True)
    df_summary.to_csv(os.path.join(CSVS, "optimization_summary.csv"),
                      index=False)
    print("\nOptimiser comparison (both regimes):")
    print(df_summary.to_string(index=False))

    # ----- Phase 6 schema: Optimization_data.csv -----
    # Sample 60 random configurations + the 6 optimised endpoints.
    rows = []
    config_id = 0
    rng = np.random.default_rng(2026)
    lb = np.array([30e-3,   20e-3,   10,   0.3e-3,   0.95])
    ub = np.array([100e-3,  60e-3,   200,  2.0e-3,   0.999])
    for _ in range(60):
        x = lb + (ub - lb) * rng.random(5)
        try:
            cfg, lm = _decode(x, N=8)
            U, OPL, T = _utility(cfg, lm, overlap_strict=False)
            rows.append({
                "Configuration_ID": str(config_id),
                "Mirror_Spacing": round(cfg.L_chord * 1e3, 4),
                "Tilt_Angle":     round(math.degrees(cfg.alpha_rad), 5),
                "Rotation_Angle": round(360.0 / cfg.N, 3),
                "Number_of_Passes": int(cfg.total_reflections),
                "Optical_Path_Length": round(OPL, 4),
                "Efficiency":          round(T, 6),
            })
        except Exception:
            pass
        config_id += 1
    for _, row in df_summary.iterrows():
        rows.append({
            "Configuration_ID": f"{row['regime']}__{row['method']}",
            "Mirror_Spacing": round(2 * row["R_mm"] * math.sin(math.pi / 8), 4),
            "Tilt_Angle":     round(math.degrees(math.atan2(
                row["H_mm"] * 1e-3, 4 * row["M_halfLaps"]
                * 2 * row["R_mm"] * 1e-3 * math.sin(math.pi / 8))), 5),
            "Rotation_Angle": 45.0,    # 360/8
            "Number_of_Passes": int(8 * row["M_halfLaps"]),
            "Optical_Path_Length": round(row["OPL_m"], 4),
            "Efficiency":          round(row["throughput"], 6),
        })
    pd.DataFrame(rows).to_csv(os.path.join(CSVS, "optimization_data.csv"),
                              index=False)
    print(f"\noptimization_data.csv written  ({len(rows)} rows)")

    # ----- comparison bar plot -----
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.35
    methods = ["SciPy/Powell", "GA", "PSO"]
    A_U = df_A.set_index("method").loc[methods, "utility"].values
    B_U = df_B.set_index("method").loc[methods, "utility"].values
    A_OPL = df_A.set_index("method").loc[methods, "OPL_m"].values
    B_OPL = df_B.set_index("method").loc[methods, "OPL_m"].values
    x = np.arange(len(methods))
    b1 = ax.bar(x - width/2, A_U, width, color="#225588",
                label="overlap-tolerant")
    b2 = ax.bar(x + width/2, B_U, width, color="#cc6644",
                label="overlap-strict")
    for b, u, o in zip(b1, A_U, A_OPL):
        ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                f"U={u:.2f}\nOPL={o:.1f}m", ha="center", va="bottom",
                fontsize=8)
    for b, u, o in zip(b2, B_U, B_OPL):
        ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                f"U={u:.2f}\nOPL={o:.1f}m", ha="center", va="bottom",
                fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.set_ylabel("utility")
    ax.set_title("Optimiser comparison  (N=8 fixed, decision vec "
                 "[R, H, M, w₀, R_ring])")
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "fig_optimiser_compare.png"), dpi=140)
    plt.close(fig)

    # ----- per-N optimisation (regime A only) -----
    print("\nRunning per-N SciPy optimisation (regime A)...")
    rows_N = []
    for N in [4, 6, 8, 12, 16, 24]:
        x0 = np.array([50e-3, 40e-3, max(4, 528 // N), 1.0e-3, 0.995])
        try:
            r = optimise_scipy(N=N, x0=x0, maxiter=400, overlap_strict=False)
            rows_N.append({
                "N": N,
                "R_mm": r.x[0] * 1e3,
                "H_mm": r.x[1] * 1e3,
                "M_halfLaps": int(round(r.x[2])),
                "w0_mm": r.x[3] * 1e3,
                "R_ring": r.x[4],
                "OPL_m": r.OPL,
                "throughput": r.throughput,
                "utility": r.utility,
            })
            print(f"  N={N:3d}: U={r.utility:.3f}, "
                  f"OPL={r.OPL:.2f}, T={r.throughput:.3f}")
        except Exception as e:
            print(f"  N={N}: failed ({e})")
    df_N_opt = pd.DataFrame(rows_N)
    df_N_opt.to_csv(os.path.join(CSVS, "optimization_per_N.csv"), index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax2 = ax.twinx()
    ax.plot(df_N_opt["N"], df_N_opt["OPL_m"], "o-", color="#225588",
            lw=1.6, ms=7, label="OPL [m]")
    ax2.plot(df_N_opt["N"], df_N_opt["throughput"], "s--", color="#cc4444",
             lw=1.4, ms=7, label="throughput")
    ax.set_xlabel("number of ring mirrors N")
    ax.set_ylabel("OPL [m]", color="#225588")
    ax2.set_ylabel("throughput", color="#cc4444")
    ax.set_title("Optimised design vs N  (regime A — overlap-tolerant)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "fig_optimiser_per_N.png"), dpi=140)
    plt.close(fig)

    print("\nDone.")


if __name__ == "__main__":
    main()
