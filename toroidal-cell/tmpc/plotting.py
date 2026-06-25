"""
plotting.py
===========

Visualisation helpers. All figures are saved to PNG; no GUI required.
"""

from __future__ import annotations
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from .geometry import TMPCConfig, trace_cell, per_mirror_z_spots


# ---------------------------------------------------------------------------
def plot_topdown(cfg: TMPCConfig, data: dict, path: str) -> None:
    """Plot the in-plane (top-down) view of the ring and the chord pattern."""
    fig, ax = plt.subplots(figsize=(6, 6))
    # ring of mirror centres
    phis = np.linspace(0, 2 * math.pi, 200)
    ax.plot(cfg.R * np.cos(phis), cfg.R * np.sin(phis),
            color="#bbbbbb", linestyle=":", lw=1, label="ring")
    # mirror positions
    for k in range(cfg.N):
        phi = 2 * math.pi * k / cfg.N
        cx, cy = cfg.R * math.cos(phi), cfg.R * math.sin(phi)
        ax.add_patch(Circle((cx, cy), 0.6 * cfg.D_mirror / 2.0,
                            fill=False, ec="#225588", lw=1.5))
        ax.text(1.18 * cx, 1.18 * cy, f"M{k}", ha="center", va="center",
                fontsize=9, color="#225588")
    # chord trajectory (only first lap for clarity)
    j_lap = cfg.N
    for j in range(min(j_lap + 1, len(data["x"]) - 1)):
        ax.plot([data["x"][j], data["x"][j + 1]],
                [data["y"][j], data["y"][j + 1]],
                color="#d04040", lw=0.8, alpha=0.8)
    # entrance hole at mirror 0
    ax.plot(cfg.R, 0, marker="x", color="black", ms=8, mew=2,
            label="entrance / exit")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"Top-down view — N={cfg.N}, R={cfg.R*1e3:.0f} mm, "
                 f"chord={cfg.L_chord*1e3:.1f} mm")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def plot_spot_patterns(cfg: TMPCConfig, data: dict, path: str) -> None:
    """Show spot pattern on each ring mirror (chord-direction × z)."""
    cols = 4
    rows = math.ceil(cfg.N / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.0 * rows),
                              sharex=True, sharey=True)
    axes = np.atleast_2d(axes)

    grouped_z = per_mirror_z_spots(data, cfg.N)
    spot_lookup = {}
    for k in range(cfg.N):
        sel = data["mirror_id"] == k
        spot_lookup[k] = data["spot_radius"][sel]

    for k in range(cfg.N):
        ax = axes[k // cols, k % cols]
        # mirror outline as rectangle (width D, height H)
        ax.add_patch(plt.Rectangle((-cfg.D_mirror / 2, -cfg.H / 2),
                                    cfg.D_mirror, cfg.H,
                                    fill=False, ec="black", lw=1.2))
        zs = grouped_z[k]
        ws = spot_lookup[k]
        # Plot each spot as a circle of radius w. In-plane chord direction
        # we set to 0 (all spots fall on the mirror centre-line in this
        # first-order model).
        for z, w in zip(zs, ws):
            ax.add_patch(Circle((0.0, z), w, fc="#cc4444", ec="#882222",
                                 alpha=0.35, lw=0.4))
        ax.set_xlim(-cfg.D_mirror / 1.7, cfg.D_mirror / 1.7)
        ax.set_ylim(-cfg.H / 1.7, cfg.H / 1.7)
        ax.set_aspect("equal")
        ax.set_title(f"M{k}  ({len(zs)} hits)", fontsize=10)
        ax.grid(True, alpha=0.2)
    # hide unused subplots
    for k in range(cfg.N, rows * cols):
        axes[k // cols, k % cols].axis("off")
    fig.suptitle("Spot patterns on each ring mirror "
                 "(chord-direction × z)", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
def plot_beam_evolution(cfg: TMPCConfig, data: dict, path: str) -> None:
    """Spot 1/e^2 radius vs path length."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(data["path_length"], data["spot_radius"] * 1e3,
            color="#225588", lw=1.2)
    ax.axhline(cfg.D_mirror / 2.0 * 1e3, color="#d04040",
                linestyle="--", lw=1, label=f"mirror aperture = D/2")
    ax.set_xlabel("optical path length [m]")
    ax.set_ylabel("1/e² spot radius [mm]")
    ax.set_title(f"Gaussian beam evolution — w₀={cfg.w0*1e3:.2f} mm, "
                 f"λ={cfg.wavelength*1e6:.3f} μm, M²={cfg.M2:.1f}")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def plot_throughput(cum_throughput: np.ndarray, path_length: np.ndarray,
                     path: str, title: str = "") -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.semilogy(path_length, cum_throughput, color="#225588", lw=1.2)
    ax.set_xlabel("cumulative path length [m]")
    ax.set_ylabel("transmission")
    ax.set_title(title or "Cumulative throughput vs path length")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def plot_sweep_2d(df, x_col: str, y_col: str, z_col: str,
                   path: str, log_z: bool = False) -> None:
    """Plot a 2-D sweep as a scatter / heatmap (z encoded by colour)."""
    fig, ax = plt.subplots(figsize=(6.5, 5))
    x = df[x_col].values
    y = df[y_col].values
    z = df[z_col].values
    if log_z:
        z = np.log10(np.clip(z, 1e-30, None))
        clabel = f"log10({z_col})"
    else:
        clabel = z_col
    sc = ax.scatter(x, y, c=z, s=80, cmap="viridis", edgecolors="black", lw=0.3)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{z_col}  vs  ({x_col}, {y_col})")
    plt.colorbar(sc, ax=ax, label=clabel)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def plot_sweep_1d(df, x_col: str, y_col: str, path: str,
                   log_y: bool = False, group_col: str | None = None,
                   title: str | None = None) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if group_col is None:
        ax.plot(df[x_col], df[y_col], "o-", color="#225588")
    else:
        for grp, sub in df.groupby(group_col):
            ax.plot(sub[x_col], sub[y_col], "o-", label=f"{group_col}={grp}")
        ax.legend(fontsize=8)
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title or f"{y_col}  vs  {x_col}")
    ax.grid(True, alpha=0.3, which="both" if log_y else "major")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
