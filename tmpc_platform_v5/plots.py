"""Publication-grade matplotlib figures (everything writes to disk)."""
from __future__ import annotations

import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

import numpy as np
import pandas as pd


def _save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------- physics ----------
def plot_spot_pattern(spots: np.ndarray, cfg, out_path: str) -> str:
    fig = plt.figure(figsize=(11, 5))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    if len(spots):
        ax1.plot(spots[:, 0], spots[:, 1], spots[:, 2], "-o", ms=2, lw=0.6)
    th = np.linspace(0, 2 * np.pi, cfg.N, endpoint=False)
    ax1.scatter(cfg.R_ring * np.cos(th), cfg.R_ring * np.sin(th),
                np.zeros_like(th), c="red", s=20)
    ax1.set_xlabel("x [mm]"); ax1.set_ylabel("y [mm]"); ax1.set_zlabel("z [mm]")
    ax1.set_title(f"Bounce trajectory (N={cfg.N}, skip={cfg.chord_skip})")
    ax2 = fig.add_subplot(1, 2, 2)
    if len(spots):
        ang = np.degrees(np.arctan2(spots[:, 1], spots[:, 0]))
        ax2.plot(ang, spots[:, 2], "-o", ms=2, lw=0.6)
    ax2.set_xlabel("Azimuth [deg]"); ax2.set_ylabel("z [mm]")
    ax2.set_title("Unfolded spot pattern"); ax2.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_beam_evolution(w_t, w_s, aperture, out_path: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(w_t, label="tangential", lw=1.8)
    ax.plot(w_s, label="sagittal", lw=1.8)
    ax.axhline(aperture, color="r", ls="--", lw=1, label="aperture")
    ax.set_xlabel("Bounce index"); ax.set_ylabel("Beam radius [mm]")
    ax.set_title("Gaussian beam evolution"); ax.legend(); ax.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_losses(loss, out_path: str) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 4))
    labels = ["reflectivity", "clipping", "aperture", "truncation"]
    vals = [loss.reflectivity_loss, loss.clipping_loss,
            loss.aperture_loss, loss.truncation_loss]
    ax.bar(labels, np.array(vals) * 100, color=["C0", "C3", "C1", "C2"])
    ax.set_ylabel("Loss [%]"); ax.set_title(f"Loss budget  (T={loss.throughput*100:.1f}%)")
    ax.grid(True, axis="y", alpha=0.3)
    return _save(fig, out_path)


# ---------- tolerance ----------
def plot_mc_histograms(mc_df: pd.DataFrame, out_path: str,
                       columns=("throughput", "opl_m", "w_max_mm", "bounces")) -> str:
    cols = [c for c in columns if c in mc_df.columns]
    fig, axes = plt.subplots(1, len(cols), figsize=(4 * len(cols), 3.5))
    if len(cols) == 1:
        axes = [axes]
    for ax, c in zip(axes, cols):
        ax.hist(mc_df[c], bins=30, color="C0", alpha=0.85, edgecolor="k", lw=0.4)
        ax.axvline(mc_df[c].mean(), color="C3", ls="--", lw=1.2,
                   label=f"mean={mc_df[c].mean():.3g}")
        ax.set_xlabel(c); ax.set_ylabel("count")
        ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle(f"Monte-Carlo distribution (N={len(mc_df)} trials)")
    return _save(fig, out_path)


def plot_sensitivity_bars(sens_df: pd.DataFrame, out_path: str,
                          metric: Optional[str] = None) -> str:
    df = sens_df.sort_values("abs_delta_at_1sigma", ascending=True)
    fig, ax = plt.subplots(figsize=(7.5, 0.35 * len(df) + 1.6))
    ax.barh(df["param"], df["abs_delta_at_1sigma"], color="C1")
    ax.set_xlabel(f"|ΔY|  at 1σ  (uniform worst-case)   [{metric or 'metric'}]")
    ax.set_title("One-at-a-time sensitivity")
    ax.grid(True, axis="x", alpha=0.3)
    return _save(fig, out_path)


