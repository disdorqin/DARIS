from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from power_models.common import DatasetBundle, compute_metrics, make_dataset_bundle, physics_postprocess


class PatchTSTLite(nn.Module):
    def __init__(self, input_dim: int, seq_len: int, hidden_dim: int = 96, patch_size: int = 12, num_layers: int = 2, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.patch_size = patch_size
        self.input_dim = input_dim
        self.seq_len = seq_len
        self.num_patches = int(np.ceil(seq_len / patch_size))

        self.patch_proj = nn.Linear(patch_size * input_dim, hidden_dim)
        self.pos_embedding = nn.Parameter(torch.zeros(1, self.num_patches + 1, hidden_dim))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, feat_dim = x.shape
        remainder = seq_len % self.patch_size
        if remainder:
            pad_len = self.patch_size - remainder
            pad = x[:, -1:, :].repeat(1, pad_len, 1)
            x = torch.cat([x, pad], dim=1)
            seq_len = x.shape[1]

        num_patches = seq_len // self.patch_size
        patches = x.reshape(batch_size, num_patches, self.patch_size * feat_dim)
        h = self.patch_proj(patches)
        h = h + self.pos_embedding[:, :num_patches, :]
        h = self.encoder(h)
        pooled = h.mean(dim=1)
        return self.head(pooled).squeeze(-1)


@dataclass
class TrainConfig:
    epochs: int
    batch_size: int
    lr: float
    lambda_phy: float


def _train_model(data: DatasetBundle, cfg: TrainConfig, optimized: bool) -> np.ndarray:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PatchTSTLite(
        input_dim=data.n_features,
        seq_len=data.x_train.shape[1],
        hidden_dim=96 if optimized else 72,
        patch_size=12,
        num_layers=3 if optimized else 2,
        num_heads=4 if optimized else 2,
        dropout=0.12 if optimized else 0.15,
    ).to(device)

    train_ds = TensorDataset(
        torch.from_numpy(data.x_train),
        torch.from_numpy(data.y_train),
        torch.from_numpy(data.last_train),
    )
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


def train_eval_patchtst(df, optimized: bool) -> Dict[str, float]:
    seq_len = 120 if optimized else 72
    data: DatasetBundle = make_dataset_bundle(df=df, seq_len=seq_len, horizon=1, optimized=optimized, feature_profile="patch")

    cfg = TrainConfig(
        epochs=8 if optimized else 5,
        batch_size=96,
        lr=8e-4 if optimized else 1e-3,
        lambda_phy=0.1,
    )

    pred = _train_model(data, cfg, optimized)
    return compute_metrics(data.y_test, pred)