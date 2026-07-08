"""Figure: input-drift capture envelopes vs drone-mount demand.

Two panels from designs/capture_envelope.csv: position capture and angle
capture per design (log scale), with the summed alignment-residual +
drone-drift demand lines for the aluminium-flexure and hybrid
plastic-body architectures.

Run from _CURRENT/:
    ../.venv/Scripts/python.exe drone_20m/capture_envelope_fig.py
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
import pandas as pd                                                # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

LABELS = {
    "D190_26m_trigas": "tri-gas\n25.7 m",
    "D160_27m": "27 m\nØ160",
    "D180_24m_H2": "H2-opt.\n23.8 m",
    "D180_15m_sparse": "sparse\n15.3 m",
    "D130_9m_halfinch": "mini ½″\n9.1 m",
    "D190_19m_2inch": "two-inch\n19.0 m",
    "D190_29m_max": "ceiling\n29.0 m",
    "D150_14cm_flight": "compact\n20.7 m",
    "D180_22m": "std-tier\n22.3 m",
}
DEMANDS = {"Al flexure demand": (0.07, 0.20, "#1f77b4"),
           "hybrid plastic demand": (0.17, 0.55, "#d62728")}


def main() -> int:
    df = pd.read_csv(os.path.join(_HERE, "designs", "capture_envelope.csv"))
    df = df[df["design"].isin(LABELS)].reset_index(drop=True)
    x = range(len(df))
    labs = [LABELS[d] for d in df["design"]]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.2))
    a1.bar(x, df["P_cap_mm"], color="#4a90b8", width=0.62)
    for name, (p, _t, c) in DEMANDS.items():
        a1.axhline(p, color=c, lw=1.6, ls="--")
        a1.text(len(df) - 0.4, p * 1.08, name, color=c, fontsize=8,
                ha="right")
    a1.set_ylabel("position capture  P$_{cap}$  [mm]")
    a1.set_title("launch-position drift capture", fontsize=10)

    a2.bar(x, df["Th_cap_mrad"], color="#7a5aa8", width=0.62)
    for name, (_p, t, c) in DEMANDS.items():
        a2.axhline(t, color=c, lw=1.6, ls="--")
        a2.text(len(df) - 0.4, t * 1.15, name, color=c, fontsize=8,
                ha="right")
    a2.set_yscale("log")
    a2.set_ylabel("angle capture  Θ$_{cap}$  [mrad]")
    a2.set_title("launch-angle drift capture (log scale)", fontsize=10)

    for ax in (a1, a2):
        ax.set_xticks(list(x))
        ax.set_xticklabels(labs, fontsize=7.5)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    fig.suptitle("Input-drift capture envelope per design vs summed "
                 "alignment-residual + drone operational-drift demand",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = os.path.join(_HERE, "designs", "figures", "capture_envelope.png")
    fig.savefig(out, dpi=170)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
