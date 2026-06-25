"""
Optiland Independent Validation of the TMPC Geometry
====================================================

Verifies the custom NumPy ray tracer (tmpc.geometry.trace_cell) by
rebuilding the same toroidal multipass cell in the open-source Optiland
package and comparing per-bounce spot positions, chord length, and AOI.
"""

from __future__ import annotations

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

from tmpc.geometry import TMPCConfig, trace_cell  # noqa: E402


# 1. Configuration ---------------------------------------------------- #
cfg = TMPCConfig(
    N=8,
    R=50e-3,
    H=40e-3,
    M_halfLaps=66,
    w0=1e-3,
    wavelength=1.654e-6,
    D_mirror=25.4e-3,
)

# Number of upgoing bounces to validate. None = full upgoing leg (264
# bounces, ~10 s). Set to 64 for a faster smoke test.
N_VALIDATE: int | None = None

OUT_CSV = PROJECT / "results" / "csv" / "optiland_validation.csv"
OUT_FIG = PROJECT / "results" / "plots" / "fig_optiland_validation.png"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_FIG.parent.mkdir(parents=True, exist_ok=True)


# 2. Reference trace -------------------------------------------------- #
print("\n=== TMPC OPTILAND CROSS-VALIDATION ===\n")
print(f"Configuration: N={cfg.N}, R={cfg.R*1e3:.1f} mm, "
      f"H={cfg.H*1e3:.1f} mm, M_halfLaps={cfg.M_halfLaps}")
print(f"L_chord       = {cfg.L_chord*1e3:.4f} mm  (= 2R sin(pi/N))")
print(f"Spiral pitch  = {2*cfg.H/(cfg.N*cfg.M_halfLaps)*1e6:.3f} um per chord")
print(f"Expected AOI  = {(np.pi/2 - np.pi/cfg.N)*180/np.pi:.3f} deg")

ref = trace_cell(cfg)
n_total = len(ref["x"])
j_up = cfg.N * cfg.M_halfLaps // 2
print(f"\nCustom tracer produced {n_total} bounces total "
      f"(j_up = {j_up} upgoing).")

n_use = j_up if N_VALIDATE is None else min(N_VALIDATE, j_up)
print(f"Validating the first {n_use} upgoing bounces.\n")

ref_pos = np.stack([
    np.asarray(ref["x"])[:n_use],
    np.asarray(ref["y"])[:n_use],
    np.asarray(ref["z"])[:n_use],
], axis=1)
ref_mirror_id = np.asarray(ref["mirror_id"])[:n_use]


# 3. Build the Optiland model ---------------------------------------- #
import optiland.backend as be          # noqa: E402
from optiland.optic import Optic        # noqa: E402
from optiland.rays import RealRays      # noqa: E402

phi = np.array([2 * np.pi * k / cfg.N for k in range(cfg.N)])
mirror_xy = np.stack([cfg.R * np.cos(phi), cfg.R * np.sin(phi)], axis=1)

# Launch from mirror 0's centre at z = -H/2, aimed at mirror 1's centre
# at z = -H/2 + dz_chord. This is the canonical TMPC launch.
dz_chord = 2 * cfg.H / (cfg.N * cfg.M_halfLaps)
launch_pos = np.array([mirror_xy[0, 0], mirror_xy[0, 1], -cfg.H / 2])
launch_target = np.array([
    mirror_xy[1, 0], mirror_xy[1, 1], -cfg.H / 2 + dz_chord
])
launch_dir = launch_target - launch_pos
launch_dir /= np.linalg.norm(launch_dir)

print(f"Launch point  : ({launch_pos[0]*1e3:+7.3f}, "
      f"{launch_pos[1]*1e3:+7.3f}, {launch_pos[2]*1e3:+7.3f}) mm")
print(f"Launch dir    : ({launch_dir[0]:+.6f}, "
      f"{launch_dir[1]:+.6f}, {launch_dir[2]:+.6f})\n")


def make_optic() -> Optic:
    """Unroll the visit sequence into one Optiland surface per bounce.

    For a mirror at world angle phi around the ring, the inward radial
    normal is (-cos phi, -sin phi, 0). Choosing rx=0, ry=-pi/2, rz=phi
    sends the surface's local +z (default Optiland surface normal) to
    that inward direction.
    """
    o = Optic(name="TMPC v1 (Optiland validation)")

    o.surfaces.add(index=0, thickness=be.inf, radius=be.inf)

    for k in range(n_use):
        m_id = int(ref_mirror_id[k])
        o.surfaces.add(
            index=k + 1,
            x=float(mirror_xy[m_id, 0]),
            y=float(mirror_xy[m_id, 1]),
            z=0.0,
            rx=0.0,
            ry=-np.pi / 2,
            rz=float(phi[m_id]),
            radius=be.inf,
            material="mirror",
            comment=f"bounce_{k+1}_mirror_{m_id}",
        )

    o.wavelengths.add(value=cfg.wavelength * 1e6, is_primary=True)
    return o


