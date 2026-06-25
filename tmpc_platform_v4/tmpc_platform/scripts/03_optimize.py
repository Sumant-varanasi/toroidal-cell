"""Stage 3: optimise designs using surrogate-accelerated objectives."""
import argparse, os, sys, joblib
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tmpc_platform.optimization import bayesian_optimize, nsga2_optimize
from tmpc_platform.ml_models.training import FEATURES
from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.losses import compute_losses
from tmpc_platform.physics_engine.thorlabs_catalog import (
    snap_to_catalog, get_family, REFLECTIVITY_1654NM,
)


def _ml_predict(model, cfg_dict):
    X = np.array([[cfg_dict.get(f, 0.0) for f in FEATURES]])
    return float(model.predict(X)[0])


def _apply_thorlabs(cfg_dict: dict, family: str = "half_inch") -> dict:
    """Snap any sampled cfg to Thorlabs catalogue values."""
    cfg = dict(cfg_dict)
    roc, sku = snap_to_catalog(cfg.get("R_t", 100.0), family=family)
    fam = get_family(family)
    cfg["R_t"] = roc
    cfg["R_s"] = roc
    cfg["mirror_aperture"] = fam["clear_aperture_radius_mm"]
    cfg["reflectivity"]    = REFLECTIVITY_1654NM
    cfg["thorlabs_sku"]    = sku
    cfg["thorlabs_family"] = family
    return cfg


def _simulator_objective(cfg_dict, key="quality",
                          thorlabs=False, family="half_inch"):
    """Ground-truth objective from the full simulator."""
    if thorlabs:
        cfg_dict = _apply_thorlabs(cfg_dict, family=family)
    if cfg_dict.get("chord_skip", 1) >= cfg_dict.get("N", 8):
        cfg_dict["chord_skip"] = max(1, cfg_dict["N"] - 1)
    cfg = TMPCConfig(**{k: v for k, v in cfg_dict.items()
                        if k in TMPCConfig.__dataclass_fields__})
    cfg.n_passes = 8 * cfg.N
    r = simulate_tmpc(cfg)
    loss = compute_losses(r.bounces, cfg.reflectivity, r.w_max,
                          cfg.mirror_aperture, 2*cfg.w0, clipped=r.clipped)
    opl_m = r.opl * 1e-3
    quality = opl_m * loss.throughput * r.volume_utilisation
    table = {"opl_m": opl_m, "throughput": loss.throughput,
             "quality": quality, "stability": r.stability_g,
             "clipping": -loss.clipping_loss}
    return table[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default="results/dataset.csv")
    ap.add_argument("--models", type=str, default="results/models")
    ap.add_argument("--out", type=str, default="results/optim")
    ap.add_argument("--bo-calls", type=int, default=40)
    ap.add_argument("--ga-gen", type=int, default=25)
    ap.add_argument("--use-surrogate", action="store_true",
                    help="optimise the ML surrogate instead of the full simulator")
    ap.add_argument("--thorlabs", action="store_true",
                    help="constrain to Thorlabs catalogue mirrors")
    ap.add_argument("--family", choices=["half_inch", "one_inch"],
                    default="half_inch",
                    help="Thorlabs mirror family (only with --thorlabs)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    if args.thorlabs:
        fam = get_family(args.family)
        print(f"[03] THORLABS MODE: family={args.family}, "
              f"aperture={fam['clear_aperture_radius_mm']} mm, R=0.97")

    # Build objective
    if args.use_surrogate:
        path = os.path.join(args.models, "Ensemble__quality.joblib")
        if not os.path.exists(path):
            path = os.path.join(args.models, "RandomForest__quality.joblib")
        model = joblib.load(path)
        print(f"[03] Using surrogate for objective: {path}")
        if args.thorlabs:
            obj_quality = lambda c: _ml_predict(model,
                                                _apply_thorlabs(c, args.family))
        else:
            obj_quality = lambda c: _ml_predict(model, c)
    else:
        print("[03] Using full simulator for objective")
        obj_quality = lambda c: _simulator_objective(
            c, "quality", thorlabs=args.thorlabs, family=args.family)

    # Bayesian optimisation
    print("[03] Running Bayesian optimisation...")
    bo = bayesian_optimize(obj_quality, n_calls=args.bo_calls, maximize=True)
    if args.thorlabs:
        bo["best_cfg"] = _apply_thorlabs(bo["best_cfg"], args.family)
    print(f"[03] BO best value: {bo['best_value']:.4f}")
    print(f"[03] BO best cfg:   {bo['best_cfg']}")
    bo["trace"].to_csv(os.path.join(args.out, "bo_trace.csv"), index=False)
    pd.DataFrame([{**bo["best_cfg"], "value": bo["best_value"]}]).to_csv(
        os.path.join(args.out, "bo_best.csv"), index=False)

    # Multi-objective NSGA-II
    print("[03] Running NSGA-II multi-objective optimisation...")
    obj_opl = lambda c: _simulator_objective(c, "opl_m",
                                              thorlabs=args.thorlabs, family=args.family)
    obj_thr = lambda c: _simulator_objective(c, "throughput",
                                              thorlabs=args.thorlabs, family=args.family)
    obj_clp = lambda c: _simulator_objective(c, "clipping",
                                              thorlabs=args.thorlabs, family=args.family)
    nsga = nsga2_optimize(
        [obj_opl, obj_thr, obj_clp],
        pop_size=40, n_gen=args.ga_gen,
        maximize_flags=[True, True, True])
    if nsga.get("ok"):
        pareto = nsga["pareto"]
        if args.thorlabs:
            snapped = pareto.apply(
                lambda r: _apply_thorlabs(r.to_dict(), args.family), axis=1)
            for k in ["R_t", "R_s", "mirror_aperture", "reflectivity",
                      "thorlabs_sku", "thorlabs_family"]:
                pareto[k] = [s[k] for s in snapped]
        pareto.to_csv(os.path.join(args.out, "pareto.csv"), index=False)
        print(f"[03] Pareto front size: {len(pareto)}")
    else:
        print(f"[03] NSGA-II skipped: {nsga}")


if __name__ == "__main__":
    main()
