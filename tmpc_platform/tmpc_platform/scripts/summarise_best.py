"""One-page physics summary of the best design.

Prints the BO best and top-N Pareto configs with full per-bounce diagnostics.

Usage:
    python -m tmpc_platform.scripts.summarise_best
    python -m tmpc_platform.scripts.summarise_best --top 5
"""
import argparse, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.gaussian_beam import GaussianBeam, propagate_through_cell
from tmpc_platform.physics_engine.losses import compute_losses


def _cfg_from_row(row) -> TMPCConfig:
    return TMPCConfig(
        N=int(row["N"]), R_ring=float(row["R_ring"]), H=float(row["H"]),
        R_t=float(row["R_t"]), R_s=float(row["R_s"]),
        mirror_aperture=float(row.get("mirror_aperture", 8.0)),
        chord_skip=int(row["chord_skip"]), w0=float(row["w0"]),
        input_offset_z=float(row.get("input_offset_z", 0.0)),
        input_angle=float(row.get("input_angle", 0.0)),
        n_passes=8 * int(row["N"]),
    )


def _report(cfg: TMPCConfig, title: str):
    res = simulate_tmpc(cfg)
    loss = compute_losses(res.bounces, cfg.reflectivity, res.w_max,
                          cfg.mirror_aperture, 2 * cfg.w0, clipped=res.clipped)
    chord = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    beam = GaussianBeam(wavelength=cfg.wavelength, w0=cfg.w0)
    prop = propagate_through_cell(beam, [chord] * cfg.n_passes,
                                  [cfg.R_t / 2] * cfg.n_passes,
                                  [cfg.R_s / 2] * cfg.n_passes)

    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)
    print(f"GEOMETRY     N={cfg.N}   chord_skip={cfg.chord_skip}   "
          f"R_ring={cfg.R_ring:.1f} mm   H={cfg.H:.1f} mm")
    print(f"MIRROR       R_t={cfg.R_t:.1f} mm   R_s={cfg.R_s:.1f} mm   "
          f"aperture={cfg.mirror_aperture:.1f} mm   R={cfg.reflectivity:.4f}")
    print(f"BEAM         lambda={cfg.wavelength*1e6:.1f} nm   w0={cfg.w0:.3f} mm   "
          f"z_off={cfg.input_offset_z:.2f} mm   tilt={cfg.input_angle*1e3:.2f} mrad")
    print()
    print(f"BOUNCES        {res.bounces:>6d}")
    print(f"OPL            {res.opl*1e-3:>6.3f}  m       "
          f"(chord/bounce = {chord:.2f} mm)")
    print(f"AOI mean       {res.aoi.mean():>6.2f}  deg")
    print(f"AOI max        {res.aoi.max():>6.2f}  deg")
    print(f"AOI std        {res.aoi.std():>6.2f}  deg")
    print(f"Beam w_max     {res.w_max:>6.3f}  mm     "
          f"(aperture {cfg.mirror_aperture:.2f} mm)")
    print(f"Vol. util.     {res.volume_utilisation*100:>6.2f}  %")
    print(f"Stability g²   {res.stability_g:>6.4f}        "
          f"{'STABLE' if 0 <= res.stability_g <= 1 else 'UNSTABLE'}")
    print(f"Clipped        {'YES' if res.clipped else 'no':>6}")
    print()
    print(f"LOSS BUDGET")
    print(f"  reflectivity loss  {loss.reflectivity_loss*100:>6.3f} %")
    print(f"  clipping loss      {loss.clipping_loss*100:>6.3f} %")
    print(f"  aperture loss      {loss.aperture_loss*100:>6.3f} %")
    print(f"  truncation loss    {loss.truncation_loss*100:>6.3f} %")
    print(f"  -----------------------------")
    print(f"  total throughput   {loss.throughput*100:>6.3f} %")
    print()
    # AOI histogram (text)
    if len(res.aoi):
        hist, edges = np.histogram(res.aoi, bins=10)
        print("AOI distribution:")
        max_h = max(hist) or 1
        for h, lo, hi in zip(hist, edges[:-1], edges[1:]):
            bar = "█" * int(20 * h / max_h)
            print(f"  {lo:5.1f}-{hi:5.1f}°  {bar:<20s} ({h})")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--optim", default="results/optim")
    ap.add_argument("--top", type=int, default=3,
                    help="how many Pareto configs to report")
    args = ap.parse_args()

    bo_path = os.path.join(args.optim, "bo_best.csv")
    if os.path.exists(bo_path):
        bo = pd.read_csv(bo_path).iloc[0]
        _report(_cfg_from_row(bo), "BAYESIAN-OPT BEST DESIGN")

    par_path = os.path.join(args.optim, "pareto.csv")
    if os.path.exists(par_path):
        par = pd.read_csv(par_path)
        # rank by sum of (normalised) objectives
        normed = par.copy()
        for col in [c for c in par.columns if c.startswith("obj_")]:
            v = par[col]
            normed[col] = (v - v.min()) / (v.max() - v.min() + 1e-12)
        par = par.assign(_score=normed[[c for c in par.columns
                                        if c.startswith("obj_")]].sum(axis=1))
        par = par.sort_values("_score", ascending=False)
        for i, (_, row) in enumerate(par.head(args.top).iterrows(), start=1):
            _report(_cfg_from_row(row),
                    f"PARETO TOP-{i}   "
                    f"OPL={row.get('obj_0',0):.2f}m  "
                    f"throughput={row.get('obj_1',0):.3f}")


if __name__ == "__main__":
    main()