print("Building Optiland model (one surface per bounce)...")
optic = make_optic()
print(f"  total surfaces: {optic.surfaces.num_surfaces}")


# 4. Trace chief ray surface-by-surface ------------------------------ #
print("Tracing chief ray through Optiland's RealRays kernel...")

rays = RealRays(
    x=float(launch_pos[0]),
    y=float(launch_pos[1]),
    z=float(launch_pos[2]),
    L=float(launch_dir[0]),
    M=float(launch_dir[1]),
    N=float(launch_dir[2]),
    intensity=1.0,
    wavelength=cfg.wavelength * 1e6,
)

incident_aoi_deg = np.zeros(n_use)

optic.surfaces.reset()
for k, s in enumerate(optic.surfaces.surfaces[1:1 + n_use]):
    d_in_world = np.array([float(rays.L[0]), float(rays.M[0]),
                           float(rays.N[0])])
    s.trace(rays)

    m_id = int(ref_mirror_id[k])
    n_world = np.array([-np.cos(phi[m_id]), -np.sin(phi[m_id]), 0.0])

    cos_aoi = float(np.clip(np.dot(-d_in_world, n_world), -1.0, 1.0))
    incident_aoi_deg[k] = np.degrees(np.arccos(cos_aoi))


# 5. Extract recorded hit positions ---------------------------------- #
def get_recorded(s, attr):
    v = getattr(s, attr, None)
    if v is None:
        return np.nan
    arr = np.asarray(v).ravel()
    return float(arr[0]) if arr.size else np.nan


opt_pos = np.array([
    [get_recorded(s, "x"), get_recorded(s, "y"), get_recorded(s, "z")]
    for s in optic.surfaces.surfaces[1:1 + n_use]
])


# 6. Comparison metrics ---------------------------------------------- #
err_xyz = opt_pos - ref_pos
err_mag = np.linalg.norm(err_xyz, axis=1)
rms = float(np.sqrt(np.mean(err_mag ** 2)) * 1e6)
max_err = float(np.max(err_mag) * 1e6)
mean_err = float(np.mean(err_mag) * 1e6)

opt_chords = np.linalg.norm(np.diff(opt_pos, axis=0), axis=1)
chord_mean_um = float(np.mean(opt_chords) * 1e6)
chord_std_um = float(np.std(opt_chords) * 1e6)
chord_err_vs_analytic_um = float((opt_chords.mean() - cfg.L_chord) * 1e6)

aoi_mean = float(np.mean(incident_aoi_deg))
aoi_std = float(np.std(incident_aoi_deg))
aoi_expected = (np.pi / 2 - np.pi / cfg.N) * 180 / np.pi

print("\n=== RESULTS ===")
print(f"  Bounces compared           : {n_use}")
print(f"  Position-error (vs custom) : mean {mean_err:7.3f} um, "
      f"RMS {rms:7.3f} um, max {max_err:7.3f} um")
print(f"  Optiland chord length      : {chord_mean_um/1e3:.6f} mm  "
      f"(std {chord_std_um:.3f} um)")
print(f"     vs analytical L_chord   : {cfg.L_chord*1e3:.6f} mm  "
      f"(diff {chord_err_vs_analytic_um:+.3f} um)")
print(f"  Optiland AOI               : {aoi_mean:.4f} deg  "
      f"(std {aoi_std:.4f} deg)")
print(f"     vs analytical pi/2-pi/N : {aoi_expected:.4f} deg  "
      f"(diff {aoi_mean - aoi_expected:+.4f} deg)")


