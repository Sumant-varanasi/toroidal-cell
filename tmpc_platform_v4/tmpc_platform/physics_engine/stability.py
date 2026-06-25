"""Cavity stability and re-entrance analysis."""
from __future__ import annotations
import numpy as np
from math import gcd


def stability_parameter(chord_length: float, ROC: float) -> float:
    """Symmetric two-mirror g-parameter product for a chord of given length.
    The cavity is stable when 0 <= g1*g2 <= 1.
    """
    g = 1.0 - chord_length / ROC
    return g * g


def is_stable(chord_length: float, ROC: float, eps: float = 1e-6) -> bool:
    g2 = stability_parameter(chord_length, ROC)
    return -eps <= g2 <= 1.0 + eps


def reentrance_score(N: int, chord_skip: int) -> float:
    """How quickly the chord pattern closes on itself.

    Period of the orbit is N / gcd(N, chord_skip). Score is normalised to [0,1]
    where 1.0 means the orbit visits all N mirror positions (coprime).
    """
    if N <= 0 or chord_skip <= 0:
        return 0.0
    period = N // gcd(N, chord_skip)
    return period / N
