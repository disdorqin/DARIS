from __future__ import annotations

from typing import Dict

import numpy as np
import torch
from xgboost import XGBRegressor

from power_models.common import DatasetBundle, compute_metrics, make_dataset_bundle, physics_postprocess


def _fit_model(data: DatasetBundle, optimized: bool, use_gpu: bool) -> np.ndarray:
    x_train = data.x_train.reshape(data.x_train.shape[0], -1)
    x_test = data.x_test.reshape(data.x_test.shape[0], -1)

    params = dict(
        n_estimators=50 if optimized else 30,
        max_depth=4 if optimized else 3,
        learning_rate=0.08 if optimized else 0.1,
        subsample=0.9 if optimized else 0.85,
        colsample_bytree=0.9 if optimized else 0.85,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
        verbosity=0,
        max_bin=128,
    )
    if use_gpu:
        params.update(tree_method="gpu_hist", predictor="gpu_predictor")
    else:
        params.update(tree_method="hist")

    model = XGBRegressor(**params)
    model.fit(x_train, data.y_train)
    pred = model.predict(x_test)

    if optimized:
        pred = physics_postprocess(pred, data.last_test, data.y_train)
    return pred


def train_eval_xgboost(df, optimized: bool) -> Dict[str, float]:
    seq_len = 60 if optimized else 48
    data: DatasetBundle = make_dataset_bundle(df=df, seq_len=seq_len, horizon=1, optimized=optimized, feature_profile="xgboost")

    use_gpu = torch.cuda.is_available()
    try:
        pred = _fit_model(data, optimized=optimized, use_gpu=use_gpu)
    except Exception:
        if use_gpu:
            pred = _fit_model(data, optimized=optimized, use_gpu=False)
        else:
            raise

    return compute_metrics(data.y_test, pred)
