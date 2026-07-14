"""Montage of COMSOL ray-trajectory renders (auto-cropped) for the paper."""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
JD = os.path.join(_HERE, "designs", "comsol", "java")
FIG = os.path.join(_HERE, "designs", "figures")

PANELS = [
    ("D190_19m_2inch_comsol.png", "two-inch 19.0 m\n8 mirrors, 152 chords"),
    ("D190_26m_trigas_comsol.png", "tri-gas 25.7 m\n16 mirrors, 176 chords"),
    ("D190_29m_max_comsol.png", "ceiling 29.0 m\n12 mirrors, 204 chords"),
]


def crop_white(img: np.ndarray, pad: int = 8) -> np.ndarray:
    if img.shape[2] == 4:
        img = img[:, :, :3]
    nonwhite = (img[:, :, :3] < 245).any(axis=2)
    ys, xs = np.nonzero(nonwhite)
    if len(ys) == 0:
        return img
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, img.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, img.shape[1])
    return img[y0:y1, x0:x1]


def main() -> int:
    fig, axes = plt.subplots(1, len(PANELS), figsize=(11.5, 4.3))
    for ax, (fn, cap) in zip(axes, PANELS):
        img = plt.imread(os.path.join(JD, fn))
        if img.dtype != np.uint8:
            img = (img * 255).astype(np.uint8) if img.max() <= 1 else \
                img.astype(np.uint8)
        ax.imshow(crop_white(img))
        ax.set_title(cap, fontsize=9.5)
        ax.axis("off")
    fig.suptitle("COMSOL Ray-Optics traces (top view): the chord-skip pattern "
                 "fills the disc and clears the central coupling hole",
                 fontsize=11, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = os.path.join(FIG, "comsol_raytrace_montage.png")
    fig.savefig(out, dpi=175)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
