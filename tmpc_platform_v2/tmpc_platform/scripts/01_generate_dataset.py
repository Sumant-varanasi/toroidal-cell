"""Stage 1: generate a Sobol-sampled dataset of TMPC configurations."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.dataset_generation import generate_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000, help="number of samples")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--out", type=str, default="results/dataset.csv")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    print(f"[01] Generating dataset: n={args.n}")
    df = generate_dataset(n_samples=args.n, n_workers=args.workers,
                          out_path=args.out, seed=args.seed)
    print(f"[01] Dataset shape: {df.shape}")
    print(df.describe().T[["mean", "std", "min", "max"]].round(3))


if __name__ == "__main__":
    main()
