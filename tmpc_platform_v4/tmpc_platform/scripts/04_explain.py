"""Stage 4: SHAP + Sobol explainability for trained surrogates."""
import argparse, os, sys, glob, joblib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.explainability import compute_shap, sobol_indices
from tmpc_platform.ml_models.training import FEATURES, TARGETS
from tmpc_platform.visualization import plot_feature_importance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default="results/dataset.csv")
    ap.add_argument("--models", type=str, default="results/models")
    ap.add_argument("--out", type=str, default="results/explain")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    df = pd.read_csv(args.data)

    for tgt in TARGETS:
        # Always use RandomForest for SHAP — TreeExplainer is fast and accurate.
        # Other models (GP, NeuralNet) would force slow KernelExplainer.
        path = os.path.join(args.models, f"RandomForest__{tgt}.joblib")
        if not os.path.exists(path):
            continue
        model = joblib.load(path)
        print(f"[04] SHAP for target={tgt}")
        s = compute_shap(model, df, tgt, out_dir=args.out)
        if s.get("mean_abs_shap"):
            plot_feature_importance(
                s["mean_abs_shap"],
                os.path.join(args.out, f"importance__{tgt}.png"),
                title=f"Feature importance for {tgt} ({s['method']})",
            )
        # Sobol indices on the surrogate
        print(f"[04] Sobol indices for target={tgt}")
        predictor = lambda X: model.predict(X)
        so = sobol_indices(predictor, n_samples=512, out_dir=args.out, target_name=tgt)
        pd.DataFrame(so).to_json(os.path.join(args.out, f"sobol__{tgt}.json"))


if __name__ == "__main__":
    main()
