"""Stacking ensemble of trained surrogates."""
from __future__ import annotations
import numpy as np
import joblib
import os
import pandas as pd
from typing import List, Dict
from sklearn.linear_model import Ridge
from .training import FEATURES, prepare_xy


class StackingSurrogate:
    """Combine N base models via a Ridge meta-learner.

    Each base model must implement .predict(X) returning a 1-D array.
    """

    def __init__(self, base_models: List, alpha: float = 1.0):
        self.base_models = base_models
        self.meta = Ridge(alpha=alpha)

    def _stack(self, X):
        return np.column_stack([m.predict(X) for m in self.base_models])

    def fit(self, X, y):
        S = self._stack(X)
        self.meta.fit(S, y)
        return self

    def predict(self, X):
        S = self._stack(X)
        return self.meta.predict(S)


def build_ensemble_for_target(df: pd.DataFrame, target: str,
                              model_dir: str = "results/models",
                              out_dir: str = "results/models") -> Dict:
    """Load all trained models for `target` and fit a stacking meta-learner."""
    base = []
    names = []
    for fn in os.listdir(model_dir):
        if fn.endswith(f"__{target}.joblib"):
            base.append(joblib.load(os.path.join(model_dir, fn)))
            names.append(fn)
    if not base:
        return {"built": False, "reason": "no base models found"}
    X, y = prepare_xy(df, target)
    ens = StackingSurrogate(base)
    ens.fit(X, y)
    path = os.path.join(out_dir, f"Ensemble__{target}.joblib")
    joblib.dump(ens, path)
    return {"built": True, "path": path, "base_models": names}
