"""Loss mechanisms in a multipass cell."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class LossBudget:
    reflectivity_loss: float
    clipping_loss: float
    aperture_loss: float
    truncation_loss: float
    total_loss: float
    throughput: float


def compute_losses(bounces: int, reflectivity: float,
                   w_max: float, aperture: float,
                   beam_diameter_in: float, hole_diameter: float = 3.0,
                   clipped: bool = False) -> LossBudget:
    """Compute the per-mechanism loss budget for a multipass pass.

    All inputs in mm where dimensional. Loss values are fractional (0..1).
    """
    # 1) reflectivity loss: 1 - R^B
    refl_loss = 1.0 - reflectivity ** max(0, bounces)

    # 2) clipping: hard clip if beam exceeds aperture
    clip_loss = 1.0 if clipped else 0.0

    # 3) aperture loss: gentle truncation when w_max approaches aperture
    if w_max >= aperture:
        ap_loss = 1.0
    else:
        # fraction of Gaussian power outside the aperture: exp(-2 a^2 / w^2)
        ap_loss = float(np.exp(-2.0 * (aperture / max(w_max, 1e-6)) ** 2))

    # 4) truncation at entrance/exit hole
    if beam_diameter_in >= hole_diameter:
        trunc_loss = 1.0
    else:
        trunc_loss = float(np.exp(-2.0 * (hole_diameter / max(beam_diameter_in, 1e-6)) ** 2))

    # combine (independent loss mechanisms; convert to throughput then back)
    T = (1 - refl_loss) * (1 - clip_loss) * (1 - ap_loss) * (1 - trunc_loss)
    T = float(np.clip(T, 0.0, 1.0))
    return LossBudget(refl_loss, clip_loss, ap_loss, trunc_loss,
                      total_loss=1 - T, throughput=T)
