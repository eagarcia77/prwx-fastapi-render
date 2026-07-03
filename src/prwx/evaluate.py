from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
        "bias": float(np.mean(y_pred - y_true)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan"),
    }


def event_metrics(y_true, y_pred, threshold: float) -> dict[str, float]:
    """Evaluate yes/no heavy-rain event detection."""
    obs = np.asarray(y_true) >= threshold
    pred = np.asarray(y_pred) >= threshold
    hits = int(np.logical_and(obs, pred).sum())
    misses = int(np.logical_and(obs, ~pred).sum())
    false_alarms = int(np.logical_and(~obs, pred).sum())
    correct_negatives = int(np.logical_and(~obs, ~pred).sum())

    pod = hits / (hits + misses) if hits + misses else float("nan")
    far = false_alarms / (hits + false_alarms) if hits + false_alarms else float("nan")
    csi = hits / (hits + misses + false_alarms) if hits + misses + false_alarms else float("nan")

    return {
        "hits": hits,
        "misses": misses,
        "false_alarms": false_alarms,
        "correct_negatives": correct_negatives,
        "pod_probability_of_detection": float(pod),
        "far_false_alarm_ratio": float(far),
        "csi_critical_success_index": float(csi),
    }


def compare_base_vs_corrected(df: pd.DataFrame, observed_col: str, base_col: str, corrected_col: str, threshold: float = 1.0) -> pd.DataFrame:
    rows = []
    for label, pred_col in [("base", base_col), ("corrected", corrected_col)]:
        metrics = regression_metrics(df[observed_col], df[pred_col])
        metrics.update(event_metrics(df[observed_col], df[pred_col], threshold=threshold))
        metrics["model"] = label
        rows.append(metrics)
    return pd.DataFrame(rows)
