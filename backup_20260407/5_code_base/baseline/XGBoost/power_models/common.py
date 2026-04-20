from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


@dataclass
class DatasetBundle:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    last_train: np.ndarray
    last_val: np.ndarray
    last_test: np.ndarray
    n_features: int


def read_numeric_timeseries(csv_path: str) -> pd.DataFrame:
    path = Path(csv_path)
    encodings = ["utf-8", "utf-8-sig", "gbk"]
    last_err = None
    raw_df = None
    for enc in encodings:
        try:
            raw_df = pd.read_csv(path, encoding=enc)
            break
        except Exception as exc:  # pylint: disable=broad-except
            last_err = exc
    if raw_df is None:
        raise RuntimeError(f"Failed to read {csv_path}: {last_err}")

    feature_df = raw_df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    feature_df = feature_df.replace([np.inf, -np.inf], np.nan)
    feature_df = feature_df.interpolate(limit_direction="both").ffill().bfill()

    max_abs = feature_df.abs().max(axis=0)
    feature_df = feature_df.loc[:, max_abs > 1e-8]
    if feature_df.empty:
        raise ValueError("No valid numeric feature columns after filtering")

    return feature_df


def decouple_features(values: np.ndarray, trend_window: int = 24) -> np.ndarray:
    trend = pd.DataFrame(values).rolling(window=trend_window, min_periods=1).mean().values
    resid = values - trend
    return np.concatenate([values, trend, resid], axis=1)


def build_windows(
    values: np.ndarray,
    seq_len: int,
    horizon: int,
    target_idx: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_list = []
    y_list = []
    last_target = []
    upper = len(values) - seq_len - horizon + 1
    for start in range(upper):
        end = start + seq_len
        y_pos = end + horizon - 1
        x_list.append(values[start:end])
        y_list.append(values[y_pos, target_idx])
        last_target.append(values[end - 1, target_idx])

    x = np.asarray(x_list, dtype=np.float32)
    y = np.asarray(y_list, dtype=np.float32)
    last = np.asarray(last_target, dtype=np.float32)
    return x, y, last


def make_dataset_bundle(
    df: pd.DataFrame,
    seq_len: int,
    horizon: int,
    optimized: bool,
) -> DatasetBundle:
    raw = df.values.astype(np.float32)
    features = decouple_features(raw) if optimized else raw
    x, y, last = build_windows(features, seq_len=seq_len, horizon=horizon)

    n = len(x)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    return DatasetBundle(
        x_train=x[:train_end],
        y_train=y[:train_end],
        x_val=x[train_end:val_end],
        y_val=y[train_end:val_end],
        x_test=x[val_end:],
        y_test=y[val_end:],
        last_train=last[:train_end],
        last_val=last[train_end:val_end],
        last_test=last[val_end:],
        n_features=x.shape[-1],
    )


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    return {"MAE": mae, "RMSE": rmse, "R2": r2}


def physics_postprocess(y_pred: np.ndarray, last_target: np.ndarray, y_train: np.ndarray) -> np.ndarray:
    lower = 0.0
    upper = float(np.quantile(y_train, 0.995) * 1.05)
    ramp = float(np.quantile(np.abs(np.diff(y_train)), 0.99))

    out = np.clip(y_pred, lower, upper)
    out = np.clip(out, last_target - ramp, last_target + ramp)
    return out
