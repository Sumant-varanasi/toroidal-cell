"""Global sensitivity analysis via Sobol indices."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from typing import Dict, Callable
from ..ml_models.training import FEATURES
from ..dataset_generation.sampler import parameter_space


def sobol_indices(predictor: Callable[[np.ndarray], np.ndarray],
                  n_samples: int = 1024,
                  out_dir: str = "results/explain",
                  target_name: str = "target") -> Dict:
    """Compute first-order and total Sobol indices.

    Falls back to a Saltelli-style estimator when SALib is unavailable.
    """
    os.makedirs(out_dir, exist_ok=True)
    # Use only the ML FEATURES (which is the predictor's input space)
    all_specs = {s.name: s for s in parameter_space()}
    specs = [all_specs[f] for f in FEATURES if f in all_specs]
    # for FEATURES not in param_space (e.g. reflectivity), use a small range
    for f in FEATURES:
        if f not in all_specs:
            from ..dataset_generation.sampler import ParamSpec
            specs.append(ParamSpec(f, 0.99, 0.9999))
    # match FEATURES order exactly
    specs_by_name = {s.name: s for s in specs}
    specs = [specs_by_name[f] for f in FEATURES]
    bounds = np.array([[s.low, s.high] for s in specs])

    try:
        from SALib.sample import saltelli
        from SALib.analyze import sobol
        problem = {"num_vars": len(specs),
                   "names": [s.name for s in specs],
                   "bounds": bounds.tolist()}
        param_values = saltelli.sample(problem, n_samples, calc_second_order=False)
        Y = predictor(param_values)
        Si = sobol.analyze(problem, Y, calc_second_order=False, print_to_console=False)
        out = {"method": "SALib",
               "S1": dict(zip(problem["names"], Si["S1"].tolist())),
               "ST": dict(zip(problem["names"], Si["ST"].tolist()))}
    except Exception:
        # fallback: simple variance decomposition via random sampling
        rng = np.random.default_rng(0)
        u = rng.random((n_samples, len(specs)))
        X = bounds[:, 0] + u * (bounds[:, 1] - bounds[:, 0])
        Y = predictor(X)
        varY = np.var(Y) + 1e-12
        S1 = {}
        for i, s in enumerate(specs):
            # bin by feature and use between-group variance
            order = np.argsort(X[:, i])
            ybin = np.array_split(Y[order], 20)
            means = np.array([np.mean(b) for b in ybin])
            S1[s.name] = float(np.var(means) / varY)
        out = {"method": "fallback", "S1": S1, "ST": S1}

    pd.DataFrame(out["S1"], index=["S1"]).T.to_csv(
        os.path.join(out_dir, f"sobol_S1__{target_name}.csv"))
    return out


def feature_importance_ranking(*importance_dicts: Dict) -> pd.DataFrame:
    """Combine multiple importance dicts into a ranked table."""
    rows = []
    for d in importance_dicts:
        rows.append(d.get("mean_abs_shap", d.get("S1", {})))
    df = pd.DataFrame(rows)
    df = df.T
    df.columns = [f"src_{i}" for i in range(df.shape[1])]
    df["mean_rank"] = df.rank(ascending=False).mean(axis=1)
    return df.sort_values("mean_rank")
