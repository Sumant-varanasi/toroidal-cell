"""Single- and multi-objective evolutionary optimisation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Callable, List
from ..dataset_generation.sampler import parameter_space

try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.algorithms.soo.nonconvex.ga import GA
    from pymoo.optimize import minimize
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import FloatRandomSampling
    _HAS_PYMOO = True
except Exception:
    _HAS_PYMOO = False


def _bounds():
    specs = parameter_space()
    xl = np.array([s.low for s in specs], dtype=float)
    xu = np.array([s.high for s in specs], dtype=float)
    names = [s.name for s in specs]
    int_mask = np.array([s.is_int for s in specs])
    return xl, xu, names, int_mask


def _decode(x, names, int_mask) -> Dict:
    cfg = {}
    for v, n, m in zip(x, names, int_mask):
        cfg[n] = int(round(v)) if m else float(v)
    if cfg.get("chord_skip", 1) >= cfg.get("N", 8):
        cfg["chord_skip"] = max(1, cfg["N"] - 1)
    return cfg


def ga_optimize(objective: Callable[[Dict], float],
                pop_size: int = 40, n_gen: int = 30,
                maximize: bool = True, seed: int = 0) -> Dict:
    if not _HAS_PYMOO:
        return {"ok": False, "reason": "pymoo not installed"}
    xl, xu, names, int_mask = _bounds()
    sign = -1.0 if maximize else 1.0

    class P(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=len(xl), n_obj=1, xl=xl, xu=xu)
        def _evaluate(self, x, out, *args, **kw):
            cfg = _decode(x, names, int_mask)
            try:
                out["F"] = sign * float(objective(cfg))
            except Exception:
                out["F"] = 1e6

    algo = GA(pop_size=pop_size, sampling=FloatRandomSampling(),
              crossover=SBX(eta=15, prob=0.9), mutation=PM(eta=20))
    res = minimize(P(), algo, ("n_gen", n_gen), seed=seed, verbose=False)
    best_cfg = _decode(res.X, names, int_mask)
    return {"ok": True, "best_cfg": best_cfg,
            "best_value": sign * float(res.F[0])}


def nsga2_optimize(objectives: List[Callable[[Dict], float]],
                   pop_size: int = 60, n_gen: int = 40,
                   maximize_flags: List[bool] = None,
                   seed: int = 0) -> Dict:
    """Multi-objective optimisation. Provide list of callables; each returns
    a scalar to minimise (use maximize_flags to flip signs for maximisation).
    """
    if not _HAS_PYMOO:
        return {"ok": False, "reason": "pymoo not installed"}
    xl, xu, names, int_mask = _bounds()
    n_obj = len(objectives)
    signs = np.array([-1.0 if (maximize_flags or [True]*n_obj)[i] else 1.0
                      for i in range(n_obj)])

    class P(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=len(xl), n_obj=n_obj, xl=xl, xu=xu)
        def _evaluate(self, x, out, *args, **kw):
            cfg = _decode(x, names, int_mask)
            try:
                vals = [float(o(cfg)) for o in objectives]
            except Exception:
                vals = [1e6] * n_obj
            out["F"] = signs * np.array(vals)

    algo = NSGA2(pop_size=pop_size, sampling=FloatRandomSampling(),
                 crossover=SBX(eta=15, prob=0.9), mutation=PM(eta=20))
    res = minimize(P(), algo, ("n_gen", n_gen), seed=seed, verbose=False)
    pareto_X = np.atleast_2d(res.X)
    pareto_F = signs * np.atleast_2d(res.F)  # back to original directions
    cfgs = [_decode(x, names, int_mask) for x in pareto_X]
    df = pd.DataFrame(cfgs)
    for i in range(n_obj):
        df[f"obj_{i}"] = pareto_F[:, i]
    return {"ok": True, "pareto": df}
