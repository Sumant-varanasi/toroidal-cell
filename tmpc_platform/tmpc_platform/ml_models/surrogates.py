"""Surrogate models for the TMPC simulator.

All models share the same scikit-learn-style fit/predict interface.
Models are trained per target: opl_m, throughput_full, quality, stability_g.
"""
from __future__ import annotations
import os
import time
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List

from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel as C, WhiteKernel
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.neural_network import MLPRegressor

from .training import FEATURES, TARGETS, prepare_xy, evaluate_model

try:
    import xgboost as xgb
    _HAS_XGB = True
except Exception:
    _HAS_XGB = False

try:
    import lightgbm as lgb
    _HAS_LGB = True
except Exception:
    _HAS_LGB = False


def _wrap_with_scaler(estimator):
    """Wrap an estimator so X is auto-scaled."""
    from sklearn.pipeline import Pipeline
    return Pipeline([("scaler", StandardScaler()), ("model", estimator)])


def train_random_forest(df: pd.DataFrame, target: str, **kw):
    X, y = prepare_xy(df, target)
    model = RandomForestRegressor(
        n_estimators=kw.get("n_estimators", 300),
        max_depth=kw.get("max_depth", None),
        n_jobs=-1, random_state=0)
    model.fit(X, y)
    return model


def train_xgboost(df: pd.DataFrame, target: str, **kw):
    if not _HAS_XGB:
        return None
    X, y = prepare_xy(df, target)
    model = xgb.XGBRegressor(
        n_estimators=kw.get("n_estimators", 500),
        max_depth=kw.get("max_depth", 6),
        learning_rate=kw.get("lr", 0.05),
        n_jobs=-1, random_state=0,
        tree_method="hist")
    model.fit(X, y)
    return model


def train_lightgbm(df: pd.DataFrame, target: str, **kw):
    if not _HAS_LGB:
        return None
    X, y = prepare_xy(df, target)
    model = lgb.LGBMRegressor(
        n_estimators=kw.get("n_estimators", 500),
        max_depth=kw.get("max_depth", -1),
        learning_rate=kw.get("lr", 0.05),
        n_jobs=-1, random_state=0, verbose=-1)
    model.fit(X, y)
    return model


def train_gaussian_process(df: pd.DataFrame, target: str, max_n: int = 800, **kw):
    """GPR scales O(n^3); subsample if dataset is large."""
    X, y = prepare_xy(df, target)
    if len(X) > max_n:
        idx = np.random.default_rng(0).choice(len(X), max_n, replace=False)
        X, y = X[idx], y[idx]
    kernel = C(1.0) * Matern(length_scale=1.0, nu=2.5) + WhiteKernel(noise_level=1e-3)
    model = _wrap_with_scaler(GaussianProcessRegressor(kernel=kernel,
                                                       normalize_y=True,
                                                       n_restarts_optimizer=2,
                                                       random_state=0))
    model.fit(X, y)
    return model


def train_neural_net(df: pd.DataFrame, target: str, **kw):
    X, y = prepare_xy(df, target)
    model = _wrap_with_scaler(MLPRegressor(
        hidden_layer_sizes=kw.get("hidden", (128, 128, 64)),
        activation="relu", solver="adam",
        max_iter=kw.get("max_iter", 400),
        early_stopping=True, random_state=0))
    model.fit(X, y)
    return model


def train_all_surrogates(df: pd.DataFrame, targets: List[str] = None,
                         out_dir: str = "results/models") -> Dict:
    """Train every available model for every target. Returns dict of metrics."""
    os.makedirs(out_dir, exist_ok=True)
    targets = targets or TARGETS
    metrics = []
    saved = {}
    trainers = {
        "RandomForest": train_random_forest,
        "XGBoost":      train_xgboost,
        "LightGBM":     train_lightgbm,
        "GaussianProcess": train_gaussian_process,
        "NeuralNet":    train_neural_net,
    }
    for tgt in targets:
        for name, trainer in trainers.items():
            t0 = time.time()
            try:
                model = trainer(df, tgt)
            except Exception as e:
                metrics.append({"target": tgt, "model": name,
                                "r2": np.nan, "mae": np.nan,
                                "fit_s": np.nan, "error": str(e)})
                continue
            if model is None:
                continue
            r2, mae = evaluate_model(model, df, tgt)
            dt = time.time() - t0
            path = os.path.join(out_dir, f"{name}__{tgt}.joblib")
            joblib.dump(model, path)
            saved[(name, tgt)] = path
            metrics.append({"target": tgt, "model": name,
                            "r2": r2, "mae": mae,
                            "fit_s": dt, "path": path})
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(os.path.join(out_dir, "metrics.csv"), index=False)
    return {"metrics": metrics_df, "models": saved}
