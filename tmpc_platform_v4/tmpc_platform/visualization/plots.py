"""All publication-quality plots produced by the platform."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def _save(fig, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_spot_pattern(spots: np.ndarray, cfg, out_path: str):
    fig = plt.figure(figsize=(11, 5))
    # 3D view
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax1.plot(spots[:, 0], spots[:, 1], spots[:, 2], "-o", ms=2, lw=0.6)
    ax1.set_xlabel("x [mm]"); ax1.set_ylabel("y [mm]"); ax1.set_zlabel("z [mm]")
    ax1.set_title(f"Bounce trajectory (N={cfg.N}, skip={cfg.chord_skip})")
    # mirror locations
    th = np.linspace(0, 2*np.pi, cfg.N, endpoint=False)
    ax1.scatter(cfg.R_ring*np.cos(th), cfg.R_ring*np.sin(th),
                np.zeros_like(th), c="red", s=20)
    # 2D unfolded (mirror index vs z)
    ax2 = fig.add_subplot(1, 2, 2)
    angles = np.arctan2(spots[:, 1], spots[:, 0])
    ax2.plot(np.degrees(angles), spots[:, 2], "-o", ms=2, lw=0.6)
    ax2.set_xlabel("Azimuth [deg]"); ax2.set_ylabel("z [mm]")
    ax2.set_title("Unfolded spot pattern")
    ax2.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_beam_evolution(w_t, w_s, aperture, out_path: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(w_t, label="tangential", lw=1.8)
    ax.plot(w_s, label="sagittal", lw=1.8)
    ax.axhline(aperture, color="r", ls="--", lw=1, label="aperture")
    ax.set_xlabel("Bounce index"); ax.set_ylabel("Beam radius [mm]")
    ax.set_title("Gaussian beam evolution through the cell")
    ax.legend(); ax.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_roc_vs_opl(df: pd.DataFrame, out_path: str,
                    x: str = "R_t", y: str = "opl_m", c: str = "throughput_full"):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sc = ax.scatter(df[x], df[y], c=df[c], s=10, cmap="viridis", alpha=0.7)
    fig.colorbar(sc, ax=ax, label=c)
    ax.set_xlabel(x); ax.set_ylabel(y)
    ax.set_title(f"{y} vs {x}")
    ax.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_stability_landscape(df: pd.DataFrame, out_path: str):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sc = ax.scatter(df["R_t"], df["R_ring"], c=df["stability_g"],
                    s=10, cmap="coolwarm", vmin=0, vmax=1.5, alpha=0.8)
    fig.colorbar(sc, ax=ax, label="stability g²")
    ax.set_xlabel("R_t [mm]"); ax.set_ylabel("R_ring [mm]")
    ax.set_title("Stability landscape")
    return _save(fig, out_path)


def plot_pareto(pareto_df: pd.DataFrame, out_path: str, obj_names=None):
    cols = [c for c in pareto_df.columns if c.startswith("obj_")]
    if len(cols) < 2:
        return None
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pareto_df[cols[0]], pareto_df[cols[1]],
               s=25, edgecolor="k", facecolor="C0")
    name0, name1 = (obj_names or cols)[:2]
    ax.set_xlabel(name0); ax.set_ylabel(name1)
    ax.set_title("Pareto front")
    ax.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_feature_importance(importance: dict, out_path: str, title="Feature importance"):
    items = sorted(importance.items(), key=lambda x: x[1])
    names, vals = zip(*items)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(names, vals, color="C2")
    ax.set_xlabel("Importance"); ax.set_title(title)
    ax.grid(True, axis="x", alpha=0.3)
    return _save(fig, out_path)


def plot_metrics_table(df: pd.DataFrame, out_path: str):
    fig, ax = plt.subplots(figsize=(10, 0.4 * len(df) + 1.5))
    ax.axis("off")
    tbl = ax.table(cellText=df.round(4).values, colLabels=df.columns,
                   loc="center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.3)
    ax.set_title("Surrogate model metrics", pad=14)
    return _save(fig, out_path)
