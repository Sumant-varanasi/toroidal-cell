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
    ap.add_argument("--thorlabs", action="store_true",
                    help="restrict to Thorlabs catalogue mirrors")
    ap.add_argument("--family", choices=["half_inch", "one_inch"],
                    default="half_inch",
                    help="Thorlabs mirror family (only with --thorlabs)")
    args = ap.parse_args()
    if args.thorlabs:
        print(f"[01] THORLABS MODE: family={args.family}")
    print(f"[01] Generating dataset: n={args.n}")
    df = generate_dataset(n_samples=args.n, n_workers=args.workers,
                          out_path=args.out, seed=args.seed,
                          thorlabs=args.thorlabs,
                          thorlabs_family=args.family)
    print(f"[01] Dataset shape: {df.shape}")
    print(df.describe().T[["mean", "std", "min", "max"]].round(3))


if __name__ == "__main__":
    main()
