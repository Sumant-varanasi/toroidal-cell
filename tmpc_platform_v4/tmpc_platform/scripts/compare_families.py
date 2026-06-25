"""Compare half_inch vs one_inch Thorlabs runs and produce:

  1. Side-by-side spot patterns (3D + mirror map + unfolded)
  2. Pareto front comparison
  3. Headline metrics table
  4. Comparison Markdown report

Reads from results_half_inch/ and results_one_inch/.
"""
import argparse, os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.gaussian_beam import (
    GaussianBeam, propagate_through_cell)
from tmpc_platform.physics_engine.losses import compute_losses


def _cfg_from_row(row) -> TMPCConfig:
    return TMPCConfig(
        N=int(row["N"]), R_ring=float(row["R_ring"]), H=float(row["H"]),
        R_t=float(row["R_t"]), R_s=float(row["R_s"]),
        mirror_aperture=float(row.get("mirror_aperture", 8.0)),
        chord_skip=int(row["chord_skip"]), w0=float(row["w0"]),
        input_offset_z=float(row.get("input_offset_z", 0.0)),
        input_angle=float(row.get("input_angle", 0.0)),
        reflectivity=float(row.get("reflectivity", 0.97)),
        n_passes=8 * int(row["N"]),
    )


def _best_cfg(family_dir: str):
    p = os.path.join(family_dir, "optim", "bo_best.csv")
    if not os.path.exists(p):
        return None, None
    row = pd.read_csv(p).iloc[0]
    cfg = _cfg_from_row(row)
    res = simulate_tmpc(cfg)
    loss = compute_losses(res.bounces, cfg.reflectivity, res.w_max,
                          cfg.mirror_aperture, 2 * cfg.w0, clipped=res.clipped)
    return cfg, (res, loss, row)


