"""Parallel Sobol dataset generator.

Each row is one fully-simulated TMPC configuration with features + targets
suitable for ML surrogates or active learning.
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .physics import TMPCConfig, simulate_tmpc
from .samplers import (sobol_sample, default_parameter_space,
                       thorlabs_sobol_sample)


def _eval_one(cfg_dict: Dict) -> Optional[Dict]:
    try:
        if cfg_dict["chord_skip"] >= cfg_dict["N"]:
            cfg_dict = dict(cfg_dict)
            cfg_dict["chord_skip"] = max(1, cfg_dict["N"] - 1)
        sku = cfg_dict.get("thorlabs_sku", "")
        keep = {k: v for k, v in cfg_dict.items()
                if k in TMPCConfig.__dataclass_fields__}
        cfg = TMPCConfig(**keep)
        cfg.n_passes = 8 * cfg.N
        res = simulate_tmpc(cfg)
        row = res.as_dict()
        if sku:
            row["thorlabs_sku"] = sku
        row["aoi_std"] = float(res.aoi.std()) if len(res.aoi) else 0.0
        row["quality"] = (
            row["opl_m"] * row["throughput"] * row["volume_utilisation"]
            * (1.0 - 0.5 * max(0.0, row["stability_g"] - 0.95))
        )
        return row
    except Exception:
        return None


def generate_dataset(n_samples: int = 1000, n_workers: Optional[int] = None,
                     out_path: str = "results/dataset.csv",
                     seed: int = 0, thorlabs: bool = False,
                     thorlabs_family: str = "half_inch",
                     progress: bool = True) -> pd.DataFrame:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if thorlabs:
        configs = thorlabs_sobol_sample(n_samples, seed=seed,
                                        family=thorlabs_family)
    else:
        configs = sobol_sample(n_samples, default_parameter_space(), seed=seed)
    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)

    rows: List[dict] = []
    t0 = time.time()
    if n_workers == 1:
        for i, c in enumerate(configs):
            r = _eval_one(c)
            if r is not None:
                rows.append(r)
            if progress and (i + 1) % max(1, n_samples // 20) == 0:
                print(f"  [{i+1}/{n_samples}] elapsed {time.time()-t0:.1f}s")
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futs = {ex.submit(_eval_one, c): i for i, c in enumerate(configs)}
            done = 0
            for f in as_completed(futs):
                r = f.result()
                done += 1
                if r is not None:
                    rows.append(r)
                if progress and done % max(1, n_samples // 20) == 0:
                    print(f"  [{done}/{n_samples}] elapsed {time.time()-t0:.1f}s")

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    if progress:
        print(f"Saved {len(df)} valid rows -> {out_path} "
              f"({time.time()-t0:.1f}s total)")
    return df
