"""Monte-Carlo robustness for mixed-SKU designs.

The platform's monte_carlo() samples its own per-mirror perturbations,
so it cannot carry the deterministic alternating-ROC baseline. This
harness composes baseline dR (the SKU mix) with random flight-grade
errors per trial and applies the robust_menu criteria.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/mixed_mc.py
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from mixed_sku_explore import HOLE_R, make_cfg                    # noqa: E402
from mixed_sku_pass2 import sep_and_clear                         # noqa: E402
from tmpc_platform_v5 import simulate_tmpc                        # noqa: E402
from tmpc_platform_v5.physics import (MirrorPerturbation,          # noqa: E402
                                      mirror_footprints)

# flight-grade sigmas (paper section 6.1)
SIG = dict(tilt=0.1e-3, lat=0.020, ax=0.030, dR=0.5, rring=0.030,
           lpos=0.020, ltilt=0.1e-3)
N_TRIALS = 100
SEED = 11


def trial(args):
    row, t = args
    rng = np.random.default_rng(SEED + t)
    N, s = int(row["N"]), int(row["s"])
    ra, rb = float(row["roc_a"]), float(row["roc_b"])
    n_exit = int(row["n_exit"])
    cfg, base = make_cfg(N, s, ra, rb,
                         float(row["r_ring"]) + rng.normal(0, SIG["rring"]),
                         float(row["ang_t"]) + rng.normal(0, SIG["ltilt"]),
                         float(row["ang_s"]) + rng.normal(0, SIG["ltilt"]),
                         float(row["off_z"]) + rng.normal(0, SIG["lpos"]),
                         float(row["w0"]), float(row["waist_frac"]),
                         n_exit)
    perts = [MirrorPerturbation(
        d_tan=rng.normal(0, SIG["lat"]),
        d_sag=rng.normal(0, SIG["lat"]),
        d_ax=rng.normal(0, SIG["ax"]),
        tilt_tan=rng.normal(0, SIG["tilt"]),
        tilt_sag=rng.normal(0, SIG["tilt"]),
        dR_t=base[q].dR_t + rng.normal(0, SIG["dR"]),
        dR_s=base[q].dR_s + rng.normal(0, SIG["dR"]))
        for q, _ in enumerate(base)]
    res = simulate_tmpc(cfg, perturbations=perts)
    n = res.bounces
    complete = n >= n_exit
    if not complete:
        return dict(complete=False, sep=np.nan, clear=np.nan,
                    exit_miss=np.nan, w_hole=np.nan)
    sep, clear, _ = sep_and_clear(cfg, perts, n_exit)
    # exit miss: distance of the n_exit-visit from the hole centre
    hits = res.spot_pattern[:n]
    mseq = res.mirror_sequence[:n]
    foot = mirror_footprints(hits, mseq, cfg)
    w_eff = np.asarray(np.maximum(res.w_tangential,
                                  res.w_sagittal))[: n + 1]
    hole = np.array([0.0, cfg.input_offset_z])
    miss = np.nan
    wj = np.nan
    for u, v, order in foot.get(0, np.empty((0, 3))):
        if abs(int(order) - (n_exit - 1)) <= 1 and int(order) > 0:
            miss = float(np.hypot(u - hole[0], v - hole[1]))
            wj = float(w_eff[min(int(order), len(w_eff) - 1)])
    return dict(complete=True, sep=sep, clear=clear, exit_miss=miss,
                w_hole=wj)


def mc_design(row, w_pair):
    tasks = [(row, t) for t in range(N_TRIALS)]
    with ProcessPoolExecutor(max_workers=8) as ex:
        rs = list(ex.map(trial, tasks))
    d = pd.DataFrame(rs)
    out = dict(
        complete_frac=float(d["complete"].mean()),
        sep_p05=float(np.nanpercentile(d["sep"], 5)),
        clear_p05=float(np.nanpercentile(d["clear"], 5)),
        exit_p95=float(np.nanpercentile(d["exit_miss"] + d["w_hole"], 95)),
    )
    out["sep_ok"] = out["sep_p05"] >= -w_pair * 0.0  # sep is margin-based
    out["sep_ok"] = out["sep_p05"] > 0.0
    out["hole_ok"] = out["clear_p05"] > 0.0
    out["exit_ok"] = out["exit_p95"] < HOLE_R
    out["robust"] = (out["complete_frac"] >= 0.99 and out["sep_ok"]
                     and out["hole_ok"] and out["exit_ok"])
    return out


def main() -> int:
    src = pd.read_csv(os.path.join(_HERE, "designs",
                                   "mixed_sku_native_winners.csv"))
    picks = src[(src["feasible"] == True)                     # noqa: E712
                | ((src["exit_miss"] < 0.06)
                   & (src["sep_margin"] > 0.2))].copy()
    print(f"{len(picks)} mixed designs -> flight-grade MC x{N_TRIALS}")
    rows = []
    for _, r in picks.iterrows():
        # native CSV lacks launch cols? ensure presence
        for c in ("ang_t", "ang_s", "off_z", "w0", "waist_frac"):
            if c not in r or pd.isna(r[c]):
                print("  missing launch params; re-derive needed"); break
        m = mc_design(r.to_dict(), w_pair=0.0)
        rows.append({**r.to_dict(), **m})
        print(f"  N={int(r['N'])} {r['roc_a']:.0f}/{r['roc_b']:.0f} "
              f"k={int(r['k'])} opl={r['opl_m']:.1f} m "
              f"complete={m['complete_frac']*100:.0f}% "
              f"sep_p05={m['sep_p05']:.2f} clear_p05={m['clear_p05']:.2f} "
              f"exit_p95={m['exit_p95']:.2f} robust={m['robust']}",
              flush=True)
    pd.DataFrame(rows).to_csv(
        os.path.join(_HERE, "designs", "mixed_mc.csv"), index=False)
    print("wrote designs/mixed_mc.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
