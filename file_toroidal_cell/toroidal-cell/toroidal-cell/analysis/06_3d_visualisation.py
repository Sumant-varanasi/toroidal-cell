"""
3D Visualisation of the Toroidal Multipass Cell
===============================================

Renders the TMPC as a 3D figure with each mirror visible as a solid
slab. Three figures are written to results/plots/:

  fig_3d_cell.png        : the cell with all 8 mirrors and a few orbits
                           of the beam path
  fig_3d_spots.png       : all 528 bounce spots in 3D, coloured by
                           bounce order (the upward spiral is obvious)
  fig_3d_one_mirror.png  : close-up of mirror M0 showing the 66 spots
                           on it, sized by Gaussian beam radius

Run from the project root:
    python analysis/06_3d_visualisation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))

from tmpc.geometry import TMPCConfig, trace_cell  # noqa: E402


# Configuration ----------------------------------------------------- #
cfg = TMPCConfig(
    N=9,
    chord_skip=4,
    w0=2.5e-3,
    ROC=0.2,
    M_halfLaps=34,         
    R=50e-3,
    H=40e-3,
    wavelength=1.654e-6,
    D_mirror=25.4e-3,
)
MIRROR_T = 5e-3   # visible thickness so the slab isn't edge-on

OUT_CELL = PROJECT / "results" / "plots" / "fig_3d_cell.png"
OUT_SPOTS = PROJECT / "results" / "plots" / "fig_3d_spots.png"
OUT_ONE_MIRROR = PROJECT / "results" / "plots" / "fig_3d_one_mirror.png"
OUT_CELL.parent.mkdir(parents=True, exist_ok=True)


# Trace ------------------------------------------------------------- #
data = trace_cell(cfg)
x = np.asarray(data["x"])
y = np.asarray(data["y"])
z = np.asarray(data["z"])
mirror_id = np.asarray(data["mirror_id"])
spot_radius = np.asarray(data["spot_radius"])
n_bounces = len(x)
phi = np.array([2 * np.pi * k / cfg.N for k in range(cfg.N)])
W = cfg.D_mirror
H = cfg.H
R = cfg.R


# Mirror slab as 6 faces (cuboid) ----------------------------------- #
def mirror_faces(phi_k):
    """Return mirror cuboid faces in MILLIMETRES (matches plot scale)."""
    r_hat = np.array([np.cos(phi_k), np.sin(phi_k), 0.0])
    t_hat = np.array([-np.sin(phi_k), np.cos(phi_k), 0.0])
    z_hat = np.array([0, 0, 1.0])
    # Work in mm throughout so the polygons sit on the same scale as the axes
    R_mm = R * 1e3
    W_mm = W * 1e3
    H_mm = H * 1e3
    T_mm = MIRROR_T * 1e3
    centre = R_mm * r_hat
    pts = {}
    for st in (-1, +1):
        for sz in (-1, +1):
            for sr in (0, +1):
                pts[(st, sz, sr)] = centre + st * 0.5 * W_mm * t_hat \
                    + sz * 0.5 * H_mm * z_hat + sr * T_mm * r_hat
    faces = [
        [pts[-1, -1, 0], pts[+1, -1, 0], pts[+1, +1, 0], pts[-1, +1, 0]],
        [pts[-1, -1, 1], pts[+1, -1, 1], pts[+1, +1, 1], pts[-1, +1, 1]],
        [pts[-1, -1, 0], pts[-1, -1, 1], pts[-1, +1, 1], pts[-1, +1, 0]],
        [pts[+1, -1, 0], pts[+1, -1, 1], pts[+1, +1, 1], pts[+1, +1, 0]],
        [pts[-1, -1, 0], pts[+1, -1, 0], pts[+1, -1, 1], pts[-1, -1, 1]],
        [pts[-1, +1, 0], pts[+1, +1, 0], pts[+1, +1, 1], pts[-1, +1, 1]],
    ]
    return faces, centre + 0.5 * T_mm * r_hat


def add_mirrors(ax, target_id=None, base_alpha=0.85):
    """Draw all mirrors as solid slabs. Disabling matplotlib's auto
    depth-sort (computed_zorder=False) and giving each mirror an explicit
    high zorder is the reliable way to force visibility."""
    for k in range(cfg.N):
        faces, ctr = mirror_faces(phi[k])
        if target_id is None:
            fc, ec, alpha = "#2e6fa8", "navy", base_alpha
        elif k == target_id:
            fc, ec, alpha = "#d4a017", "darkgoldenrod", 0.95
        else:
            fc, ec, alpha = "#cccccc", "grey", 0.35
        poly = Poly3DCollection(faces, alpha=alpha, facecolor=fc,
                                edgecolor=ec, linewidth=0.9)
        poly.set_zorder(100)
        ax.add_collection3d(poly)
        lbl = ctr + np.array([np.cos(phi[k]), np.sin(phi[k]), 0]) * 18.0 \
                  + np.array([0, 0, H * 1e3 * 0.7])
        ax.text(lbl[0], lbl[1], lbl[2],
                f"M{k}", color="navy", fontsize=13, weight="bold",
                ha="center", zorder=200)


def style(ax, elev=24, azim=-58, zoom=1.30):
    ax.set_proj_type("ortho")
    lim = R * zoom * 1e3
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-H * 0.8 * 1e3, H * 0.8 * 1e3)
    ax.set_box_aspect([1, 1, H / (2 * R) * 1.6])
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_zlabel("z [mm]")
    ax.view_init(elev=elev, azim=azim)


# 1. Cell figure --------------------------------------------------- #
fig = plt.figure(figsize=(11, 9))
ax = fig.add_subplot(111, projection="3d", computed_zorder=False)

# Ring outline first (lowest zorder)
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(R * np.cos(theta) * 1e3, R * np.sin(theta) * 1e3,
        np.zeros_like(theta), "k--", lw=0.5, alpha=0.3, zorder=1)

# Beam path: show only first 3 orbits clearly, rest very faded
n_show = 3 * cfg.N + 1
launch = np.array([R * np.cos(phi[0]), R * np.sin(phi[0]), -H / 2])
px = np.concatenate([[launch[0]], x[:n_show - 1]]) * 1e3
py = np.concatenate([[launch[1]], y[:n_show - 1]]) * 1e3
pz = np.concatenate([[launch[2]], z[:n_show - 1]]) * 1e3
ax.plot(px, py, pz, color="red", lw=2.0, alpha=0.95,
        zorder=50, label=f"First {n_show - 1} bounces (3 orbits)")
ax.plot(x[n_show:] * 1e3, y[n_show:] * 1e3, z[n_show:] * 1e3,
        color="orange", lw=0.2, alpha=0.10, zorder=2,
        label=f"Remaining {n_bounces - n_show} bounces (faded)")

# Mirrors with explicit zorder (drawn after beam path so they sit on top)
add_mirrors(ax)

# Top retroreflector
ax.plot([0], [0], [H / 2 * 1e3], "k^", ms=14, zorder=150,
        label="Top retroreflector")

ax.set_title(
    f"TMPC v1 — 3D view of the cell\n"
    f"N={cfg.N} mirrors, R={R*1e3:.0f} mm ring, H={H*1e3:.0f} mm tall, "
    f"{n_bounces} bounces, OPL={data['path_length'][-1]:.2f} m",
    fontsize=11,
)
ax.legend(loc="upper left", fontsize=9)
style(ax)
fig.tight_layout()
fig.savefig(OUT_CELL, dpi=140, bbox_inches="tight")
print(f"Wrote: {OUT_CELL}")
plt.close(fig)


# 2. Spot scatter -------------------------------------------------- #
fig2 = plt.figure(figsize=(11, 9))
ax2 = fig2.add_subplot(111, projection="3d", computed_zorder=False)

theta = np.linspace(0, 2 * np.pi, 200)
ax2.plot(R * np.cos(theta) * 1e3, R * np.sin(theta) * 1e3,
         np.zeros_like(theta), "k--", lw=0.5, alpha=0.3, zorder=1)

sc = ax2.scatter(x * 1e3, y * 1e3, z * 1e3,
                 c=np.arange(n_bounces), cmap="viridis",
                 s=20, alpha=0.9, edgecolor="none", zorder=50)
cb = fig2.colorbar(sc, ax=ax2, pad=0.10, shrink=0.65)
cb.set_label("Bounce number (0 = entry, last = exit)")

add_mirrors(ax2, base_alpha=0.55)
ax2.plot([0], [0], [H / 2 * 1e3], "k^", ms=14, zorder=150)

ax2.set_title(
    f"TMPC v1 — all {n_bounces} bounce spots in 3D, coloured by order\n"
    f"OPL = {data['path_length'][-1]:.2f} m over the full trace",
    fontsize=11,
)
style(ax2, elev=18, azim=-60)
fig2.tight_layout()
fig2.savefig(OUT_SPOTS, dpi=140, bbox_inches="tight")
print(f"Wrote: {OUT_SPOTS}")
plt.close(fig2)


# 3. One-mirror close-up ------------------------------------------ #
fig3 = plt.figure(figsize=(11, 8))
ax3 = fig3.add_subplot(111, projection="3d", computed_zorder=False)
target_id = 0
add_mirrors(ax3, target_id=target_id)

hits = (mirror_id == target_id)
n_hits = int(hits.sum())
ax3.scatter(
    x[hits] * 1e3, y[hits] * 1e3, z[hits] * 1e3,
    s=(spot_radius[hits] * 1e3) ** 2 * 4,
    c=np.arange(n_hits), cmap="plasma",
    alpha=0.8, edgecolor="black", linewidth=0.3, zorder=200,
)

ctr_x = R * np.cos(phi[target_id]) * 1e3
ctr_y = R * np.sin(phi[target_id]) * 1e3
ax3.set_xlim(ctr_x - 40, ctr_x + 40)
ax3.set_ylim(ctr_y - 40, ctr_y + 40)
ax3.set_zlim(-H * 0.8 * 1e3, H * 0.8 * 1e3)
ax3.set_box_aspect([1, 1, 1.1])
ax3.set_proj_type("ortho")
# View from inside the cavity looking radially outward at M0
ax3.view_init(elev=5, azim=180 + np.degrees(phi[target_id]))
ax3.set_xlabel("x [mm]"); ax3.set_ylabel("y [mm]"); ax3.set_zlabel("z [mm]")
ax3.set_title(
    f"Close-up of mirror M{target_id}: all {n_hits} bounces that hit it\n"
    f"(disc area scales with Gaussian beam radius, colour = bounce order)",
    fontsize=11,
)
fig3.tight_layout()
fig3.savefig(OUT_ONE_MIRROR, dpi=140, bbox_inches="tight")
print(f"Wrote: {OUT_ONE_MIRROR}")
plt.close(fig3)

print("\nDone. Three 3D figures written to results/plots/.")
