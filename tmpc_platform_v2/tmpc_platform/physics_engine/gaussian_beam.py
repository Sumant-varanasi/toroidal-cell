"""Gaussian beam propagation with ABCD matrices.

Tracks complex q-parameter through arbitrary sequences of free-space
propagation and curved-mirror reflections, separately for the tangential
and sagittal planes (toroidal mirrors have two distinct focal lengths).
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class GaussianBeam:
    wavelength: float        # [mm]  e.g. 1.654e-3 for 1654 nm
    w0: float                # waist radius at z=0 [mm]
    z0: float = 0.0          # waist position [mm]

    @property
    def zR(self) -> float:
        return np.pi * self.w0 ** 2 / self.wavelength

    def q(self, z: float = 0.0) -> complex:
        return (z - self.z0) + 1j * self.zR

    def w(self, z: float) -> float:
        return self.w0 * np.sqrt(1.0 + ((z - self.z0) / self.zR) ** 2)


def free_space(d: float) -> np.ndarray:
    return np.array([[1.0, d], [0.0, 1.0]])


def thin_mirror(f: float) -> np.ndarray:
    """Curved mirror as a thin lens of focal length f = R/2 (paraxial)."""
    return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])


def abcd_propagate(q_in: complex, M: np.ndarray) -> complex:
    A, B = M[0]
    C, D = M[1]
    return (A * q_in + B) / (C * q_in + D)


def beam_radius_from_q(q: complex, wavelength: float) -> float:
    """Beam radius w from complex q-parameter."""
    inv_q = 1.0 / q
    inv_w2 = -inv_q.imag * np.pi / wavelength
    if inv_w2 <= 0:
        return float("inf")
    return np.sqrt(1.0 / inv_w2)


def propagate_through_cell(beam: GaussianBeam,
                           segments: List[float],
                           focal_tan: List[float],
                           focal_sag: List[float]):
    """Propagate beam through a sequence of (free-space, mirror) elements.

    Parameters
    ----------
    segments  : free-space lengths [mm] between successive mirrors
    focal_tan : tangential focal lengths at each mirror
    focal_sag : sagittal   focal lengths at each mirror

    Returns dict with per-bounce beam radii in tangential & sagittal planes.
    """
    q_t = beam.q(0.0)
    q_s = beam.q(0.0)
    w_t = [beam.w0]
    w_s = [beam.w0]
    for i, d in enumerate(segments):
        # free-space
        q_t = abcd_propagate(q_t, free_space(d))
        q_s = abcd_propagate(q_s, free_space(d))
        # mirror (if any at this index)
        if i < len(focal_tan):
            q_t = abcd_propagate(q_t, thin_mirror(focal_tan[i]))
            q_s = abcd_propagate(q_s, thin_mirror(focal_sag[i]))
        w_t.append(beam_radius_from_q(q_t, beam.wavelength))
        w_s.append(beam_radius_from_q(q_s, beam.wavelength))
    return {"w_tangential": np.array(w_t), "w_sagittal": np.array(w_s),
            "w_max": max(max(w_t), max(w_s))}
