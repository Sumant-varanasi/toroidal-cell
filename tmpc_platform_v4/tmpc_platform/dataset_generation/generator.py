"""Parallel dataset generator."""
from __future__ import annotations
import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from ..physics_engine import TMPCConfig, simulate_tmpc
from ..physics_engine.losses import compute_losses
from .sampler import sobol_sample, parameter_space, thorlabs_sobol_sample


def _evaluate_one(cfg_dict: Dict) -> Optional[Dict]:
    """Evaluate one configuration; return flat dict of features+targets or None."""
    try:
        # chord_skip must be < N
        if cfg_dict["chord_skip"] >= cfg_dict["N"]:
            cfg_dict = dict(cfg_dict)
            cfg_dict["chord_skip"] = max(1, cfg_dict["N"] - 1)
        # extract SKU before filtering to TMPCConfig fields
        sku = cfg_dict.get("thorlabs_sku", "")
        cfg = TMPCConfig(**{k: v for k, v in cfg_dict.items()
                            if k in TMPCConfig.__dataclass_fields__})
        # default n_passes scales with N for fair comparison
        cfg.n_passes = 8 * cfg.N
        res = simulate_tmpc(cfg)
        loss = compute_losses(
            bounces=res.bounces, reflectivity=cfg.reflectivity,
            w_max=res.w_max, aperture=cfg.mirror_aperture,
            beam_diameter_in=2 * cfg.w0, clipped=res.clipped,
        )
        row = res.as_dict()
        if sku:
            row["thorlabs_sku"] = sku
        # store per-bounce AOI as semicolon-separated string (CSV-friendly)
        row["aoi_per_bounce"] = ";".join(f"{a:.3f}" for a in res.aoi)
        row["aoi_std"] = float(res.aoi.std()) if len(res.aoi) else 0.0
        row.update({
            "refl_loss": loss.reflectivity_loss,
            "clip_loss": loss.clipping_loss,
            "ap_loss":   loss.aperture_loss,
            "trunc_loss": loss.truncation_loss,
            "total_loss": loss.total_loss,
            "throughput_full": loss.throughput,
        })
        # composite "design quality" score
        opl_m = row["opl_m"]
        row["quality"] = (
            opl_m * row["throughput_full"] * row["volume_utilisation"]
            * (1.0 - 0.5 * max(0.0, row["stability_g"] - 0.95))
        )
        return row
    except Exception as exc:
        return None


def generate_dataset(n_samples: int = 5000, n_workers: int = None,
                     out_path: str = "results/dataset.csv",
                     seed: int = 0,
                     thorlabs: bool = False,
                     thorlabs_family: str = "half_inch",
                     progress: bool = True) -> pd.DataFrame:
    """Generate a dataset of `n_samples` configurations.

    Uses Sobol sampling over the default parameter space and parallel
    evaluation across CPU cores. Writes a CSV to `out_path`.

    If thorlabs=True, restrict to off-the-shelf catalogue mirrors. The
    `thorlabs_family` argument selects 'half_inch' (CM127-*-M01) or
    'one_inch' (CM254-*-M01).
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if thorlabs:
        configs = thorlabs_sobol_sample(n_samples, seed=seed,
                                        family=thorlabs_family)
        if progress:
            print(f"  [Thorlabs mode, family={thorlabs_family}] "
                  f"{len(configs)} configs")
    else:
        specs = parameter_space()
        configs = sobol_sample(n_samples, specs, seed=seed)

    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)

    rows = []
    t0 = time.time()
    if n_workers == 1:
        for i, c in enumerate(configs):
            r = _evaluate_one(c)
            if r is not None:
                rows.append(r)
            if progress and (i + 1) % max(1, n_samples // 20) == 0:
                print(f"  [{i+1}/{n_samples}] elapsed {time.time()-t0:.1f}s")
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futs = {ex.submit(_evaluate_one, c): i for i, c in enumerate(configs)}
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
