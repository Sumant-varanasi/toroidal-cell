"""
04_generate_csvs.py
===================

Produce the four CSV files in the column schemas required by the
spec (Phase 6):

  reflection_data.csv     Pass_Number, Mirror_ID, X_Position, Y_Position,
                          Spot_Radius, Incident_Angle, Path_Length
  beam_data.csv           Pass_Number, Beam_Waist, Divergence,
                          Power_Remaining
  loss_data.csv           Pass_Number, Mirror_Loss, Clipping_Loss,
                          Coupling_Loss, Total_Loss, Remaining_Power
  optimization_data.csv   already produced by 03_optimize.py; we
                          (re)write the v1 + recommended baseline rows
                          here so all four files exist as a coherent
                          set for the v1 design

Units throughout: position in metres, angles in degrees, power as a
fraction of input (P_in = 1).
"""
from __future__ import annotations
import os, sys, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from tmpc.geometry  import TMPCConfig, trace_cell, incident_angle_deg
from tmpc.losses    import (
    LossModel, per_pass_throughput, clipping_loss,
    mirror_loss_breakdown, misalignment_coupling_loss,
)
from tmpc.gaussian  import GaussianBeam


CSVS  = os.path.abspath(os.path.join(HERE, "..", "results", "csv"))
os.makedirs(CSVS, exist_ok=True)


