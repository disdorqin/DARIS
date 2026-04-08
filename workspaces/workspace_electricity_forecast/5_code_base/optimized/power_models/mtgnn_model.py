from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from power_models.common import DatasetBundle, compute_metrics, make_dataset_bundle, physics_postprocess


class MTGNNLite(nn.Module):
    def __init__(self, n_features: int, adj: np.ndarray, hidden_dim: int = 64):
        super().__init__()
        self.register_buffer("adj", torch.from_numpy(adj.astype(np.float32)))
        self.in_proj = nn.Linear(n_features * 2, hidden_dim)
        self.temporal = nn.Sequential(
            nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, S, N]
        graph_ctx = torch.einsum("ij,bsj->bsi", self.adj, x)
        h = torch.cat([x, graph_ctx], dim=-1)
        h = self.in_proj(h)
        h = h.transpose(1, 2)
        h = self.temporal(h)
        h = h[:, :, -1]
        out = self.head(h).squeeze(-1)
        return out


@dataclass
class TrainConfig:
    epochs: int
    batch_size: int
    lr: float
    lambda_phy: float


def _build_adj(train_x: np.ndarray) -> np.ndarray:
    # train_x: [N, S, F]
    flat = train_x.reshape(-1, train_x.shape[-1])
    corr = np.corrcoef(flat.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    corr = np.abs(corr)
    np.fill_diagonal(corr, 1.0)
    row_sum = corr.sum(axis=1, keepdims=True) + 1e-6
    return corr / row_sum


def _train_model(data: DatasetBundle, cfg: TrainConfig, optimized: bool) -> np.ndarray:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    adj = _build_adj(data.x_train)
    model = MTGNNLite(n_features=data.n_features, adj=adj, hidden_dim=88 if optimized else 64).to(device)

    train_ds = TensorDataset(torch.from_numpy(data.x_train), torch.from_numpy(data.y_train), torch.from_numpy(data.last_train))
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)

    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    criterion = nn.MSELoss()

    ramp = float(np.quantile(np.abs(np.diff(data.y_train)), 0.99))

    model.train()
    for _ in range(cfg.epochs):
        for xb, yb, lastb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            lastb = lastb.to(device)

            pred = model(xb)
            loss = criterion(pred, yb)
            if optimized:
                phy = torch.relu(torch.abs(pred - lastb) - ramp).mean()
                loss = loss + cfg.lambda_phy * phy

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        test_pred = model(torch.from_numpy(data.x_test).to(device)).cpu().numpy()

    if optimized:
        test_pred = physics_postprocess(test_pred, data.last_test, data.y_train)

    return test_pred


def train_eval_mtgnn(df, optimized: bool) -> Dict[str, float]:
    seq_len = 120 if optimized else 72
    data: DatasetBundle = make_dataset_bundle(df=df, seq_len=seq_len, horizon=1, optimized=optimized, feature_profile="graph")

    cfg = TrainConfig(
        epochs=10 if optimized else 6,
        batch_size=128,
        lr=8e-4 if optimized else 1e-3,
        lambda_phy=0.1,
    )

    pred = _train_model(data, cfg, optimized)
    return compute_metrics(data.y_test, pred)
