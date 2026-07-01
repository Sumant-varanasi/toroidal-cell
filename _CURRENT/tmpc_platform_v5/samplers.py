"""Parameter-space samplers + Thorlabs concave-mirror catalogue."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. Parameter spec
# =============================================================================
@dataclass
class ParamSpec:
    name: str
    low: float
    high: float
    is_int: bool = False


def default_parameter_space() -> List[ParamSpec]:
    return [
        ParamSpec("N",                8,    16,   is_int=True),
        ParamSpec("R_ring",          30.0, 80.0),
        ParamSpec("H",               20.0, 60.0),
        ParamSpec("R_t",             40.0, 200.0),
        ParamSpec("R_s",             40.0, 200.0),
        ParamSpec("mirror_aperture",  5.0, 12.0),
        ParamSpec("chord_skip",       1,    7,   is_int=True),
        ParamSpec("w0",               0.2,  1.5),
        ParamSpec("input_offset_z",  -3.0,  3.0),
        ParamSpec("input_angle",     -0.05, 0.05),
    ]


def _scale(u: np.ndarray, specs: Sequence[ParamSpec]) -> List[Dict]:
    out: List[Dict] = []
    for row in u:
        cfg: Dict = {}
        for v, s in zip(row, specs):
            x = s.low + v * (s.high - s.low)
            cfg[s.name] = int(round(x)) if s.is_int else float(x)
        out.append(cfg)
    return out


def sobol_sample(n: int, specs: Optional[Sequence[ParamSpec]] = None,
                 seed: int = 0) -> List[Dict]:
    from scipy.stats import qmc
    specs = specs or default_parameter_space()
    u = qmc.Sobol(d=len(specs), scramble=True, seed=seed).random(n)
    return _scale(u, specs)


def lhs_sample(n: int, specs: Optional[Sequence[ParamSpec]] = None,
               seed: int = 0) -> List[Dict]:
    from scipy.stats import qmc
    specs = specs or default_parameter_space()
    u = qmc.LatinHypercube(d=len(specs), seed=seed).random(n)
    return _scale(u, specs)


# =============================================================================
# 2. Thorlabs catalogue (protected gold, 1654 nm)
# =============================================================================
HALF_INCH_GOLD_CONCAVE: List[Tuple[str, float, float]] = [
    ("CM127-010-M01",  9.5,   19.0),
    ("CM127-012-M01", 12.0,   24.0),
    ("CM127-025-M01", 25.0,   50.0),
    ("CM127-050-M01", 50.0,  100.0),
]
ONE_INCH_GOLD_CONCAVE: List[Tuple[str, float, float]] = [
    ("CM254-019-M01",   19.0,   38.0),
    ("CM254-025-M01",   25.0,   50.0),
    ("CM254-050-M01",   50.0,  100.0),
    ("CM254-075-M01",   75.0,  150.0),
    ("CM254-100-M01",  100.0,  200.0),
    ("CM254-150-M01",  150.0,  300.0),
    ("CM254-200-M01",  200.0,  400.0),
    ("CM254-250-M01",  250.0,  500.0),
    ("CM254-500-M01",  500.0, 1000.0),
    ("CM254-750-M01",  750.0, 1500.0),
    ("CM254-1000-M01", 1000.0, 2000.0),
]
FAMILIES = {
    "half_inch": {"catalog": HALF_INCH_GOLD_CONCAVE,
                  "diameter_mm": 12.7, "clear_aperture_radius_mm": 5.7},
    "one_inch":  {"catalog": ONE_INCH_GOLD_CONCAVE,
                  "diameter_mm": 25.4, "clear_aperture_radius_mm": 11.4},
}
REFLECTIVITY_1654NM = 0.97


def get_family(family: str = "half_inch") -> dict:
    if family not in FAMILIES:
        raise ValueError(f"Unknown family '{family}'. Options: {list(FAMILIES)}")
    return FAMILIES[family]


def catalog_rocs(family: str = "half_inch") -> np.ndarray:
    return np.array([roc for _, _, roc in get_family(family)["catalog"]],
                    dtype=float)


def catalog_skus(family: str = "half_inch") -> List[str]:
    return [sku for sku, _, _ in get_family(family)["catalog"]]


def snap_to_catalog(roc: float, family: str = "half_inch") -> Tuple[float, str]:
    rocs = catalog_rocs(family)
    skus = catalog_skus(family)
    idx = int(np.argmin(np.abs(rocs - roc)))
    return float(rocs[idx]), skus[idx]


def thorlabs_parameter_space(family: str = "half_inch") -> List[ParamSpec]:
    if family == "half_inch":
        ring_lo, ring_hi, h_lo, h_hi = 15.0, 50.0, 15.0, 50.0
    elif family == "one_inch":
        ring_lo, ring_hi, h_lo, h_hi = 25.0, 120.0, 20.0, 80.0
    else:
        ring_lo, ring_hi, h_lo, h_hi = 30.0, 80.0, 20.0, 60.0
    return [
        ParamSpec("N",                8,    16,   is_int=True),
        ParamSpec("R_ring",          ring_lo, ring_hi),
        ParamSpec("H",               h_lo, h_hi),
        ParamSpec("chord_skip",       1,    7,   is_int=True),
        ParamSpec("w0",               0.2,  1.5),
        ParamSpec("input_offset_z",  -3.0,  3.0),
        ParamSpec("input_angle",     -0.05, 0.05),
    ]


def thorlabs_sobol_sample(n: int, seed: int = 0,
                          family: str = "half_inch") -> List[Dict]:
    from scipy.stats import qmc
    specs = thorlabs_parameter_space(family)
    fam = get_family(family)
    aperture = fam["clear_aperture_radius_mm"]
    u = qmc.Sobol(d=len(specs) + 1, scramble=True, seed=seed).random(n)
    rocs = catalog_rocs(family)
    skus = catalog_skus(family)
    out: List[Dict] = []
    for row in u:
        cfg: Dict = {}
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
