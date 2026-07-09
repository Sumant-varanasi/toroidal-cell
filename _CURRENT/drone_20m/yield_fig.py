"""Figure: 5000-trial drone-yield as trial-failure-rate (log), per architecture.

Plots (100 - yield) on a log axis so the >99.9 % product criterion
(= 0.1 % failure) is a meaningful line: designs that clear it sit below
the dashed line. Two bars per design (aluminium flexure vs hybrid
plastic-body). Data: designs/mc5000_drone_yield.csv.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/yield_fig.py
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402
import pandas as pd                                                # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

ORDER = ["D190_26m_trigas", "D180_15m_sparse", "D190_19m_2inch",
         "D180_24m_H2", "D130_9m_halfinch", "D150_14cm_flight",
         "D160_27m", "D190_29m_max", "D180_22m"]
LABELS = {
    "D190_26m_trigas": "tri-gas\n25.7 m", "D180_15m_sparse": "sparse\n15.3 m",
    "D190_19m_2inch": "two-inch\n19.0 m", "D180_24m_H2": "H2-opt.\n23.8 m",
    "D130_9m_halfinch": "mini ½″\n9.1 m", "D150_14cm_flight": "compact\n20.7 m",
    "D160_27m": "27 m\nØ160", "D190_29m_max": "ceiling\n29.0 m",
    "D180_22m": "std-tier\n22.3 m",
}
FLOOR = 0.02   # % — display floor for perfect (100.000 %) bars


def main() -> int:
    df = pd.read_csv(os.path.join(_HERE, "designs", "mc5000_drone_yield.csv"))
    piv = df.pivot(index="design", columns="arch", values="yield_pct")
    piv = piv.reindex(ORDER)
    fail_al = np.maximum(100.0 - piv["al_flexure"].to_numpy(), FLOOR)
    fail_hy = np.maximum(100.0 - piv["hybrid"].to_numpy(), FLOOR)

    x = np.arange(len(ORDER))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.2, 4.6))
    b1 = ax.bar(x - w / 2, fail_al, w, label="aluminium flexure mount",
                color="#4a90b8")
    b2 = ax.bar(x + w / 2, fail_hy, w, label="hybrid plastic + Al cartridge",
                color="#c56b8f")
    ax.axhline(0.1, color="#c0392b", lw=1.8, ls="--")
    ax.text(len(ORDER) - 0.5, 0.115,
            "drone product criterion  (99.9 % yield)",
            color="#c0392b", fontsize=9, ha="right", va="bottom")
    ax.set_yscale("log")
    ax.set_ylim(FLOOR * 0.8, 80)
    ax.set_ylabel("trial failure rate  (100 − yield) [%]   — lower is better")
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[d] for d in ORDER], fontsize=8)
    ax.grid(axis="y", which="both", alpha=0.22)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    # mark the three that clear the line
    for xi, fa in zip(x, fail_al):
        if fa <= FLOOR * 1.01:
            ax.text(xi - w / 2, FLOOR * 0.9, "✓", color="#1e7d34",
                    fontsize=13, ha="center", va="top", weight="bold")
    ax.set_title("5000-trial composed-drift Monte-Carlo drone yield "
                 "(alignment residual + operational drift, per mount)",
                 fontsize=11)
    fig.tight_layout()
    out = os.path.join(_HERE, "designs", "figures", "drone_yield_mc5000.png")
    fig.savefig(out, dpi=170)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
