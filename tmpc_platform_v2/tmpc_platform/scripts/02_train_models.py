"""Stage 2: train all surrogate models + PINN + ensemble."""
import argparse, os, sys, joblib
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.ml_models import (train_all_surrogates, TARGETS, train_pinn)
from tmpc_platform.ml_models.ensemble import build_ensemble_for_target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default="results/dataset.csv")
    ap.add_argument("--out", type=str, default="results/models")
    ap.add_argument("--targets", nargs="+", default=TARGETS)
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    print(f"[02] Loaded dataset: {df.shape}")
    print(f"[02] Training surrogates for targets: {args.targets}")
    out = train_all_surrogates(df, targets=args.targets, out_dir=args.out)
    metrics = out["metrics"]
    print("\n[02] Surrogate metrics:")
    print(metrics.to_string(index=False))

    print("\n[02] Training PINN (PyTorch if available)...")
    for tgt in args.targets:
        r = train_pinn(df, target=tgt, out_dir=args.out)
        print(f"  PINN[{tgt}]: {r.get('trained', False)}")

    print("\n[02] Building stacking ensembles...")
    for tgt in args.targets:
        r = build_ensemble_for_target(df, tgt, model_dir=args.out, out_dir=args.out)
        print(f"  Ensemble[{tgt}]: {r}")


if __name__ == "__main__":
    main()