def _plot_side_by_side_spot(cfgA, resA, cfgB, resB, out_path):
    fig = plt.figure(figsize=(13, 5.5))
    for k, (cfg, res, title) in enumerate([
            (cfgA, resA, "Half-inch (CM127)"),
            (cfgB, resB, "One-inch (CM254)")], start=1):
        ax = fig.add_subplot(1, 2, k, projection="3d")
        sp = res.spot_pattern
        if len(sp) > 0:
            ax.plot(sp[:, 0], sp[:, 1], sp[:, 2], "-o", ms=3, lw=0.6)
        th = np.linspace(0, 2 * np.pi, cfg.N, endpoint=False)
        ax.scatter(cfg.R_ring * np.cos(th), cfg.R_ring * np.sin(th),
                   np.zeros_like(th), c="red", s=30)
        ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]"); ax.set_zlabel("z [mm]")
        ax.set_title(f"{title}\nN={cfg.N}  skip={cfg.chord_skip}  "
                     f"OPL={res.opl*1e-3:.2f} m")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _plot_pareto_overlay(half_dir, one_dir, out_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    for tag, color, d in [("half-inch", "tab:blue", half_dir),
                          ("one-inch",  "tab:orange", one_dir)]:
        p = os.path.join(d, "optim", "pareto.csv")
        if not os.path.exists(p): continue
        par = pd.read_csv(p)
        ax.scatter(par["obj_0"], par["obj_1"],
                   s=40, alpha=0.7, c=color, edgecolor="black",
                   label=f"{tag}  (n={len(par)})")
    ax.set_xlabel("OPL [m]"); ax.set_ylabel("Throughput")
    ax.set_title("Pareto front: half-inch vs one-inch")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _plot_dataset_overlay(half_dir, one_dir, out_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    for tag, color, d in [("half-inch", "tab:blue", half_dir),
                          ("one-inch",  "tab:orange", one_dir)]:
        p = os.path.join(d, "dataset.csv")
        if not os.path.exists(p): continue
        df = pd.read_csv(p)
        ax.scatter(df["opl_m"], df["throughput_full"], s=4, alpha=0.4,
                   c=color, label=f"{tag} (n={len(df)})")
    ax.set_xlabel("OPL [m]"); ax.set_ylabel("Throughput")
    ax.set_title("Full design space coverage")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _row(label, half_val, one_val, fmt="{:.3f}"):
    h = fmt.format(half_val) if half_val is not None else "—"
    o = fmt.format(one_val)  if one_val  is not None else "—"
    return f"| {label:<28s} | {h:>14s} | {o:>14s} |\n"


def _md_report(cfgA, packA, cfgB, packB, out_path):
    lines = ["# Thorlabs Family Comparison Report\n\n"]
    lines.append(f"| Quantity                     |   Half-inch    |    One-inch    |\n"
                 f"|------------------------------|---------------:|---------------:|\n")
    if packA and packB:
        rA, lA, rowA = packA
        rB, lB, rowB = packB
        lines.append(_row("SKU",     rowA.get("thorlabs_sku","?"), rowB.get("thorlabs_sku","?"), "{}"))
        lines.append(_row("N",       cfgA.N, cfgB.N, "{}"))
        lines.append(_row("chord_skip", cfgA.chord_skip, cfgB.chord_skip, "{}"))
        lines.append(_row("R_ring [mm]", cfgA.R_ring, cfgB.R_ring, "{:.2f}"))
        lines.append(_row("H [mm]",     cfgA.H,      cfgB.H,      "{:.2f}"))
        lines.append(_row("R_t = R_s [mm]", cfgA.R_t, cfgB.R_t,   "{:.1f}"))
        lines.append(_row("aperture [mm]", cfgA.mirror_aperture, cfgB.mirror_aperture, "{:.2f}"))
        lines.append(_row("w0 [mm]",   cfgA.w0,     cfgB.w0,     "{:.3f}"))
        lines.append(_row("bounces",   rA.bounces,  rB.bounces,  "{}"))
        lines.append(_row("OPL [m]",   rA.opl*1e-3, rB.opl*1e-3, "{:.3f}"))
        lines.append(_row("AOI mean [deg]", rA.aoi.mean() if len(rA.aoi) else 0,
                                            rB.aoi.mean() if len(rB.aoi) else 0, "{:.2f}"))
        lines.append(_row("AOI max [deg]",  rA.aoi.max()  if len(rA.aoi) else 0,
                                            rB.aoi.max()  if len(rB.aoi) else 0, "{:.2f}"))
        lines.append(_row("beam w_max [mm]", rA.w_max, rB.w_max, "{:.3f}"))
        lines.append(_row("vol. utilisation", rA.volume_utilisation,
                                              rB.volume_utilisation, "{:.3f}"))
        lines.append(_row("stability g²", rA.stability_g, rB.stability_g, "{:.4f}"))
        lines.append(_row("throughput",   lA.throughput,  lB.throughput,  "{:.4f}"))
        lines.append(_row("refl. loss",   lA.reflectivity_loss, lB.reflectivity_loss, "{:.4f}"))
        lines.append(_row("clipping loss",lA.clipping_loss, lB.clipping_loss, "{:.4f}"))
        lines.append(_row("aperture loss",lA.aperture_loss, lB.aperture_loss, "{:.4f}"))
        lines.append(_row("clipped",      "yes" if rA.clipped else "no",
                                          "yes" if rB.clipped else "no", "{}"))
    lines.append("\n")
    lines.append("## Files\n\n"
                 "- `comparison_spot_pattern.png` — 3D bounce trajectories side-by-side\n"
                 "- `comparison_pareto.png` — Pareto fronts (OPL vs throughput)\n"
                 "- `comparison_dataset.png` — full dataset coverage overlay\n"
                 "- `results_half_inch/` — full half-inch outputs (dashboard reads from here)\n"
                 "- `results_one_inch/` — full one-inch outputs\n")
    with open(out_path, "w") as f:
        f.writelines(lines)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--half", default="results_half_inch")
    ap.add_argument("--one",  default="results_one_inch")
    ap.add_argument("--out",  default="results_comparison")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cfgA, packA = _best_cfg(args.half)
    cfgB, packB = _best_cfg(args.one)

    if cfgA and cfgB:
        _plot_side_by_side_spot(cfgA, packA[0], cfgB, packB[0],
                                os.path.join(args.out, "comparison_spot_pattern.png"))
    _plot_pareto_overlay(args.half, args.one,
                         os.path.join(args.out, "comparison_pareto.png"))
    _plot_dataset_overlay(args.half, args.one,
                          os.path.join(args.out, "comparison_dataset.png"))

    rp = _md_report(cfgA, packA, cfgB, packB,
                    os.path.join(args.out, "comparison_report.md"))
    print(f"\n[compare] wrote {rp}")
    print(f"[compare] plots saved to {args.out}/")


if __name__ == "__main__":
    main()
