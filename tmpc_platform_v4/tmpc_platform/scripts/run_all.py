"""Run the full pipeline end-to-end with a single command.

Usage:
    python -m tmpc_platform.scripts.run_all --n 1000
"""
import argparse, os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    t0 = time.time()
    res = subprocess.run(cmd, check=False)
    print(f"  ({time.time()-t0:.1f}s, rc={res.returncode})")
    if res.returncode != 0:
        sys.exit(res.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--bo-calls", type=int, default=30)
    ap.add_argument("--ga-gen", type=int, default=20)
    ap.add_argument("--use-surrogate", action="store_true")
    ap.add_argument("--thorlabs", action="store_true",
                    help="restrict to Thorlabs catalogue")
    ap.add_argument("--family", choices=["half_inch", "one_inch"],
                    default="half_inch")
    args = ap.parse_args()

    py = sys.executable
    s = lambda name: os.path.join(HERE, name)

    cmd1 = [py, s("01_generate_dataset.py"), "--n", str(args.n),
            "--workers", str(args.workers or 1)]
    if args.thorlabs:
        cmd1 += ["--thorlabs", "--family", args.family]
    run(cmd1)
    run([py, s("02_train_models.py")])
    cmd3 = [py, s("03_optimize.py"),
            "--bo-calls", str(args.bo_calls), "--ga-gen", str(args.ga_gen)]
    if args.use_surrogate:
        cmd3.append("--use-surrogate")
    if args.thorlabs:
        cmd3 += ["--thorlabs", "--family", args.family]
    run(cmd3)
    run([py, s("04_explain.py")])
    run([py, s("05_visualize.py")])

    print("\nAll stages complete. See results/ for outputs.")


if __name__ == "__main__":
    main()
