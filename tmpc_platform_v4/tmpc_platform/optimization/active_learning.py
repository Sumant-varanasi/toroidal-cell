"""Active learning: iteratively query the most uncertain configurations."""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Callable, Dict
from ..ml_models.training import FEATURES
from ..dataset_generation.sampler import sobol_sample, parameter_space


def active_learning_loop(initial_df: pd.DataFrame,
                         simulator_fn: Callable[[Dict], Dict],
                         model_builder: Callable[[pd.DataFrame], object],
                         target: str = "quality",
                         n_rounds: int = 5,
                         pool_size: int = 200,
                         queries_per_round: int = 20) -> Dict:
    """Active learning with uncertainty-based query (random-forest std proxy).

    simulator_fn(cfg_dict) -> row dict (same keys as dataset rows)
    model_builder(df) -> trained model with .predict
    """
    df = initial_df.copy()
    history = []
    for r in range(n_rounds):
        model = model_builder(df)
        pool = sobol_sample(pool_size, seed=r + 1)
        Xp = np.array([[cfg.get(f, 0.0) for f in FEATURES] for cfg in pool])
        # uncertainty proxy: ensemble of trees -> std
        try:
            stds = np.std([est.predict(Xp) for est in model.estimators_], axis=0)
        except Exception:
            stds = np.zeros(len(pool))
        # query top-uncertainty
        idx = np.argsort(-stds)[:queries_per_round]
        new_rows = []
        for j in idx:
            r_row = simulator_fn(pool[j])
            if r_row is not None:
                new_rows.append(r_row)
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        history.append({"round": r, "n_total": len(df),
                        "max_unc": float(stds.max()) if len(stds) else 0.0})
    return {"final_df": df, "history": pd.DataFrame(history)}
