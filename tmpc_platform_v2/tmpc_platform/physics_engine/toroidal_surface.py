"""Toroidal surface geometry.

A toroidal mirror has two principal radii of curvature:
    R_t : tangential (in-plane, controls in-ring focusing)
    R_s : sagittal   (out-of-plane, controls vertical focusing)

We model each mirror as a small patch of a torus whose axis is locally
perpendicular to the ring normal. The implicit surface (local frame, mirror
vertex at origin, optical axis along +z, sagittal direction along y) is:

    F(x,y,z) = ( sqrt( (R_t - z)^2 + x^2 ) - (R_t - R_s) )^2 + y^2 - R_s^2

For R_t == R_s this reduces to a sphere; for |R_t| >> |R_s| it approaches
a cylinder. The gradient gives the analytic surface normal used for the
exact reflection law.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class ToroidalSurface:
    R_t: float          # tangential radius of curvature [mm]
    R_s: float          # sagittal radius of curvature   [mm]
    aperture: float     # clear aperture radius          [mm]
    center: np.ndarray  # 3D vertex position
    normal: np.ndarray  # outward optical-axis direction (unit)
    sag_axis: np.ndarray  # sagittal direction (unit, perp to normal)

    def __post_init__(self):
        self.center = np.asarray(self.center, dtype=float)
        self.normal = _unit(np.asarray(self.normal, dtype=float))
        self.sag_axis = _unit(np.asarray(self.sag_axis, dtype=float))
        # tangential axis completes right-handed local frame
        self.tan_axis = _unit(np.cross(self.sag_axis, self.normal))

    # ---- world <-> local transforms ----
    def to_local(self, p: np.ndarray) -> np.ndarray:
        d = p - self.center
        return np.array([d @ self.tan_axis, d @ self.sag_axis, d @ self.normal])

    def to_world(self, q: np.ndarray) -> np.ndarray:
        return (self.center
                + q[0] * self.tan_axis
                + q[1] * self.sag_axis
                + q[2] * self.normal)

    def dir_to_local(self, v: np.ndarray) -> np.ndarray:
        return np.array([v @ self.tan_axis, v @ self.sag_axis, v @ self.normal])

    def dir_to_world(self, v: np.ndarray) -> np.ndarray:
        return v[0] * self.tan_axis + v[1] * self.sag_axis + v[2] * self.normal

    # ---- implicit surface ----
    def F_local(self, q: np.ndarray) -> float:
        x, y, z = q
        a = np.sqrt((self.R_t - z) ** 2 + x ** 2) - (self.R_t - self.R_s)
        return a ** 2 + y ** 2 - self.R_s ** 2

    def grad_local(self, q: np.ndarray) -> np.ndarray:
        x, y, z = q
        s = np.sqrt((self.R_t - z) ** 2 + x ** 2) + 1e-30
        a = s - (self.R_t - self.R_s)
        dFdx = 2 * a * x / s
        dFdy = 2 * y
        dFdz = -2 * a * (self.R_t - z) / s
        return np.array([dFdx, dFdy, dFdz])

    def normal_at(self, p_world: np.ndarray) -> np.ndarray:
        """Outward surface normal (world frame) at point p_world on the surface."""
        q = self.to_local(p_world)
        g = self.grad_local(q)
        n_local = _unit(g)
        # ensure it points toward the optical axis (i.e. opposite to incoming ray side)
        if n_local[2] < 0:
            n_local = -n_local
        return self.dir_to_world(n_local)

    # ---- ray intersection (Newton from paraxial seed) ----
    def intersect(self, origin: np.ndarray, direction: np.ndarray,
                  t_max: float = 1e4, tol: float = 1e-9, max_iter: int = 40):
        """Find first intersection of ray (origin, direction) with the surface.

        Returns (t, point) or (None, None) if no valid intersection within aperture.
        """
        o = self.to_local(origin)
        d = self.dir_to_local(direction)

        # paraxial seed: intersect with tangent plane z=0
        if abs(d[2]) < 1e-12:
            return None, None
        t = -o[2] / d[2]
        if t < tol or t > t_max:
            # try a small forward step instead
            t = max(1e-3, t)

        # Newton iteration on F(o + t d) = 0
        for _ in range(max_iter):
            q = o + t * d
            F = self.F_local(q)
            if abs(F) < tol:
                break
            g = self.grad_local(q)
            dF_dt = g @ d
            if abs(dF_dt) < 1e-20:
                return None, None
            t_new = t - F / dF_dt
            if t_new < 0:
                return None, None
            if abs(t_new - t) < tol:
                t = t_new
                break
            t = t_new
        else:
            return None, None

        q = o + t * d
        # aperture check (cylindrical clear aperture about local z)
        r_lat = np.hypot(q[0], q[1])
        if r_lat > self.aperture:
            return t, None  # hit surface plane but outside clear aperture -> clipping
        p_world = self.to_world(q)
        return t, p_world


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-20:
        return v
    return v / n
