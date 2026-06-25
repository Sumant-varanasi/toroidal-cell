"""SHAP-based feature attribution."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from typing import Dict
from ..ml_models.training import FEATURES


def compute_shap(model, df: pd.DataFrame,
                 target: str,
                 out_dir: str = "results/explain",
                 max_samples: int = 200) -> Dict:
    """Compute SHAP values; gracefully falls back to permutation importance."""
    os.makedirs(out_dir, exist_ok=True)
    df = df.dropna(subset=FEATURES + [target]).copy()
    X = df[FEATURES].to_numpy(dtype=float)
    if len(X) > max_samples:
        idx = np.random.default_rng(0).choice(len(X), max_samples, replace=False)
        X = X[idx]
    out = {"features": FEATURES, "target": target}
    try:
        import shap
        # tree models support TreeExplainer; otherwise use KernelExplainer w/ sample
        try:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X)
        except Exception:
            background = shap.sample(X, min(50, len(X)))
            explainer = shap.KernelExplainer(model.predict, background)
            sv = explainer.shap_values(X, nsamples=100)
        sv = np.array(sv)
        mean_abs = np.mean(np.abs(sv), axis=0)
        out["method"] = "shap"
        out["mean_abs_shap"] = dict(zip(FEATURES, mean_abs.tolist()))
        # save raw
        np.save(os.path.join(out_dir, f"shap_values__{target}.npy"), sv)
    except Exception as e:
        # permutation importance fallback
        from sklearn.inspection import permutation_importance
        y = df[target].to_numpy(dtype=float)
        if len(y) > max_samples:
            y = y[idx]
        try:
            r = permutation_importance(model, X, y, n_repeats=5, random_state=0)
            out["method"] = "permutation"
            out["mean_abs_shap"] = dict(zip(FEATURES, r.importances_mean.tolist()))
        except Exception as e2:
            out["method"] = "failed"
            out["error"] = f"{e} | {e2}"
            return out

    pd.DataFrame([out["mean_abs_shap"]]).T.rename(
        columns={0: "importance"}).to_csv(
        os.path.join(out_dir, f"importance__{target}.csv"))
    return out
