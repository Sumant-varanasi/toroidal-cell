"""Run the FULL pipeline for both Thorlabs mirror families and produce
a side-by-side comparison report.

Usage:
    python -m tmpc_platform.scripts.run_both --n 8192 --bo-calls 60 --ga-gen 40
"""
import argparse, os, sys, subprocess, time, shutil
HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    t0 = time.time()
    res = subprocess.run(cmd, check=False)
    print(f"  ({time.time()-t0:.1f}s, rc={res.returncode})")
    return res.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4096)
    ap.add_argument("--bo-calls", type=int, default=40)
    ap.add_argument("--ga-gen", type=int, default=25)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--use-surrogate", action="store_true")
    ap.add_argument("--skip-half", action="store_true")
    ap.add_argument("--skip-one",  action="store_true")
    args = ap.parse_args()

    py = sys.executable
    families = []
    if not args.skip_half: families.append("half_inch")
    if not args.skip_one:  families.append("one_inch")

    for family in families:
        target_dir = f"results_{family}"
        print(f"\n{'='*70}\n  RUNNING FAMILY: {family.upper()}  -> {target_dir}\n{'='*70}")
        # clear previous results/ folder so the per-stage scripts write fresh
        if os.path.exists("results"):
            shutil.rmtree("results")
        cmd = [py, "-m", "tmpc_platform.scripts.run_all",
               "--n", str(args.n),
               "--bo-calls", str(args.bo_calls),
               "--ga-gen", str(args.ga_gen),
               "--thorlabs", "--family", family]
        if args.workers:
            cmd += ["--workers", str(args.workers)]
        if args.use_surrogate:
            cmd.append("--use-surrogate")
        rc = run(cmd)
        if rc != 0:
            print(f"[run_both] {family} run failed (rc={rc})")
            sys.exit(rc)
        # archive
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.move("results", target_dir)
        print(f"[run_both] saved -> {target_dir}/")
        # per-family summary
        run([py, "-m", "tmpc_platform.scripts.summarise_best",
             "--optim", os.path.join(target_dir, "optim"), "--top", "5"])

    # comparison report
    if len(families) == 2:
        print(f"\n{'='*70}\n  COMPARISON REPORT\n{'='*70}")
        run([py, "-m", "tmpc_platform.scripts.compare_families"])

    print("\nDone.  Open results_half_inch/ and results_one_inch/ for outputs.")
    print("Launch the dashboard with:")
    print("    streamlit run tmpc_platform\\app.py")
    print("(use the 'dataset.csv path' box at the bottom to switch between families)")


if __name__ == "__main__":
    main()
