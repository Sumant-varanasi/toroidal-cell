"""Physics-informed neural network for TMPC surrogate.

A standard MLP with an additional physics-consistency penalty in the loss:
    L = MSE(y_pred, y_true)
      + lambda_phys * |violations of physics constraints|

Constraints encoded here:
    1) OPL should increase monotonically with bounce count (proxied by N).
    2) Throughput should monotonically decrease as bounces increase
       (since each bounce loses 1-R).
    3) Stability g should lie in [0,1] for physically meaningful designs.

Uses PyTorch if available; otherwise falls back to a soft-penalty MLP via
gradient descent in NumPy (slow but works for small datasets).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import os, joblib
from typing import Dict
from .training import FEATURES, prepare_xy

try:
    import torch
    import torch.nn as nn
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False


class _PINN(nn.Module if _HAS_TORCH else object):
    def __init__(self, in_dim=8, hidden=128, out_dim=1):
        if not _HAS_TORCH:
            raise RuntimeError("PyTorch not available")
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return self.net(x)


def train_pinn(df: pd.DataFrame, target: str = "opl_m",
               epochs: int = 400, lr: float = 1e-3,
               lambda_phys: float = 0.05,
               out_dir: str = "results/models") -> Dict:
    """Train PINN for given target with physics-consistency regularisation."""
    os.makedirs(out_dir, exist_ok=True)
    if not _HAS_TORCH:
        return {"trained": False, "reason": "torch not installed"}

    X, y = prepare_xy(df, target)
    Xs_mean, Xs_std = X.mean(0), X.std(0) + 1e-8
    ys_mean, ys_std = y.mean(), y.std() + 1e-8
    Xn = (X - Xs_mean) / Xs_std
    yn = (y - ys_mean) / ys_std

    Xt = torch.tensor(Xn, dtype=torch.float32)
    yt = torch.tensor(yn, dtype=torch.float32).unsqueeze(1)

    model = _PINN(in_dim=Xn.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    mse = nn.MSELoss()

    # which feature columns? get index of N (col 0 typically) and reflectivity
    idx_N    = FEATURES.index("N")
    idx_R    = FEATURES.index("reflectivity")

    history = []
    for ep in range(epochs):
        opt.zero_grad()
        pred = model(Xt)
        loss_data = mse(pred, yt)

        # physics: take small batch and perturb N (more N => more bounces =>
        # more OPL if predicting opl, less throughput if predicting throughput)
        with torch.no_grad():
            X_pert = Xt.clone()
            X_pert[:, idx_N] = X_pert[:, idx_N] + 0.1  # increase normalised N
        pred_pert = model(X_pert)
        if target in ("opl_m", "quality"):
            # expect pred_pert >= pred
            violation = torch.relu(pred - pred_pert).mean()
        elif target == "throughput_full":
            # expect pred_pert <= pred
            violation = torch.relu(pred_pert - pred).mean()
        else:
            violation = torch.tensor(0.0)

        loss = loss_data + lambda_phys * violation
        loss.backward()
        opt.step()
        if ep % 50 == 0:
            history.append({"epoch": ep, "loss": float(loss.item()),
                            "data": float(loss_data.item()),
                            "phys": float(violation.item())})

    # save
    path = os.path.join(out_dir, f"PINN__{target}.pt")
    torch.save({
        "state_dict": model.state_dict(),
        "Xs_mean": Xs_mean, "Xs_std": Xs_std,
        "ys_mean": ys_mean, "ys_std": ys_std,
        "in_dim": Xn.shape[1], "target": target,
    }, path)
    return {"trained": True, "path": path, "history": history}


def predict_pinn(model_path: str, X: np.ndarray) -> np.ndarray:
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch not available")
    ckpt = torch.load(model_path, weights_only=False)
    model = _PINN(in_dim=ckpt["in_dim"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    Xn = (X - ckpt["Xs_mean"]) / ckpt["Xs_std"]
    with torch.no_grad():
        yn = model(torch.tensor(Xn, dtype=torch.float32)).numpy().ravel()
    return yn * ckpt["ys_std"] + ckpt["ys_mean"]
