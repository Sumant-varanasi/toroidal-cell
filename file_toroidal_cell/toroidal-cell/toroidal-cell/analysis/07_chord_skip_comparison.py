"""
07_chord_skip_comparison.py
===========================

Compare the toroidal-MPC geometry under different chord-skip strategies:
    s = 1  — current "perimeter walk" (beam hops between neighbour mirrors)
    s = 3  — diagonal crossings (gcd(3, 8) = 1, all mirrors visited)
    s = 5  — symmetric counterpart to s = 3 (gcd(5, 8) = 1)

For each value, this script:
  - traces the cell,
  - computes path length, AOI, max spot size, throughput,
  - computes volume-utilisation (Monte Carlo Beer-Lambert proxy),
  - generates a top-down spot/path overlay,
  - writes a summary CSV and comparison figure.

This is the change motivated by Tuzson/Graf (2017) and Chang et al.
(2020): the beam should sample the cell INTERIOR, not skim the perimeter.

Outputs
-------
results/csv/chord_skip_comparison.csv
results/plots/fig_chord_skip_topdown.png   (4 subplots: top-down per s)
results/plots/fig_chord_skip_metrics.png   (bar chart: OPL, AOI, util)

Run from the project root:
    python analysis/07_chord_skip_comparison.py
"""

from __future__ import annotations

import os
import sys
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))

from tmpc.geometry import (                       # noqa: E402
    TMPCConfig, trace_cell, incident_angle_deg,
    volume_utilisation, mirror_centre, mirror_fill_fraction,
    max_radial_extent,
)
from tmpc.losses import LossModel                  # noqa: E402


OUT_CSV = PROJECT / "results" / "csv" / "chord_skip_comparison.csv"
OUT_TOP = PROJECT / "results" / "plots" / "fig_chord_skip_topdown.png"
OUT_MET = PROJECT / "results" / "plots" / "fig_chord_skip_metrics.png"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_TOP.parent.mkdir(parents=True, exist_ok=True)


# Configurations to compare ---------------------------------------- #
BASE = dict(N=8, R=50e-3, H=40e-3, M_halfLaps=66, w0=1e-3,
            wavelength=1.654e-6, D_mirror=25.4e-3)
SKIPS = [1, 2, 3, 5]   # 1 = current; 3, 5 = best (gcd=1); 2 = partial

# Reflectivity matching the published target (dielectric ~ 99.9%).
R_RING = 0.999


# Trace each configuration ----------------------------------------- #
results = []
print("\n=== CHORD-SKIP COMPARISON ===\n")
print(f"  Base config: N={BASE['N']}, R={BASE['R']*1e3:.0f} mm, "
      f"H={BASE['H']*1e3:.0f} mm, M_halfLaps={BASE['M_halfLaps']}, "
      f"R_ring={R_RING}\n")

for s in SKIPS:
    try:
        cfg = TMPCConfig(chord_skip=s, **BASE)
    except ValueError as e:
        print(f"  chord_skip={s}: invalid ({e}); skipped.")
        continue

    data = trace_cell(cfg)

    # Volume utilisation (using mean beam radius as threshold)
    vu = volume_utilisation(data, cfg, n_samples=15000)

    # Throughput via the loss model
    lm = LossModel(R_ring=R_RING, R_top=R_RING)
    n_refl = len(data["x"])
    throughput = R_RING ** n_refl

    # Fill fraction / clipping flag
    fill = mirror_fill_fraction(data, cfg)
    max_w = max_radial_extent(data, cfg)

    n_distinct_mirrors_used = len(np.unique(data["mirror_id"]))

    row = {
        "chord_skip":            s,
        "gcd_skip_N":            int(np.gcd(s, cfg.N)),
        "L_chord_mm":            cfg.L_chord * 1e3,
        "AOI_deg":               incident_angle_deg(cfg),
        "n_bounces":             n_refl,
        "OPL_m":                 cfg.OPL_design,
        "throughput":            throughput,
        "max_spot_radius_mm":    max_w * 1e3,
        "mirror_fill_fraction":  fill,
        "volume_utilisation":    vu["utilisation"],
        "threshold_used_mm":     vu["threshold_m"] * 1e3,
        "median_dist_to_path_mm": vu["median_distance_m"] * 1e3,
        "mirrors_visited":       n_distinct_mirrors_used,
    }
    results.append((row, data, cfg))

    print(f"  chord_skip = {s}  (gcd(s,N) = {row['gcd_skip_N']})")
    print(f"      L_chord   = {row['L_chord_mm']:.2f} mm")
    print(f"      AOI       = {row['AOI_deg']:.2f} deg")
    print(f"      OPL       = {row['OPL_m']:.2f} m   "
          f"({n_refl} bounces)")
    print(f"      throughput= {throughput*100:.1f} %  at R_ring={R_RING}")
    print(f"      max spot  = {row['max_spot_radius_mm']:.2f} mm "
          f"(mirror D/2 = {cfg.D_mirror*500:.2f} mm)")
    print(f"      vol util  = {vu['utilisation']*100:.1f} %")
    print(f"      mirrors visited = {n_distinct_mirrors_used} of {cfg.N}")
    print()


