"""Thorlabs catalogue constraints for the TMPC platform.

Restricts the search space to off-the-shelf protected gold spherical
concave mirrors. Two families are supported:

  half_inch : CM127-*-M01  (Ø12.7 mm, clear aperture ~5.7 mm radius, 4 SKUs)
  one_inch  : CM254-*-M01  (Ø25.4 mm, clear aperture ~11.4 mm radius, 11 SKUs)

Reference: https://www.thorlabs.com (Concave Mirrors, Protected Gold, 800 nm - 20 um)
"""
from __future__ import annotations
import numpy as np
from typing import List, Tuple


# ---- Ø1/2" catalogue: (SKU, focal_length_mm, ROC_mm = 2f) ----
HALF_INCH_GOLD_CONCAVE: List[Tuple[str, float, float]] = [
    ("CM127-010-M01",  9.5,   19.0),
    ("CM127-012-M01", 12.0,   24.0),
    ("CM127-025-M01", 25.0,   50.0),
    ("CM127-050-M01", 50.0,  100.0),
]

# ---- Ø1" catalogue ----
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
    "half_inch": {
        "catalog": HALF_INCH_GOLD_CONCAVE,
        "diameter_mm": 12.7,
        "clear_aperture_radius_mm": 5.7,  # >90% of D/2 = 5.715
    },
    "one_inch": {
        "catalog": ONE_INCH_GOLD_CONCAVE,
        "diameter_mm": 25.4,
        "clear_aperture_radius_mm": 11.4,  # >90% of D/2 = 11.43
    },
}

REFLECTIVITY_1654NM = 0.97          # protected gold >96% over 800nm-20um

# Default (kept for backward compat with old imports)
DIAMETER_MM = FAMILIES["half_inch"]["diameter_mm"]
CLEAR_APERTURE_RADIUS_MM = FAMILIES["half_inch"]["clear_aperture_radius_mm"]


def get_family(family: str = "half_inch") -> dict:
    if family not in FAMILIES:
        raise ValueError(f"Unknown family '{family}'. Options: {list(FAMILIES)}")
    return FAMILIES[family]


def catalog_rocs(family: str = "half_inch") -> np.ndarray:
    """Sorted array of available ROC values [mm] for given family."""
    cat = get_family(family)["catalog"]
    return np.array([roc for _, _, roc in cat], dtype=float)


def catalog_skus(family: str = "half_inch") -> List[str]:
    return [sku for sku, _, _ in get_family(family)["catalog"]]


def snap_to_catalog(roc: float, family: str = "half_inch") -> Tuple[float, str]:
    """Snap an arbitrary ROC to the nearest catalogue value.
    Returns (snapped_ROC_mm, SKU)."""
    rocs = catalog_rocs(family)
    skus = catalog_skus(family)
    idx = int(np.argmin(np.abs(rocs - roc)))
    return float(rocs[idx]), skus[idx]


def sku_for_roc(roc: float, family: str = "half_inch", tol: float = 0.5) -> str:
    """Return SKU for exact-or-nearby ROC; '' if not in catalogue."""
    for sku, _, R in get_family(family)["catalog"]:
        if abs(R - roc) <= tol:
            return sku
    return ""
