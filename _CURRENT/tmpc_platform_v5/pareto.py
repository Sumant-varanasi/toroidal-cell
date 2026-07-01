"""Dependency-free multi-objective Pareto analysis for TMPC designs.

This module provides:
    is_dominated     -- pairwise dominance check
    pareto_front     -- O(n^2) non-dominated-set filter
    pareto_search    -- Sobol sample -> simulate -> Pareto front DataFrame
    top_designs      -- slice the Pareto subset, sorted by a key

No third-party optimisation libraries (pymoo, DEAP, torch, etc.) are used.
numpy and pandas are always available in the TMPC environment.
"""
from __future__ import annotations

import sys
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd


# =============================================================================
# 1. Pairwise dominance
# =============================================================================

def is_dominated(a: Sequence[float], b: Sequence[float],
                 maximize: Sequence[bool]) -> bool:
    """Return True if objective-vector *b* dominates *a*.

    *b* dominates *a* when:
      - *b* is at least as good as *a* on every objective, AND
      - *b* is strictly better on at least one objective.

    Parameters
    ----------
    a, b       : sequences of objective values (same length as ``maximize``)
    maximize   : per-objective flag; True = larger is better
    """
    a = list(a)
    b = list(b)
    if len(a) != len(b) or len(a) != len(maximize):
        raise ValueError("a, b, and maximize must all have the same length")

    at_least_as_good = True
    strictly_better = False

    for ai, bi, mx in zip(a, b, maximize):
        if mx:
            # larger is better
            if bi < ai:
                at_least_as_good = False
                break
            if bi > ai:
                strictly_better = True
        else:
            # smaller is better
            if bi > ai:
                at_least_as_good = False
                break
            if bi < ai:
                strictly_better = True

    return at_least_as_good and strictly_better


# =============================================================================
# 2. Pareto front (non-dominated set)
# =============================================================================

def pareto_front(rows: List[Dict], objectives: List[str],
                 maximize: List[bool]) -> List[int]:
    """Return the indices of the non-dominated set via an O(n^2) filter.

    Parameters
    ----------
    rows       : list of dicts, each must contain all keys in ``objectives``
    objectives : list of column names to consider
    maximize   : per-objective direction (same length as ``objectives``)

    Returns
    -------
    List of integer indices (into *rows*) whose designs are not dominated
    by any other design in the list.
    """
    if not rows:
        return []
    if len(objectives) != len(maximize):
        raise ValueError("objectives and maximize must have the same length")

    # Extract the objective matrix  (n, k)
    n = len(rows)
    k = len(objectives)
    obj_mat = np.empty((n, k), dtype=float)
    for i, row in enumerate(rows):
        for j, key in enumerate(objectives):
            obj_mat[i, j] = float(row[key])

    non_dominated: List[int] = []
    for i in range(n):
        dominated = False
        for j in range(n):
            if i == j:
                continue
            # Check whether j dominates i
            if is_dominated(obj_mat[i], obj_mat[j], maximize):
                dominated = True
                break
        if not dominated:
            non_dominated.append(i)

    return non_dominated


# =============================================================================
# 3. Pareto search over the Sobol parameter space
# =============================================================================

