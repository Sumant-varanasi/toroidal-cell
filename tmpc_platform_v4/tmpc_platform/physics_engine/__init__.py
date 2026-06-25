"""Physics engine for toroidal multipass cells.

Provides:
    - toroidal_surface  : surface equations, normals, intersections
    - ray_tracer        : 3D vector ray tracing with reflection
    - gaussian_beam     : Gaussian beam + ABCD propagation
    - multipass         : full multipass cell simulation
    - losses            : reflectivity, clipping, aperture, truncation
    - stability         : cavity stability and re-entrance analysis
"""
from .toroidal_surface import ToroidalSurface
from .ray_tracer import Ray, trace_ray, reflect
from .gaussian_beam import GaussianBeam, abcd_propagate
from .multipass import TMPCConfig, simulate_tmpc, SimResult
from .losses import LossBudget, compute_losses
from .stability import stability_parameter, is_stable, reentrance_score

__all__ = [
    "ToroidalSurface", "Ray", "trace_ray", "reflect",
    "GaussianBeam", "abcd_propagate",
    "TMPCConfig", "simulate_tmpc", "SimResult",
    "LossBudget", "compute_losses",
    "stability_parameter", "is_stable", "reentrance_score",
]
