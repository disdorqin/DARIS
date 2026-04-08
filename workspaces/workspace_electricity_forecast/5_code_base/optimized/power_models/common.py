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


FEATURE_PROFILES = {
    "baseline": {
        "aux_features": 0,
        "windows": (),
        "include_time": False,
        "include_lags": False,
        "include_diffs": False,
        "include_interactions": False,
    },
    "temporal": {
        "aux_features": 4,
        "windows": (6, 24),
        "include_time": True,
        "include_lags": True,
        "include_diffs": True,
        "include_interactions": False,
    },
    "graph": {
        "aux_features": 5,
        "windows": (3, 12, 24),
        "include_time": True,
        "include_lags": True,
        "include_diffs": True,
        "include_interactions": True,
    },
    "patch": {
        "aux_features": 4,
        "windows": (6, 24, 48),
        "include_time": True,
        "include_lags": True,
        "include_diffs": True,
        "include_interactions": False,
    },
    "xgboost": {
        "aux_features": 2,
        "windows": (3,),
        "include_time": True,
        "include_lags": True,
        "include_diffs": True,
        "include_interactions": True,
    },
}


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


def _time_context_features(length: int) -> pd.DataFrame:
    if length <= 0:
        return pd.DataFrame()

    position = np.arange(length, dtype=np.float32)
    normalized = position / max(float(length - 1), 1.0)
    periods = {
        "time_sin_day": np.sin(2.0 * np.pi * position / 24.0),
        "time_cos_day": np.cos(2.0 * np.pi * position / 24.0),
        "time_sin_week": np.sin(2.0 * np.pi * position / (24.0 * 7.0)),
        "time_cos_week": np.cos(2.0 * np.pi * position / (24.0 * 7.0)),
        "time_sin_month": np.sin(2.0 * np.pi * position / (24.0 * 30.0)),
        "time_cos_month": np.cos(2.0 * np.pi * position / (24.0 * 30.0)),
        "time_index_norm": normalized,
    }
    return pd.DataFrame(periods)


def _select_auxiliary_columns(frame: pd.DataFrame, max_aux_features: int) -> list[str]:
    if frame.shape[1] <= 1 or max_aux_features <= 0:
        return []

    corr = frame.corr(numeric_only=True).abs()
    target_col = frame.columns[0]
    if target_col not in corr.columns:
        return list(frame.columns[1:1 + max_aux_features])

    ranked = corr[target_col].drop(labels=[target_col], errors="ignore").sort_values(ascending=False)
    return [col for col in ranked.index.tolist()[:max_aux_features] if col in frame.columns]


def build_feature_matrix(df: pd.DataFrame, profile: str = "baseline") -> pd.DataFrame:
    frame = df.astype(np.float32).copy()
    rule = FEATURE_PROFILES.get(profile, FEATURE_PROFILES["baseline"])
    if profile == "baseline" or frame.empty:
        return frame

    parts: list[pd.DataFrame] = [frame]
    target_col = frame.columns[0]
    selected_cols = [target_col, *_select_auxiliary_columns(frame, rule["aux_features"])]
    selected = frame.loc[:, selected_cols]

    if rule["include_time"]:
        parts.append(_time_context_features(len(frame)).reset_index(drop=True))

    if rule["include_lags"]:
        parts.append(selected.shift(1).bfill().add_suffix("_lag1"))
        parts.append(selected.shift(24).bfill().add_suffix("_lag24"))

    if rule["include_diffs"]:
        parts.append(selected.diff().fillna(0.0).add_suffix("_diff1"))
        parts.append(selected.diff(24).fillna(0.0).add_suffix("_diff24"))

    for window in rule["windows"]:
        rolling = selected.rolling(window=window, min_periods=1)
        parts.append(rolling.mean().add_suffix(f"_rollmean_{window}"))
        parts.append(rolling.std().fillna(0.0).add_suffix(f"_rollstd_{window}"))

    if rule["include_interactions"] and len(selected_cols) > 1:
        target = selected[[target_col]]
        aux = selected.drop(columns=[target_col])
        interactions = aux.multiply(target[target_col], axis=0)
        interactions.columns = [f"{target_col}_x_{col}" for col in aux.columns]
        parts.append(interactions)

    engineered = pd.concat(parts, axis=1)
    engineered = engineered.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)
    return engineered.astype(np.float32)


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
    feature_profile: str = "baseline",
) -> DatasetBundle:
    profile = feature_profile if optimized else "baseline"
    features_frame = build_feature_matrix(df, profile=profile)
    features = features_frame.values.astype(np.float32)
    if optimized and profile == "baseline":
        features = decouple_features(features)
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
    y_true = np.asarray(y_true).reshape(-1)
    y_pred = np.asarray(y_pred).reshape(-1)

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    smape = float(np.mean(2.0 * np.abs(y_pred - y_true) / np.maximum(np.abs(y_true) + np.abs(y_pred), 1e-8)) * 100.0)
    wape = float(np.sum(np.abs(y_pred - y_true)) / max(float(np.sum(np.abs(y_true))), 1e-8) * 100.0)
    r2 = float(r2_score(y_true, y_pred))
    return {"MAE": mae, "RMSE": rmse, "SMAPE": smape, "WAPE": wape, "R2": r2}


def physics_postprocess(y_pred: np.ndarray, last_target: np.ndarray, y_train: np.ndarray) -> np.ndarray:
    lower = 0.0
    upper = float(np.quantile(y_train, 0.995) * 1.05)
    ramp = float(np.quantile(np.abs(np.diff(y_train)), 0.99))

    out = np.clip(y_pred, lower, upper)
    out = np.clip(out, last_target - ramp, last_target + ramp)
    return out
