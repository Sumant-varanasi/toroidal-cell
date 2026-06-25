"""3D vector ray tracing with exact reflection law."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Ray:
    origin: np.ndarray
    direction: np.ndarray
    path_length: float = 0.0
    alive: bool = True
    history: List[np.ndarray] = field(default_factory=list)

    def __post_init__(self):
        self.origin = np.asarray(self.origin, dtype=float)
        self.direction = _unit(np.asarray(self.direction, dtype=float))
        if not self.history:
            self.history = [self.origin.copy()]

    def advance(self, t: float):
        self.origin = self.origin + t * self.direction
        self.path_length += t
        self.history.append(self.origin.copy())


def reflect(direction: np.ndarray, normal: np.ndarray) -> np.ndarray:
    """Exact reflection of `direction` about `normal`."""
    d = _unit(direction)
    n = _unit(normal)
    return _unit(d - 2.0 * (d @ n) * n)


def trace_ray(ray: Ray, surfaces, max_bounces: int = 1000,
              aoi_record: Optional[List[float]] = None):
    """Sequentially trace `ray` through `surfaces` (list of ToroidalSurface).

    The list defines the sequence of reflections. The caller is responsible
    for determining the bounce sequence (e.g. via the chord pattern).

    Returns dict with: bounces, opl, clipped (bool), exit_ray.
    """
    bounces = 0
    clipped = False
    for surf in surfaces[:max_bounces]:
        t, p = surf.intersect(ray.origin, ray.direction)
        if t is None:
            ray.alive = False
            break
        if p is None:
            # hit plane but outside clear aperture
            clipped = True
            ray.alive = False
            break
        ray.advance(t)
        n = surf.normal_at(p)
        if aoi_record is not None:
            cos_i = abs(ray.direction @ n)
            aoi_record.append(np.degrees(np.arccos(np.clip(cos_i, 0, 1))))
        ray.direction = reflect(ray.direction, n)
        bounces += 1

    return {
        "bounces": bounces,
        "opl": ray.path_length,
        "clipped": clipped,
        "exit_ray": ray,
    }


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-20 else v
