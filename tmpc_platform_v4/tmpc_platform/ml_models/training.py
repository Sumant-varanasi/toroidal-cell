"""Shared training/evaluation helpers."""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error


FEATURES = [
    "N", "R_ring", "H", "R_t", "R_s",
    "chord_skip", "w0", "reflectivity",
]

TARGETS = ["opl_m", "throughput_full", "quality", "stability_g"]


def prepare_xy(df: pd.DataFrame, target: str,
               test_size: float = 0.0, seed: int = 0
               ) -> Tuple[np.ndarray, np.ndarray]:
    """Return (X, y) arrays. If test_size>0 returns train/test tuples."""
    df = df.dropna(subset=FEATURES + [target]).copy()
    X = df[FEATURES].to_numpy(dtype=float)
    y = df[target].to_numpy(dtype=float)
    if test_size > 0:
        return train_test_split(X, y, test_size=test_size, random_state=seed)
    return X, y


def evaluate_model(model, df: pd.DataFrame, target: str,
                   test_size: float = 0.2, seed: int = 0):
    Xtr, Xte, ytr, yte = prepare_xy(df, target, test_size=test_size, seed=seed)
    model.fit(Xtr, ytr)
    yp = model.predict(Xte)
    return float(r2_score(yte, yp)), float(mean_absolute_error(yte, yp))
