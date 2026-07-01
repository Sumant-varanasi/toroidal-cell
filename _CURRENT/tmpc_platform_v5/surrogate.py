"""Quick RandomForest surrogate over a generated dataset.

Trains one regressor per target, returns R² + MAE and a callable that maps a
feature vector to a prediction. For the heavier ML stack (XGBoost, LightGBM,
PINN, stacking ensembles), use the v4 platform — this module is intentionally
minimal but enough for a closed-loop run.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

FEATURES = ["N", "R_ring", "H", "R_t", "R_s",
            "chord_skip", "w0", "reflectivity"]
DEFAULT_TARGETS = ["opl_m", "throughput", "quality", "stability_g"]


def train_surrogates(df: pd.DataFrame, targets: List[str] = None,
                     test_size: float = 0.2, seed: int = 0,
                     n_estimators: int = 200) -> Dict:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split

    targets = targets or DEFAULT_TARGETS
    out_models: Dict[str, RandomForestRegressor] = {}
    metrics_rows = []
    importances_rows = []
    for tgt in targets:
        if tgt not in df.columns:
            continue
        sub = df.dropna(subset=FEATURES + [tgt])
        X = sub[FEATURES].to_numpy(dtype=float)
        y = sub[tgt].to_numpy(dtype=float)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size,
                                              random_state=seed)
        m = RandomForestRegressor(n_estimators=n_estimators,
                                  random_state=seed, n_jobs=-1)
        m.fit(Xtr, ytr)
        yp = m.predict(Xte)
        metrics_rows.append({"target": tgt,
                             "r2": float(r2_score(yte, yp)),
                             "mae": float(mean_absolute_error(yte, yp))})
        importances_rows.append({"target": tgt,
                                 **dict(zip(FEATURES, m.feature_importances_))})
        out_models[tgt] = m
    return {"models": out_models,
            "metrics": pd.DataFrame(metrics_rows),
            "importance": pd.DataFrame(importances_rows)}
