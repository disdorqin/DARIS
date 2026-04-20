from __future__ import annotations

from typing import Dict

import numpy as np
from xgboost import XGBRegressor

from power_models.common import DatasetBundle, compute_metrics, make_dataset_bundle, physics_postprocess


def train_eval_xgboost(df, optimized: bool) -> Dict[str, float]:
    seq_len = 84 if optimized else 72
    data: DatasetBundle = make_dataset_bundle(df=df, seq_len=seq_len, horizon=1, optimized=optimized)

    x_train = data.x_train.reshape(data.x_train.shape[0], -1)
    x_test = data.x_test.reshape(data.x_test.shape[0], -1)

    model = XGBRegressor(
        n_estimators=140 if optimized else 90,
        max_depth=5 if optimized else 4,
        learning_rate=0.05 if optimized else 0.07,
        subsample=0.85 if optimized else 0.8,
        colsample_bytree=0.85 if optimized else 0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
        tree_method="hist",
        max_bin=256,
        verbosity=0,
    )

    model.fit(x_train, data.y_train)
    pred = model.predict(x_test)

    if optimized:
        pred = physics_postprocess(pred, data.last_test, data.y_train)

    return compute_metrics(data.y_test, pred)
