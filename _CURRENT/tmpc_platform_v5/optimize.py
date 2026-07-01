"""Design-space optimisation.

Two engines, same interface:

    random_search(objective, n_trials)       — always available
    bayesian_optimize(objective, n_calls)    — uses scikit-optimize if installed

`objective(cfg_dict)` returns a float. By default we maximise; pass
maximize=False to minimise.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from .physics import TMPCConfig, simulate_tmpc
from .samplers import default_parameter_space, sobol_sample


# =============================================================================
# 1. Random / Sobol search
# =============================================================================
def random_search(objective: Callable[[Dict], float],
                  n_trials: int = 200, seed: int = 0,
                  maximize: bool = True) -> Dict:
    specs = default_parameter_space()
    configs = sobol_sample(n_trials, specs, seed=seed)
    rows = []
    for c in configs:
        if c["chord_skip"] >= c["N"]:
            c["chord_skip"] = max(1, c["N"] - 1)
        try:
            v = float(objective(c))
        except Exception:
            v = -np.inf if maximize else np.inf
        rows.append({**c, "objective": v})
    df = pd.DataFrame(rows)
    df_sorted = df.sort_values("objective", ascending=not maximize)
    best = df_sorted.iloc[0].to_dict()
    return {"best_cfg": {k: best[k] for k in best if k != "objective"},
            "best_value": float(best["objective"]),
            "trace": df}


# =============================================================================
# 2. Bayesian optimisation
# =============================================================================
def bayesian_optimize(objective: Callable[[Dict], float],
                      n_calls: int = 60, n_initial: int = 20,
                      seed: int = 0, maximize: bool = True) -> Dict:
    try:
        from skopt import gp_minimize
        from skopt.space import Real, Integer
    except ImportError:
        print("scikit-optimize not installed — falling back to random_search")
        return random_search(objective, n_trials=n_calls, seed=seed,
                             maximize=maximize)
    n_initial = max(1, min(n_initial, max(1, n_calls - 1)))
    if n_calls < n_initial + 1:
        n_calls = n_initial + 1
    specs = default_parameter_space()
    dims, names = [], []
    for s in specs:
        names.append(s.name)
        dims.append(Integer(int(s.low), int(s.high), name=s.name)
                    if s.is_int else Real(s.low, s.high, name=s.name))
    sign = -1.0 if maximize else 1.0

    def _obj(values):
        cfg = dict(zip(names, values))
        if cfg.get("chord_skip", 1) >= cfg.get("N", 8):
            cfg["chord_skip"] = max(1, cfg["N"] - 1)
        try:
            return sign * float(objective(cfg))
        except Exception:
            return 1e6

    res = gp_minimize(_obj, dimensions=dims, n_calls=n_calls,
                      n_initial_points=n_initial,
                      random_state=seed, acq_func="EI")
    best_cfg = dict(zip(names, res.x))
    trace = pd.DataFrame(res.x_iters, columns=names)
    trace["objective"] = sign * np.array(res.func_vals)
    return {"best_cfg": best_cfg,
            "best_value": sign * float(res.fun),
            "trace": trace}


# =============================================================================
# 3. Standard physics objectives (saves you writing boilerplate)
# =============================================================================
def make_objective(target: str):
    """Return objective(cfg_dict) -> float for one of: opl_m, throughput,
    quality, bounces."""
    def _obj(cfg_dict: Dict) -> float:
        cfg = TMPCConfig(**{k: v for k, v in cfg_dict.items()
                            if k in TMPCConfig.__dataclass_fields__})
        cfg.n_passes = 8 * cfg.N
        res = simulate_tmpc(cfg)
        d = res.as_dict()
        if target == "quality":
            return (d["opl_m"] * d["throughput"] * d["volume_utilisation"]
                    * (1.0 - 0.5 * max(0.0, d["stability_g"] - 0.95)))
        return float(d[target])
    return _obj
