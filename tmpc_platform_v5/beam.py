"""Realistic astigmatic Gaussian-beam optics for the TMPC.

What makes this "realistic" vs. the toy f = R/2 model:

* Off-axis astigmatism.  A spherical/toroidal mirror used at angle of
  incidence theta_i has two *different* effective focal lengths:

      f_tangential = ROC * cos(theta_i) / 2
      f_sagittal   = ROC / (2 * cos(theta_i))

  At the polygon AOI theta_i = pi/2 - pi/N (large for small N) this split
  is enormous, so the tangential and sagittal beam radii evolve very
  differently.  A toroidal mirror (R_t != R_s) adds a second, independent
  split on top of that.

* Beam-quality factor M^2 (real lasers are not diffraction-limited):

      z_R = pi * w0^2 / (M^2 * lambda)

* Complex q-parameter propagation through the *actual* per-bounce
  ray-transfer matrices, plus an `envelope_along_path` helper that samples
  the 1/e^2 radius at many points *between* bounces so the 3D viewer can
  draw a smooth beam tube instead of stick segments.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. Astigmatic focal lengths
# =============================================================================
def astigmatic_focal_lengths(R_t: float, R_s: float, aoi_rad: float
                             ) -> Tuple[float, float]:
    """Effective tangential & sagittal focal lengths of a toroidal mirror at
    angle of incidence `aoi_rad`.

    f_tan = R_t * cos(theta) / 2     (meridional plane sees foreshortened ROC)
    f_sag = R_s / (2 cos(theta))     (sagittal plane sees lengthened ROC)
    """
    c = max(np.cos(aoi_rad), 1e-6)
    f_t = R_t * c / 2.0
    f_s = R_s / (2.0 * c)
    return f_t, f_s


# =============================================================================
# 2. Complex-q Gaussian beam (embedded-Gaussian / M^2 formulation)
# =============================================================================
@dataclass
class AstigBeam:
    """Astigmatic Gaussian beam: independent q in tangential & sagittal."""
    wavelength: float          # [mm]
    w0: float                  # input waist 1/e^2 radius [mm]
    M2: float = 1.0
    z_from_waist: float = 0.0  # initial distance from waist [mm]

    def __post_init__(self):
        zR = np.pi * self.w0 ** 2 / (self.M2 * self.wavelength)
        self.q_t = complex(self.z_from_waist, zR)
        self.q_s = complex(self.z_from_waist, zR)

    def _w(self, q: complex) -> float:
        inv = (1.0 / q).imag
        return float(np.sqrt(-self.M2 * self.wavelength / (np.pi * inv))) if inv < 0 else float("inf")

    @property
    def w_t(self) -> float:
        return self._w(self.q_t)

    @property
    def w_s(self) -> float:
        return self._w(self.q_s)


def _free(d: float) -> np.ndarray:
    return np.array([[1.0, d], [0.0, 1.0]])


def _lens(f: float) -> np.ndarray:
    if not np.isfinite(f):
        return np.eye(2)
    return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])


def _apply(q: complex, M: np.ndarray) -> complex:
    A, B = M[0]; C, D = M[1]
    return (A * q + B) / (C * q + D)


def _w_of_q(q: complex, wavelength: float, M2: float) -> float:
    inv = (1.0 / q).imag
    return float(np.sqrt(-M2 * wavelength / (np.pi * inv))) if inv < 0 else float("inf")


# =============================================================================
# 3. Realistic propagation through the cell
# =============================================================================
def propagate_astigmatic(beam: AstigBeam,
                         segments: Sequence[float],
                         R_t: Sequence[float],
                         R_s: Sequence[float],
                         aoi_rad: Sequence[float]) -> dict:
    """Propagate through (free space -> mirror) repeated, with per-bounce AOI.

    Lengths in mm; angles in rad. Returns per-bounce tangential & sagittal
    1/e^2 radii (including the waist at index 0) plus their maxima.
    """
    q_t, q_s = beam.q_t, beam.q_s
    w_t = [_w_of_q(q_t, beam.wavelength, beam.M2)]
    w_s = [_w_of_q(q_s, beam.wavelength, beam.M2)]
    n = len(segments)
    for i in range(n):
        q_t = _apply(q_t, _free(segments[i]))
        q_s = _apply(q_s, _free(segments[i]))
        if i < len(R_t):
            f_t, f_s = astigmatic_focal_lengths(R_t[i], R_s[i], aoi_rad[i])
            q_t = _apply(q_t, _lens(f_t))
            q_s = _apply(q_s, _lens(f_s))
        w_t.append(_w_of_q(q_t, beam.wavelength, beam.M2))
        w_s.append(_w_of_q(q_s, beam.wavelength, beam.M2))
    w_t = np.array(w_t); w_s = np.array(w_s)
    return {"w_tangential": w_t, "w_sagittal": w_s,
            "w_max": float(np.nanmax([np.nanmax(w_t), np.nanmax(w_s)])),
            "w_mean": float(np.nanmean(0.5 * (w_t + w_s)))}


def envelope_along_path(beam: AstigBeam,
                        spots: np.ndarray,
                        R_t: Sequence[float],
                        R_s: Sequence[float],
                        aoi_rad: Sequence[float],
                        samples_per_segment: int = 12) -> dict:
    """Sample the beam 1/e^2 radius at many points *between* bounce spots, so a
    3D viewer can render a smooth tube.

    Parameters
    ----------
    spots : (B, 3) array of bounce hit-points (the real ray-traced path).

    Returns
    -------
    dict with:
        points  : (P, 3) sampled centre-line positions
        w_t,w_s : (P,) tangential & sagittal radii at each sample
        w       : (P,) mean radius (for an isotropic tube approximation)
    """
    if len(spots) < 2:
        return {"points": spots, "w_t": np.array([beam.w_t]),
                "w_s": np.array([beam.w_s]), "w": np.array([beam.w_t])}
    q_t, q_s = beam.q_t, beam.q_s
    pts: List[np.ndarray] = []
    wt: List[float] = []
    ws: List[float] = []
    n_seg = len(spots) - 1
    for i in range(n_seg):
        A = spots[i]; B = spots[i + 1]
        seg_vec = B - A
        seg_len = float(np.linalg.norm(seg_vec))
        # propagate q across this segment in small steps, recording w
        step = seg_len / samples_per_segment
        for j in range(samples_per_segment):
            pts.append(A + (j / samples_per_segment) * seg_vec)
            wt.append(_w_of_q(q_t, beam.wavelength, beam.M2))
            ws.append(_w_of_q(q_s, beam.wavelength, beam.M2))
            q_t = _apply(q_t, _free(step))
            q_s = _apply(q_s, _free(step))
        # apply the mirror at spot B (end of this segment) if curved
        if i < len(R_t):
            f_t, f_s = astigmatic_focal_lengths(R_t[i], R_s[i], aoi_rad[i])
            q_t = _apply(q_t, _lens(f_t))
            q_s = _apply(q_s, _lens(f_s))
    # final point
    pts.append(spots[-1])
    wt.append(_w_of_q(q_t, beam.wavelength, beam.M2))
    ws.append(_w_of_q(q_s, beam.wavelength, beam.M2))
    pts = np.array(pts)
    wt = np.array(wt); ws = np.array(ws)
    return {"points": pts, "w_t": wt, "w_s": ws, "w": 0.5 * (wt + ws)}


# =============================================================================
# 4. Round-trip stability (per plane, from the unit-cell ABCD)
# =============================================================================
def unit_cell_stability(L_leg: float, R: float, aoi_rad: float,
                        plane: str = "tangential") -> float:
    """Stability parameter m = (A+D)/2 of one (free-space + mirror) unit cell.
    |m| <= 1 => a bounded Gaussian mode exists (stable)."""
    f_t, f_s = astigmatic_focal_lengths(R, R, aoi_rad)
    f = f_t if plane == "tangential" else f_s
    M = _lens(f) @ _free(L_leg)
    return float((M[0, 0] + M[1, 1]) / 2.0)
