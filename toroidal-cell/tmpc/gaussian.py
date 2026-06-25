"""
gaussian.py
===========

Gaussian beam optics and ABCD matrix analysis for the toroidal multipass cell.

Two regimes:

1. Flat ring mirrors (ROC = inf)
   The beam propagates in free space between reflections. The waist size is
   fully determined by the input collimator. There is no in-cell focusing,
   so beam diameter grows as

        w(z) = w0 * sqrt(1 + ((z - z_w) / z_R)^2),
        z_R = pi w0^2 / (M^2 lambda),

   where z is the cumulative optical path and z_w is the waist position
   along that path.

2. Curved ring mirrors (ROC < inf)
   Each reflection acts as a thin lens. Because the angle of incidence at
   ring mirrors of a regular polygon is theta_i = pi/2 - pi/N (large for
   small N), reflection off a spherical mirror introduces strong
   astigmatism. We use the standard splittings

        f_tan = ROC * cos(theta_i) / 2     (tangential / meridional)
        f_sag = ROC / (2 cos(theta_i))     (sagittal)

   The unit-cell ABCD matrix is computed in each plane separately, and the
   stability parameter is reported per plane.

A single "unit cell" of the unfolded multipass system is

    free space (L_leg) -> thin lens (f) -> ...

For a closed pattern that returns to the entrance after total_reflections
bounces, the resonator-style stability requirement is

        |(A + D) / 2| <= 1

evaluated on the unit-cell ABCD matrix.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np


# ---------------------------------------------------------------------------
# Gaussian beam container
# ---------------------------------------------------------------------------
@dataclass
class GaussianBeam:
    """Represents a Gaussian beam by its complex q-parameter.

    1/q = 1/R - i lambda / (pi n w^2)
    """
    q: complex
    wavelength: float
    M2: float = 1.0

    @classmethod
    def from_waist(cls, w0: float, wavelength: float,
                   distance_from_waist: float = 0.0,
                   M2: float = 1.0) -> "GaussianBeam":
        zR = math.pi * w0 ** 2 / (M2 * wavelength)
        q = complex(distance_from_waist, zR)
        return cls(q=q, wavelength=wavelength, M2=M2)

    # ----- derived quantities ----------------------------------------------
    @property
    def w(self) -> float:
        """1/e^2 intensity radius."""
        inv_q = 1.0 / self.q
        # Im(1/q) = -lambda / (pi w^2 M2)  for embedded-Gaussian formulation
        return math.sqrt(-self.M2 * self.wavelength / (math.pi * inv_q.imag))

    @property
    def R(self) -> float:
        """Wavefront radius of curvature (inf for collimated)."""
        inv_q = 1.0 / self.q
        return math.inf if abs(inv_q.real) < 1e-30 else 1.0 / inv_q.real

    @property
    def rayleigh(self) -> float:
        return self.q.imag

    @property
    def divergence_halfangle(self) -> float:
        """Far-field 1/e^2 half-angle in radians."""
        w0 = math.sqrt(self.q.imag * self.M2 * self.wavelength / math.pi)
        return self.M2 * self.wavelength / (math.pi * w0)


# ---------------------------------------------------------------------------
# ABCD matrix elements
# ---------------------------------------------------------------------------
def free_space(d: float) -> np.ndarray:
    return np.array([[1.0, d], [0.0, 1.0]])


def thin_lens(f: float) -> np.ndarray:
    if math.isinf(f):
        return np.array([[1.0, 0.0], [0.0, 1.0]])
    return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])


def mirror_focal_lengths(ROC: float, theta_i_rad: float) -> tuple[float, float]:
    """Tangential and sagittal effective focal lengths for an off-axis
    spherical mirror.

    Returns
    -------
    (f_tangential, f_sagittal)   both in metres. inf if ROC is inf.
    """
    if math.isinf(ROC):
        return math.inf, math.inf
    f_tan = ROC * math.cos(theta_i_rad) / 2.0
    f_sag = ROC / (2.0 * math.cos(theta_i_rad))
    return f_tan, f_sag


# ---------------------------------------------------------------------------
# Apply ABCD to a beam
# ---------------------------------------------------------------------------
def apply_abcd(beam: GaussianBeam, M: np.ndarray) -> GaussianBeam:
    A, B = M[0, 0], M[0, 1]
    C, D = M[1, 0], M[1, 1]
    q_new = (A * beam.q + B) / (C * beam.q + D)
    return GaussianBeam(q=q_new, wavelength=beam.wavelength, M2=beam.M2)


def propagate_beam(beam: GaussianBeam, distance: float) -> GaussianBeam:
    return apply_abcd(beam, free_space(distance))


# ---------------------------------------------------------------------------
# Unit cell for the multipass system
# ---------------------------------------------------------------------------
def abcd_unit_cell(L_leg: float, ROC: float,
                   theta_i_rad: float, plane: str = "tangential"
                   ) -> np.ndarray:
    """ABCD matrix for one leg + one mirror reflection, in the requested plane.

    plane : 'tangential' or 'sagittal'
    """
    f_tan, f_sag = mirror_focal_lengths(ROC, theta_i_rad)
    f = f_tan if plane == "tangential" else f_sag
    return thin_lens(f) @ free_space(L_leg)


def stability(unit_cell: np.ndarray) -> float:
    """Stability parameter (A + D)/2.

    |(A + D)/2| <= 1   →  stable propagation (closed Gaussian mode exists).
    """
    return float((unit_cell[0, 0] + unit_cell[1, 1]) / 2.0)


def round_trip_evolution(L_leg: float, ROC: float, theta_i_rad: float,
                         n_reflections: int, beam_in: GaussianBeam,
                         plane: str = "tangential"
                         ) -> tuple[np.ndarray, np.ndarray]:
    """Track spot radius and wavefront ROC every reflection.

    Returns
    -------
    (w_array, R_array) of length n_reflections + 1 (initial + after each
    reflection).
    """
    unit = abcd_unit_cell(L_leg, ROC, theta_i_rad, plane=plane)
    w = np.empty(n_reflections + 1)
    R = np.empty(n_reflections + 1)
    b = beam_in
    w[0], R[0] = b.w, b.R
    for i in range(n_reflections):
        b = apply_abcd(b, unit)
        w[i + 1], R[i + 1] = b.w, b.R
    return w, R
