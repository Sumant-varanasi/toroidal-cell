"""Quasi-random samplers for the TMPC parameter space."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from ..physics_engine.thorlabs_catalog import (
    catalog_rocs, catalog_skus, get_family,
    REFLECTIVITY_1654NM,
)


@dataclass
class ParamSpec:
    name: str
    low: float
    high: float
    is_int: bool = False


def parameter_space() -> List[ParamSpec]:
    """Default search space for the TMPC platform."""
    return [
        ParamSpec("N",          8,    16,   is_int=True),
        ParamSpec("R_ring",     30.0, 80.0),
        ParamSpec("H",          20.0, 60.0),
        ParamSpec("R_t",        40.0, 200.0),
        ParamSpec("R_s",        40.0, 200.0),
        ParamSpec("mirror_aperture", 5.0, 12.0),
        ParamSpec("chord_skip", 1,    7,    is_int=True),  # validated against N at eval time
        ParamSpec("w0",         0.2,  1.5),
        ParamSpec("input_offset_z", -3.0, 3.0),
        ParamSpec("input_angle", -0.05, 0.05),
    ]


def _scale(u: np.ndarray, specs: List[ParamSpec]) -> List[Dict]:
    out = []
    for row in u:
        cfg = {}
        for v, s in zip(row, specs):
            x = s.low + v * (s.high - s.low)
            cfg[s.name] = int(round(x)) if s.is_int else float(x)
        out.append(cfg)
    return out


def sobol_sample(n: int, specs: List[ParamSpec] = None, seed: int = 0) -> List[Dict]:
    from scipy.stats import qmc
    specs = specs or parameter_space()
    sampler = qmc.Sobol(d=len(specs), scramble=True, seed=seed)
    u = sampler.random(n)
    return _scale(u, specs)


def lhs_sample(n: int, specs: List[ParamSpec] = None, seed: int = 0) -> List[Dict]:
    from scipy.stats import qmc
    specs = specs or parameter_space()
    sampler = qmc.LatinHypercube(d=len(specs), seed=seed)
    u = sampler.random(n)
    return _scale(u, specs)


# --------------------------------------------------------------------------
# Thorlabs-constrained sampling
# --------------------------------------------------------------------------
def thorlabs_parameter_space(family: str = "half_inch") -> List[ParamSpec]:
    """Reduced parameter space for Thorlabs spherical mirrors.

    R_t = R_s (spherical), aperture and reflectivity locked. R is sampled
    separately from the chosen catalogue.

    R_ring range is family-dependent. Smallest ROC sets a soft upper bound
    on R_ring for cavity stability (need chord < ROC).
    """
    if family == "half_inch":
        # smallest ROC = 19 mm; R_ring max ~50 mm
        ring_lo, ring_hi = 15.0, 50.0
        h_lo, h_hi = 15.0, 50.0
    elif family == "one_inch":
        # smallest ROC = 38 mm; bigger aperture allows larger R_ring too
        ring_lo, ring_hi = 25.0, 120.0
        h_lo, h_hi = 20.0, 80.0
    else:
        ring_lo, ring_hi = 30.0, 80.0
        h_lo, h_hi = 20.0, 60.0
    return [
        ParamSpec("N",          8,    16,   is_int=True),
        ParamSpec("R_ring",     ring_lo, ring_hi),
        ParamSpec("H",          h_lo, h_hi),
        ParamSpec("chord_skip", 1,    7,    is_int=True),
        ParamSpec("w0",         0.2,  1.5),
        ParamSpec("input_offset_z", -3.0, 3.0),
        ParamSpec("input_angle", -0.05, 0.05),
    ]


def thorlabs_sobol_sample(n: int, seed: int = 0,
                          family: str = "half_inch") -> List[Dict]:
    """Sobol-sampled configs constrained to chosen Thorlabs catalogue."""
    from scipy.stats import qmc
    specs = thorlabs_parameter_space(family)
    fam = get_family(family)
    aperture = fam["clear_aperture_radius_mm"]
    sampler = qmc.Sobol(d=len(specs) + 1, scramble=True, seed=seed)
    u = sampler.random(n)
    rocs = catalog_rocs(family)
    skus = catalog_skus(family)
    out = []
    for row in u:
        cfg = {}
        for v, s in zip(row[:len(specs)], specs):
            x = s.low + v * (s.high - s.low)
            cfg[s.name] = int(round(x)) if s.is_int else float(x)
        idx = int(row[-1] * len(rocs)) % len(rocs)
        cfg["R_t"] = float(rocs[idx])
        cfg["R_s"] = float(rocs[idx])
        cfg["thorlabs_sku"]    = skus[idx]
        cfg["thorlabs_family"] = family
        cfg["mirror_aperture"] = aperture
        cfg["reflectivity"]    = REFLECTIVITY_1654NM
        out.append(cfg)
    return out
