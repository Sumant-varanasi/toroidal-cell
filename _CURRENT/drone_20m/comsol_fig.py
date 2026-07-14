"""Figure: COMSOL vs exact-tracer agreement per design (RMS/worst, log).

Reads designs/comsol/comsol_agreement.csv and draws the per-design RMS
and worst-bounce deviation on a log axis, with the 10 um reference line
(the Optiland-parity criterion). Writes designs/figures/comsol_agreement.png.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402
import pandas as pd                                                # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

ORDER = ["D190_29m_max", "D190_26m_trigas", "D180_24m_H2", "D160_27m",
         "D150_14cm_flight", "D180_22m", "D190_19m_2inch",
         "D180_15m_sparse", "D130_9m_halfinch"]
LABELS = {
    "D190_29m_max": "ceiling\n29.0 m", "D190_26m_trigas": "tri-gas\n25.7 m",
    "D180_24m_H2": "H2-opt.\n23.8 m", "D160_27m": "27 m\nØ160",
    "D150_14cm_flight": "compact\n20.7 m", "D180_22m": "std-tier\n22.3 m",
    "D190_19m_2inch": "two-inch\n19.0 m", "D180_15m_sparse": "sparse\n15.3 m",
    "D130_9m_halfinch": "mini ½″\n9.1 m",
}


def main() -> int:
    df = pd.read_csv(os.path.join(_HERE, "designs", "comsol",
                                  "comsol_agreement.csv"))
    df = df.set_index("design").reindex(ORDER).reset_index()
    x = np.arange(len(df))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.0, 4.3))
    ax.bar(x - w / 2, df["rms_um"], w, label="RMS deviation",
           color="#3a7ca5")
    ax.bar(x + w / 2, df["worst_um"], w, label="worst-bounce deviation",
           color="#c98a3a")
    ax.axhline(10.0, color="#c0392b", lw=1.6, ls="--")
    ax.text(len(df) - 0.5, 10.6, "10 µm (Optiland-parity criterion)",
            color="#c0392b", fontsize=8.5, ha="right")
    ax.set_yscale("log")
    ax.set_ylim(0.5, 40)
    ax.set_ylabel("chief-ray deviation, COMSOL vs exact tracer [µm]")
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[d] for d in df["design"]], fontsize=8)
    ax.grid(axis="y", which="both", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title("Independent COMSOL Ray-Optics cross-validation: chief-ray "
                 "agreement over the full folded path (98–228 bounces)",
                 fontsize=10.5)
    fig.tight_layout()
    out = os.path.join(_HERE, "designs", "figures", "comsol_agreement.png")
    fig.savefig(out, dpi=170)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
