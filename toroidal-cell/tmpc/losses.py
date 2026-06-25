"""
losses.py
=========

Loss model for the toroidal multipass cell.

Three categories of loss are tracked:

1. Mirror losses
   Each ring reflection loses power (1 - R_ring) where R_ring is the
   mirror reflectivity (e.g. 0.97 for protected silver, 0.995 for a high-end
   dielectric in the NIR). The top retroreflector adds one (1 - R_top)
   reflection. We split this into:
     * Reflectivity loss   = 1 - R   (the dominant term for metals)
     * Absorption loss     = small fraction of (1 - R) attributable to
                             intrinsic absorption in the coating;
                             estimated from coating type.
     * Scatter loss        = the remainder of (1 - R).
   For an explicit accounting we use a user-specified split; defaults are
   reasonable for protected silver in the NIR.

2. Beam losses
   * Clipping loss : geometric loss from a Gaussian spot truncated by a
     finite-aperture mirror. For a circular aperture of radius a and a
     centred Gaussian of 1/e^2 radius w,
         T_aperture = 1 - exp(-2 a^2 / w^2)
     applies after EACH reflection. We assume centred spots; off-centre
     spots have larger clipping (handled by a worst-case multiplier).
   * Diffraction loss : from the beam wrapping around / refilling near the
     mirror edge. We treat the Gaussian aperture loss above as the diffraction
     model; for slightly truncated beams this is a tight upper bound on the
     true Fresnel-diffraction calculation.
   * Misalignment loss : pointing error of the input beam coupling into
     the unit-cell eigenmode. Quantified by an angular tilt sigma_theta
     and a translational offset sigma_d via the standard mode-mismatch
     formula. Off by default.
   * Coupling loss : input-mode mismatch when injecting w0_input into the
     unit-cell mode w0_eigen (only meaningful for curved-mirror cells).

3. System losses
   Total transmission after a given number of reflections is the product
   of the per-reflection survival probabilities. Helper routines below.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np


# ---------------------------------------------------------------------------
@dataclass
class LossModel:
    R_ring: float = 0.97             # ring mirror reflectivity
    R_top:  float = 0.97             # top retroreflector reflectivity
    absorption_fraction: float = 0.40  # of (1-R) attributed to absorption
    scatter_fraction:    float = 0.60  # of (1-R) attributed to scatter
    sigma_theta_rad: float = 0.0       # angular pointing error (1 sigma) [rad]
    sigma_d_m: float = 0.0             # translational pointing error (1 sigma) [m]


# ---------------------------------------------------------------------------
# Mirror losses
# ---------------------------------------------------------------------------
def mirror_loss_breakdown(model: LossModel, top: bool = False) -> dict:
    """Per-reflection loss broken down into reflectivity / absorption /
    scatter. The reflectivity loss = 1 - R is split into absorption and
    scatter via the given fractions, summing to 1 - R."""
    R = model.R_top if top else model.R_ring
    total = 1.0 - R
    abs_loss  = model.absorption_fraction * total
    scat_loss = model.scatter_fraction * total
    return {
        "reflectivity_loss": total,
        "absorption_loss": abs_loss,
        "scatter_loss":    scat_loss,
        "transmission":    R,
    }


# ---------------------------------------------------------------------------
# Beam losses
# ---------------------------------------------------------------------------
def clipping_loss(spot_w: float, aperture_radius: float) -> float:
    """Fractional power lost when a centred Gaussian of 1/e^2 radius
    spot_w hits a circular aperture of radius aperture_radius."""
    if spot_w <= 0:
        return 0.0
    return math.exp(-2.0 * aperture_radius ** 2 / spot_w ** 2)


def misalignment_coupling_loss(sigma_theta: float, sigma_d: float,
                                w0: float, wavelength: float) -> float:
    """First-order mode-mismatch loss for combined angular + lateral
    misalignment.  For small errors,

        1 - eta  ≈  (sigma_d / w0)^2  +  (pi w0 sigma_theta / lambda)^2.

    Returns the loss (1 - eta).
    """
    return (sigma_d / w0) ** 2 + (math.pi * w0 * sigma_theta / wavelength) ** 2


# ---------------------------------------------------------------------------
# Cumulative throughput
# ---------------------------------------------------------------------------
def throughput_after_n(R_per_bounce: float, n: int,
                        clipping_per_bounce: float = 0.0) -> float:
    """Power remaining after n reflections.

    R_per_bounce        : mirror reflectivity per ring bounce
    clipping_per_bounce : fractional clipping per bounce (0..1, additive in log)
    """
    survive = R_per_bounce * (1.0 - clipping_per_bounce)
    return survive ** n


def per_pass_throughput(spot_radii: np.ndarray, aperture_radius: float,
                         R_ring: float, R_top: float | None = None,
                         top_bounce_index: int | None = None
                         ) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-pass and cumulative throughput along the path.

    Parameters
    ----------
    spot_radii         : array of 1/e^2 spot radii at each reflection [m]
    aperture_radius    : effective mirror aperture radius [m]
    R_ring             : ring mirror reflectivity
    R_top              : top retro reflectivity (defaults to R_ring)
    top_bounce_index   : index in spot_radii where the top retro bounce
                         conceptually sits (use any ring-bounce index;
                         the top retro is folded in once at that pass).

    Returns
    -------
    (per_pass, cumulative) survival fractions (not losses)
    """
    n = len(spot_radii)
    clip = np.array([1.0 - clipping_loss(w, aperture_radius)
                     for w in spot_radii])  # fraction surviving aperture
    refl = np.full(n, R_ring)
    if R_top is not None and top_bounce_index is not None:
        # One additional R_top reflection — apply at the chosen index
        refl[top_bounce_index] *= R_top
    per_pass = refl * clip
    cumulative = np.cumprod(per_pass)
    return per_pass, cumulative


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------
def reflectivity_for_target_throughput(n_reflections: int,
                                        target: float) -> float:
    """Inverse: what per-bounce reflectivity is needed for cumulative
    throughput = target after n bounces?  R = target^(1/n)."""
    return target ** (1.0 / n_reflections)