def plot_exit_pointing(mc_df: pd.DataFrame, out_path: str) -> str:
    """Histogram of exit-ray pointing drift and spot-walk from a tolerance MC."""
    cols = [c for c in ("exit_drift_mrad", "spot_walk_mm") if c in mc_df.columns]
    if not cols:
        return out_path
    fig, axes = plt.subplots(1, len(cols), figsize=(5 * len(cols), 3.6))
    if len(cols) == 1:
        axes = [axes]
    units = {"exit_drift_mrad": "mrad", "spot_walk_mm": "mm"}
    for ax, c in zip(axes, cols):
        ax.hist(mc_df[c], bins=30, color="C4", alpha=0.85, edgecolor="k", lw=0.4)
        ax.axvline(mc_df[c].quantile(0.95), color="C3", ls="--", lw=1.2,
                   label=f"p95={mc_df[c].quantile(0.95):.3g}")
        ax.set_xlabel(f"{c} [{units.get(c,'')}]"); ax.set_ylabel("count")
        ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("Alignment walk-off under tolerance Monte-Carlo")
    return _save(fig, out_path)


def plot_pareto(pareto_df: pd.DataFrame, out_path: str,
                x: str = "opl_m", y: str = "throughput") -> str:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pareto_df[x], pareto_df[y], s=30, edgecolor="k",
               facecolor="C0", zorder=3)
    df_sorted = pareto_df.sort_values(x)
    ax.plot(df_sorted[x], df_sorted[y], color="C0", lw=1, alpha=0.5, zorder=2)
    ax.set_xlabel(x); ax.set_ylabel(y)
    ax.set_title(f"Pareto front: {y} vs {x}")
    ax.grid(True, alpha=0.3)
    return _save(fig, out_path)


def plot_cell_3d(res, cfg, out_path: str) -> str:
    """Static publication-grade 3D render of the ring + ray path (matplotlib).
    A browser-free companion to the interactive viz3d viewer."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    # mirror faces as small quads
    quads = []
    for k in range(cfg.N):
        th = 2 * np.pi * k / cfg.N
        c = np.array([cfg.R_ring * np.cos(th), cfg.R_ring * np.sin(th), 0.0])
        n = -np.array([np.cos(th), np.sin(th), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        tan = np.cross(sag, n); tan /= np.linalg.norm(tan)
        a = cfg.mirror_aperture
        corners = [c + a * tan + 0.5 * cfg.H * sag,
                   c - a * tan + 0.5 * cfg.H * sag,
                   c - a * tan - 0.5 * cfg.H * sag,
                   c + a * tan - 0.5 * cfg.H * sag]
        quads.append(corners)
    pc = Poly3DCollection(quads, alpha=0.25, facecolor="#3d6c92",
                          edgecolor="#7faed1")
    ax.add_collection3d(pc)
    s = res.spot_pattern
    if len(s):
        ax.plot(s[:, 0], s[:, 1], s[:, 2], "-", color="#ff5050", lw=0.8)
        sc = ax.scatter(s[:, 0], s[:, 1], s[:, 2], c=np.arange(len(s)),
                        cmap="plasma", s=12)
        fig.colorbar(sc, ax=ax, label="bounce #", shrink=0.6)
    ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]"); ax.set_zlabel("z [mm]")
    ax.set_title(f"TMPC cell — N={cfg.N} skip={cfg.chord_skip} "
                 f"OPL={res.opl*1e-3:.2f} m  T={res.throughput*100:.1f}%")
    try:
        ax.set_box_aspect((1, 1, cfg.H / (2 * cfg.R_ring)))
    except Exception:
        pass
    return _save(fig, out_path)


def plot_tolerance_budget(budget_df: pd.DataFrame, out_path: str) -> str:
    df = budget_df.sort_values("allocated_sigma", ascending=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 0.35 * len(df) + 1.8))
    axes[0].barh(df["param"], df["allocated_sigma"], color="C2")
    axes[0].set_xlabel("Allocated 1σ (in native units of each tolerance)")
    axes[0].set_title("RSS tolerance budget")
    axes[0].grid(True, axis="x", alpha=0.3)
    axes[1].barh(df["param"], df["allocated_delta"], color="C0")
    axes[1].set_xlabel("ΔY contributed by allocated σ")
    axes[1].set_title("Per-param contribution")
    axes[1].grid(True, axis="x", alpha=0.3)
    return _save(fig, out_path)
