"""Stage 5: produce all publication plots."""
import argparse, os, sys, joblib, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.gaussian_beam import GaussianBeam, propagate_through_cell
from tmpc_platform.visualization import (
    plot_spot_pattern, plot_roc_vs_opl, plot_stability_landscape,
    plot_metrics_table, plot_beam_evolution, plot_pareto,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default="results/dataset.csv")
    ap.add_argument("--models", type=str, default="results/models")
    ap.add_argument("--optim", type=str, default="results/optim")
    ap.add_argument("--out", type=str, default="results/plots")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    df = pd.read_csv(args.data)
    print(f"[05] Plotting from dataset: {df.shape}")

    plot_roc_vs_opl(df, os.path.join(args.out, "roc_vs_opl.png"))
    plot_stability_landscape(df, os.path.join(args.out, "stability_landscape.png"))

    # surrogate metrics
    m = os.path.join(args.models, "metrics.csv")
    if os.path.exists(m):
        plot_metrics_table(pd.read_csv(m), os.path.join(args.out, "metrics_table.png"))

    # representative spot pattern: best quality config
    best = df.sort_values("quality", ascending=False).iloc[0]
    cfg = TMPCConfig(
        N=int(best["N"]), R_ring=float(best["R_ring"]), H=float(best["H"]),
        R_t=float(best["R_t"]), R_s=float(best["R_s"]),
        mirror_aperture=8.0, chord_skip=int(best["chord_skip"]),
        w0=float(best["w0"]),
    )
    cfg.n_passes = 8 * cfg.N
    res = simulate_tmpc(cfg)
    print(f"[05] Best-quality config: N={cfg.N}, skip={cfg.chord_skip}, "
          f"OPL={res.opl*1e-3:.2f} m, throughput={res.throughput:.3f}")
    if len(res.spot_pattern) > 1:
        plot_spot_pattern(res.spot_pattern, cfg,
                          os.path.join(args.out, "spot_pattern_best.png"))

    # beam evolution
    chord = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    beam = GaussianBeam(wavelength=cfg.wavelength, w0=cfg.w0)
    prop = propagate_through_cell(beam, [chord]*cfg.n_passes,
                                  [cfg.R_t/2]*cfg.n_passes,
                                  [cfg.R_s/2]*cfg.n_passes)
    plot_beam_evolution(prop["w_tangential"], prop["w_sagittal"],
                        cfg.mirror_aperture,
                        os.path.join(args.out, "beam_evolution.png"))

    # pareto
    p = os.path.join(args.optim, "pareto.csv")
    if os.path.exists(p):
        plot_pareto(pd.read_csv(p),
                    os.path.join(args.out, "pareto_front.png"),
                    obj_names=["OPL [m]", "Throughput", "-Clipping"])


if __name__ == "__main__":
    main()