# 7. CSV ------------------------------------------------------------- #
with open(OUT_CSV, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow([
        "Bounce_Number", "Mirror_ID",
        "Custom_X_m", "Custom_Y_m", "Custom_Z_m",
        "Optiland_X_m", "Optiland_Y_m", "Optiland_Z_m",
        "Error_X_um", "Error_Y_um", "Error_Z_um", "Error_Magnitude_um",
        "Optiland_AOI_deg",
    ])
    for k in range(n_use):
        w.writerow([
            k + 1, int(ref_mirror_id[k]),
            f"{ref_pos[k,0]:.9f}", f"{ref_pos[k,1]:.9f}",
            f"{ref_pos[k,2]:.9f}",
            f"{opt_pos[k,0]:.9f}", f"{opt_pos[k,1]:.9f}",
            f"{opt_pos[k,2]:.9f}",
            f"{err_xyz[k,0]*1e6:.3f}", f"{err_xyz[k,1]*1e6:.3f}",
            f"{err_xyz[k,2]*1e6:.3f}", f"{err_mag[k]*1e6:.3f}",
            f"{incident_aoi_deg[k]:.4f}",
        ])
print(f"\nCSV written: {OUT_CSV}")


# 8. Plot ------------------------------------------------------------ #
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))

ax = axes[0]
theta = np.linspace(0, 2 * np.pi, 360)
ax.plot(cfg.R * np.cos(theta) * 1e3, cfg.R * np.sin(theta) * 1e3,
        "k--", lw=0.6, alpha=0.5, label="Ring (R)")
ax.scatter(mirror_xy[:, 0] * 1e3, mirror_xy[:, 1] * 1e3,
           c="k", marker="s", s=40, label="Mirror centres")
ax.scatter(ref_pos[:, 0] * 1e3, ref_pos[:, 1] * 1e3,
           c="C0", marker="o", s=24, label="Custom tracer", alpha=0.8)
ax.scatter(opt_pos[:, 0] * 1e3, opt_pos[:, 1] * 1e3,
           c="C3", marker="x", s=30, label="Optiland", alpha=0.9)
ax.set_xlabel("x [mm]")
ax.set_ylabel("y [mm]")
ax.set_title(f"Top-down spot overlay ({n_use} bounces)")
ax.set_aspect("equal")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8, loc="upper right")

ax = axes[1]
ax.plot(np.arange(1, n_use + 1), ref_pos[:, 2] * 1e3,
        "C0o-", ms=4, lw=0.8, label="Custom tracer")
ax.plot(np.arange(1, n_use + 1), opt_pos[:, 2] * 1e3,
        "C3x--", ms=5, lw=0.6, label="Optiland")
ax.axhline(cfg.H / 2 * 1e3, color="grey", ls=":", lw=0.6,
           label="Cell top H/2")
ax.axhline(-cfg.H / 2 * 1e3, color="grey", ls=":", lw=0.6,
           label="Cell bottom -H/2")
ax.set_xlabel("Bounce number")
ax.set_ylabel("z [mm]")
ax.set_title("Height (z) along the spiral")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8)

ax = axes[2]
ax.semilogy(np.arange(1, n_use + 1),
            np.clip(err_mag * 1e6, 1e-6, None),
            "C2.-", ms=4, lw=0.7)
ax.set_xlabel("Bounce number")
ax.set_ylabel("|Optiland - Custom| [um]")
ax.set_title("Per-bounce position error")
ax.grid(True, alpha=0.3, which="both")

fig.suptitle(
    f"TMPC Geometry: Custom Tracer vs Optiland   "
    f"(RMS = {rms:.3f} um, max = {max_err:.3f} um)",
    fontsize=11,
)
fig.tight_layout()
fig.savefig(OUT_FIG, dpi=140, bbox_inches="tight")
print(f"Figure written: {OUT_FIG}")


# 9. Verdict --------------------------------------------------------- #
print("\n=== VERDICT ===")
TOL_UM = 10.0
chord_tol_um = 1.0
aoi_tol_deg = 0.01
checks_pass = (
    rms < TOL_UM
    and max_err < TOL_UM * 3
    and abs(chord_err_vs_analytic_um) < chord_tol_um
    and abs(aoi_mean - aoi_expected) < aoi_tol_deg
)
if checks_pass:
    print(f"  PASS: Optiland reproduces the custom tracer's geometry to")
    print(f"        - position RMS < {TOL_UM:.0f} um")
    print(f"        - chord length matches analytical L_chord to "
          f"< {chord_tol_um:.1f} um")
    print(f"        - AOI matches pi/2 - pi/N to < "
          f"{aoi_tol_deg:.3f} deg")
    print(f"        The analytical geometry model is independently validated.")
else:
    print(f"  FAIL: one or more tolerances exceeded.")
    print(f"        position RMS  = {rms:.2f} um (tol {TOL_UM:.0f})")
    print(f"        chord error   = {chord_err_vs_analytic_um:+.3f} um "
          f"(tol {chord_tol_um:.1f})")
    print(f"        AOI error     = {aoi_mean - aoi_expected:+.4f} deg "
          f"(tol {aoi_tol_deg:.3f})")
print()