def pareto_search(
    n_samples: int = 512,
    seed: int = 0,
    objectives: Tuple[str, ...] = ("opl_m", "throughput"),
    maximize: Tuple[bool, ...] = (True, True),
    minimize_clipping: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    """Sample the TMPC design space and identify the Pareto front.

    Workflow
    --------
    1. Draw ``n_samples`` points from the Sobol-scrambled default parameter
       space (via :func:`tmpc_platform_v5.samplers.sobol_sample`).
    2. Evaluate each design with :func:`tmpc_platform_v5.simulate_tmpc`.
       Failures are silently skipped.
    3. Build a combined objective list from ``objectives``. If
       ``minimize_clipping`` is True, a synthetic ``-clipped`` objective is
       appended (maximising its negation = minimising clipping).
    4. Compute the non-dominated front with :func:`pareto_front`.
    5. Return the full DataFrame with an extra ``on_pareto`` boolean column,
       sorted so Pareto rows come first.

    Parameters
    ----------
    n_samples         : total Sobol samples to draw and evaluate
    seed              : Sobol scrambling seed
    objectives        : tuple of ``as_dict()`` keys to optimise
    maximize          : per-objective direction (same length as *objectives*)
    minimize_clipping : if True, clip-free designs are preferred regardless of
                        clipping's presence in *objectives*
    verbose           : print a progress line every ~10 %% of evaluations

    Returns
    -------
    pandas.DataFrame with all ``as_dict()`` scalar fields plus ``on_pareto``.
    Pareto rows appear first; within each group ordering is by evaluation index.
    """
    from .physics import TMPCConfig, simulate_tmpc
    from .samplers import sobol_sample, default_parameter_space

    objectives = list(objectives)
    maximize = list(maximize)

    # Build the extended objective list for Pareto filtering
    obj_keys = list(objectives)
    obj_max = list(maximize)
    if minimize_clipping and "clipped" not in obj_keys:
        # clipped is 0 or 1 in as_dict(); we want to MINIMISE it
        # -> maximise the negated value (we'll add neg_clipped to the dict)
        obj_keys.append("neg_clipped")
        obj_max.append(True)   # maximise neg_clipped  <=> minimise clipped

    param_configs = sobol_sample(n_samples, specs=None, seed=seed)

    rows: List[Dict] = []
    n_total = len(param_configs)
    report_interval = max(1, n_total // 10)

    for idx, cfg_dict in enumerate(param_configs):
        if verbose and idx % report_interval == 0:
            pct = 100.0 * idx / n_total
            print(f"[pareto_search] {idx}/{n_total} evaluated ({pct:.0f}%%) ...",
                  flush=True)

        # --- guard: chord_skip must be in [1, N-1] ---
        N = int(cfg_dict.get("N", 8))
        cs = int(cfg_dict.get("chord_skip", 1))
        if cs >= N:
            cs = max(1, N - 1)
            cfg_dict["chord_skip"] = cs

        # --- set n_passes = 8*N ---
        cfg_dict["n_passes"] = 8 * N

        try:
            cfg = TMPCConfig(**{k: v for k, v in cfg_dict.items()
                                if k in TMPCConfig.__dataclass_fields__})
            res = simulate_tmpc(cfg)
            row = res.as_dict()
            # Add auxiliary objectives
            row["neg_clipped"] = -float(row.get("clipped", 0))
            rows.append(row)
        except Exception:
            # Skip any design that raises (e.g. invalid geometry)
            continue

    if verbose:
        print(f"[pareto_search] Done. {len(rows)}/{n_total} evaluations succeeded.",
              flush=True)

    if not rows:
        return pd.DataFrame()

    # Identify the Pareto front
    front_indices = pareto_front(rows, obj_keys, obj_max)
    front_set = set(front_indices)

    for i, row in enumerate(rows):
        row["on_pareto"] = (i in front_set)

    df = pd.DataFrame(rows)

    # Sort: Pareto rows first, then by original evaluation order
    df = df.sort_values("on_pareto", ascending=False).reset_index(drop=True)

    # Drop the auxiliary column if we added it internally
    if "neg_clipped" in df.columns and "neg_clipped" not in objectives:
        df = df.drop(columns=["neg_clipped"])

    return df


# =============================================================================
# 4. Top designs
# =============================================================================

def top_designs(df: pd.DataFrame, k: int = 10,
                by: str = "opl_m") -> pd.DataFrame:
    """Return the top-``k`` Pareto-optimal designs, sorted by ``by``.

    Parameters
    ----------
    df  : DataFrame returned by :func:`pareto_search` (must have ``on_pareto``)
    k   : maximum number of rows to return
    by  : column name to sort on (descending; larger = better)

    Returns
    -------
    DataFrame slice of at most ``k`` rows from the Pareto subset.
    """
    if "on_pareto" not in df.columns:
        raise ValueError("DataFrame must have an 'on_pareto' column "
                         "(run pareto_search first).")
    pareto_df = df[df["on_pareto"]].copy()
    ascending = False  # default: bigger is better
    pareto_df = pareto_df.sort_values(by, ascending=ascending)
    return pareto_df.head(k).reset_index(drop=True)
