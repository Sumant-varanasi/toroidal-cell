"""Bayesian optimization using scikit-optimize."""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Callable
from ..dataset_generation.sampler import parameter_space


def bayesian_optimize(objective: Callable[[Dict], float],
                      n_calls: int = 60,
                      n_initial: int = 20,
                      maximize: bool = True,
                      seed: int = 0) -> Dict:
    """Bayesian optimization over the default TMPC parameter space.

    objective(cfg_dict) -> float (e.g. simulator throughput or quality).
    Returns best config and trace.
    """
    from skopt import gp_minimize
    from skopt.space import Real, Integer

    # ensure n_initial <= n_calls
    n_initial = max(5, min(n_initial, n_calls // 2 if n_calls > 10 else n_calls - 1))
    n_initial = max(1, n_initial)
    if n_calls < n_initial + 1:
        n_calls = n_initial + 1

    specs = parameter_space()
    dims = []
    names = []
    for s in specs:
        names.append(s.name)
        if s.is_int:
            dims.append(Integer(int(s.low), int(s.high), name=s.name))
        else:
            dims.append(Real(s.low, s.high, name=s.name))

    sign = -1.0 if maximize else 1.0

    def _obj(values):
        cfg = dict(zip(names, values))
        if cfg.get("chord_skip", 1) >= cfg.get("N", 8):
            cfg["chord_skip"] = max(1, cfg["N"] - 1)
        try:
            return sign * float(objective(cfg))
        except Exception:
            return 1e6

    res = gp_minimize(
        _obj, dimensions=dims,
        n_calls=n_calls, n_initial_points=n_initial,
        random_state=seed, acq_func="EI",
    )
    best_cfg = dict(zip(names, res.x))
    trace = pd.DataFrame(res.x_iters, columns=names)
    trace["objective"] = sign * np.array(res.func_vals)  # undo sign flip
    return {
        "best_cfg": best_cfg,
        "best_value": sign * float(res.fun),  # undo sign flip
        "trace": trace,
    }