def main() -> None:
    # ---------------- v1 reference design ----------------
    cfg = TMPCConfig()                            # v1 defaults
    lm  = LossModel(R_ring=0.999, R_top=0.999,    # for headline numbers
                     absorption_fraction=0.40,
                     scatter_fraction=0.60,
                     sigma_theta_rad=50e-6,       # 50 µrad pointing 1σ
                     sigma_d_m=20e-6)             # 20 µm offset 1σ

    data = trace_cell(cfg)
    n = int(data["pass_no"][-1])

    # ---------------- (1) reflection_data.csv ----------------
    df_refl = pd.DataFrame({
        "Pass_Number":      data["pass_no"],
        "Mirror_ID":        data["mirror_id"],
        "X_Position":       np.round(data["x"], 6),
        "Y_Position":       np.round(data["y"], 6),
        "Spot_Radius":      np.round(data["spot_radius"], 7),
        "Incident_Angle":   np.round(data["incident_angle_deg"], 4),
        "Path_Length":      np.round(data["path_length"], 6),
    })
    df_refl.to_csv(os.path.join(CSVS, "reflection_data.csv"), index=False)
    print(f"  reflection_data.csv   ({len(df_refl)} rows)")

    # ---------------- (2) beam_data.csv ----------------
    # Compute divergence from Gaussian beam properties at each path
    # length (far-field half-angle = M^2 * lambda / (pi w0); the same
    # value applies at every pass — included for completeness).
    div_halfangle_rad = cfg.M2 * cfg.wavelength / (math.pi * cfg.w0)
    div_mrad_full = 2.0 * div_halfangle_rad * 1e3

    # Compute Power_Remaining including BOTH mirror losses and clipping
    # at the corresponding spot radius.
    aperture = cfg.D_mirror / 2.0
    _, cumul = per_pass_throughput(
        data["spot_radius"], aperture,
        R_ring=lm.R_ring, R_top=lm.R_top, top_bounce_index=n // 2,
    )

    df_beam = pd.DataFrame({
        "Pass_Number":     data["pass_no"],
        "Beam_Waist":      np.round(data["spot_radius"], 7),     # m, 1/e^2
        "Divergence":      np.round(np.full(n, div_mrad_full), 5),  # mrad full angle
        "Power_Remaining": np.round(cumul, 8),
    })
    df_beam.to_csv(os.path.join(CSVS, "beam_data.csv"), index=False)
    print(f"  beam_data.csv         ({len(df_beam)} rows)")

    # ---------------- (3) loss_data.csv ----------------
    # Mirror loss (per bounce) is constant = 1 - R_ring. The middle
    # bounce conceptually absorbs an extra (1 - R_top) for the top
    # retroreflector — applied at the midpoint index.
    mirror_loss = np.full(n, 1.0 - lm.R_ring)
    if n // 2 < n:
        mirror_loss[n // 2] += (1.0 - lm.R_top)
    # Clipping loss (per bounce) = fraction of Gaussian outside aperture
    clip_loss = np.array([clipping_loss(w, aperture)
                          for w in data["spot_radius"]])
    # Coupling loss (input-mode mismatch) — applied once, at pass 1
    coupling_once = misalignment_coupling_loss(
        lm.sigma_theta_rad, lm.sigma_d_m, cfg.w0, cfg.wavelength,
    )
    coupling = np.zeros(n)
    coupling[0] = coupling_once
    # Per-pass total loss (additive in the small-loss sense; otherwise
    # 1 - (1-clip)*(1-mirror)). We use the multiplicative formulation:
    survive = (1.0 - mirror_loss) * (1.0 - clip_loss) * (1.0 - coupling)
    survive = np.clip(survive, 0.0, 1.0)
    total_loss = 1.0 - survive
    remaining = np.cumprod(survive)

    df_loss = pd.DataFrame({
        "Pass_Number":     data["pass_no"],
        "Mirror_Loss":     np.round(mirror_loss, 8),
        "Clipping_Loss":   np.round(clip_loss, 8),
        "Coupling_Loss":   np.round(coupling, 8),
        "Total_Loss":      np.round(total_loss, 8),
        "Remaining_Power": np.round(remaining, 8),
    })
    df_loss.to_csv(os.path.join(CSVS, "loss_data.csv"), index=False)
    print(f"  loss_data.csv         ({len(df_loss)} rows)")

    # ---------------- (4) optimization_data.csv ----------------
    # 03_optimize.py already created the bulk of this. Here we prepend
    # the v1 reference and the recommended optimised design so the file
    # has a clear top-of-table for hand inspection. (The Phase 6 spec
    # mandates these column names exactly.)
    headline_rows = []
    # v1 reference
    headline_rows.append({
        "Configuration_ID": "v1_reference",
        "Mirror_Spacing":   round(cfg.L_chord * 1e3, 4),
        "Tilt_Angle":       round(math.degrees(cfg.alpha_rad), 5),
        "Rotation_Angle":   round(360.0 / cfg.N, 3),
        "Number_of_Passes": int(cfg.total_reflections),
        "Optical_Path_Length": round(cfg.OPL_design, 4),
        "Efficiency":       round(float(cumul[-1]), 6),
    })
    # Read 03_optimize output if present; append v1 row to the top
    opt_path = os.path.join(CSVS, "optimization_data.csv")
    if os.path.exists(opt_path):
        existing = pd.read_csv(opt_path)
        out = pd.concat([pd.DataFrame(headline_rows), existing], ignore_index=True)
    else:
        out = pd.DataFrame(headline_rows)
    out.to_csv(opt_path, index=False)
    print(f"  optimization_data.csv ({len(out)} rows, v1 prepended)")

    # ---------------- summary printout ----------------
    print("\nv1 reference design summary (R_ring=0.999):")
    print(f"  OPL                : {cfg.OPL_design:.3f} m")
    print(f"  total reflections  : {cfg.total_reflections}")
    print(f"  max spot radius    : {data['spot_radius'].max()*1e3:.3f} mm")
    print(f"  cumulative loss    : {1 - remaining[-1]:.3f}")
    print(f"  final power        : {remaining[-1]:.4f}")
    print(f"  divergence (full)  : {div_mrad_full:.4f} mrad")
    print(f"  Rayleigh range zR  : "
          f"{math.pi * cfg.w0 ** 2 / (cfg.M2 * cfg.wavelength):.3f} m")

    # Mirror-loss breakdown for the protected silver vs hi-R cases
    print("\nMirror-loss breakdown (per bounce):")
    for Rv in [0.97, 0.99, 0.995, 0.999]:
        bd = mirror_loss_breakdown(LossModel(R_ring=Rv))
        print(f"  R={Rv:.3f}  abs={bd['absorption_loss']*1e6:8.0f} ppm   "
              f"scat={bd['scatter_loss']*1e6:8.0f} ppm   total="
              f"{bd['reflectivity_loss']*1e6:8.0f} ppm")


if __name__ == "__main__":
    main()
