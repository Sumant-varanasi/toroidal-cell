"""Quasi-random samplers for the TMPC parameter space."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


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