# Write summary CSV ------------------------------------------------ #
with open(OUT_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    if results:
        w.writerow(list(results[0][0].keys()))
        for row, _, _ in results:
            w.writerow([f"{v:.6g}" if isinstance(v, float) else v
                        for v in row.values()])
print(f"CSV written: {OUT_CSV}")


# Figure 1 — top-down spot/path overlay for each s ----------------- #
n_panels = len(results)
fig, axes = plt.subplots(1, n_panels, figsize=(4.2 * n_panels, 4.3))
if n_panels == 1:
    axes = [axes]

theta = np.linspace(0, 2 * np.pi, 360)
for ax, (row, data, cfg) in zip(axes, results):
    # Ring outline
    ax.plot(cfg.R * np.cos(theta) * 1e3, cfg.R * np.sin(theta) * 1e3,
            "k:", lw=0.6, alpha=0.5)

    # Mirrors as filled circles
    for k in range(cfg.N):
        m = mirror_centre(k, cfg)
        ax.add_patch(plt.Circle(
            (m[0] * 1e3, m[1] * 1e3), cfg.D_mirror * 1e3 / 2,
            facecolor="steelblue", edgecolor="navy", alpha=0.4, lw=0.6,
            zorder=2))
        ax.text(m[0] * 1.20 * 1e3, m[1] * 1.20 * 1e3, f"M{k}",
                fontsize=8, ha="center", va="center", color="navy")

    # The full path: connect launch -> bounces -> exit
    p0 = mirror_centre(0, cfg).copy()
    p0[2] = cfg.z_entry
    xs = np.concatenate([[p0[0]], data["x"], [p0[0]]]) * 1e3
    ys = np.concatenate([[p0[1]], data["y"], [p0[1]]]) * 1e3
    ax.plot(xs, ys, color="crimson", lw=0.4, alpha=0.55, zorder=3)

    ax.set_xlim(-cfg.R * 1.35 * 1e3, cfg.R * 1.35 * 1e3)
    ax.set_ylim(-cfg.R * 1.35 * 1e3, cfg.R * 1.35 * 1e3)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(
        f"chord_skip = {row['chord_skip']}\n"
        f"L={row['L_chord_mm']:.1f} mm, AOI={row['AOI_deg']:.1f}°\n"
        f"OPL={row['OPL_m']:.1f} m, util={row['volume_utilisation']*100:.0f}%",
        fontsize=10,
    )

fig.suptitle(
    "Top-down view: chord-skip pattern determines whether the beam "
    "samples the cell INTERIOR or skims the PERIMETER",
    fontsize=12,
)
fig.tight_layout()
fig.savefig(OUT_TOP, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"Figure written: {OUT_TOP}")


# Figure 2 — metrics bar chart ------------------------------------ #
labels = [f"s={r['chord_skip']}" for r, _, _ in results]
vals = {
    "OPL [m]":              [r["OPL_m"] for r, _, _ in results],
    "AOI [deg]":            [r["AOI_deg"] for r, _, _ in results],
    "Throughput [%]":       [r["throughput"] * 100 for r, _, _ in results],
    "Volume utilised [%]":  [r["volume_utilisation"] * 100 for r, _, _ in results],
}

fig2, axes2 = plt.subplots(2, 2, figsize=(10, 7.2))
flat = axes2.flatten()
colors = ["#225588", "#cc4444", "#22aa66", "#aa6600"]
for (k, v), ax, col in zip(vals.items(), flat, colors):
    bars = ax.bar(labels, v, color=col, alpha=0.85, edgecolor="black", lw=0.8)
    for b, val in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                f"{val:.1f}", ha="center", va="bottom", fontsize=10,
                fontweight="bold")
    ax.set_title(k, fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)

fig2.suptitle(
    f"Chord-skip comparison  (N={BASE['N']}, R={BASE['R']*1e3:.0f} mm, "
    f"H={BASE['H']*1e3:.0f} mm, {results[0][0]['n_bounces']} bounces, "
    f"R_ring={R_RING})",
    fontsize=12,
)
fig2.tight_layout()
fig2.savefig(OUT_MET, dpi=140, bbox_inches="tight")
plt.close(fig2)
print(f"Figure written: {OUT_MET}")

print("\nDone.")
