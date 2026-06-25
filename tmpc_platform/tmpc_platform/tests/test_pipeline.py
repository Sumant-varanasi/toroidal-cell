"""Smoke tests for dataset generation and ML training."""
import os, tempfile
import pandas as pd
import numpy as np
from tmpc_platform.dataset_generation import generate_dataset, sobol_sample, parameter_space
from tmpc_platform.ml_models import train_all_surrogates, TARGETS


def test_sampler_shapes():
    specs = parameter_space()
    s = sobol_sample(8, specs)
    assert len(s) == 8
    assert set(s[0].keys()) == {sp.name for sp in specs}


def test_generate_small_dataset(tmp_path):
    out = tmp_path / "ds.csv"
    df = generate_dataset(n_samples=12, n_workers=1, out_path=str(out), progress=False)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in ["N", "R_ring", "opl_m", "throughput_full", "quality"]:
        assert col in df.columns


def test_train_surrogate_smoke(tmp_path):
    df = generate_dataset(n_samples=80, n_workers=1,
                          out_path=str(tmp_path / "ds.csv"), progress=False)
    out_dir = str(tmp_path / "models")
    res = train_all_surrogates(df, targets=["opl_m"], out_dir=out_dir)
    metrics = res["metrics"]
    rf_row = metrics[metrics["model"] == "RandomForest"].iloc[0]
    assert not np.isnan(rf_row["r2"])
