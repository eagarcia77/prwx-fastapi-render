from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .evaluate import regression_metrics
from .features import model_feature_columns, prepare_features


@dataclass
class AdvancedTrainedModel:
    """Operational ensemble model used by PR-WX v0.5.

    The model predicts local precipitation bias and adds it to the base forecast.
    It also estimates an uncertainty interval using the distribution of individual
    tree predictions from the Random Forest member.
    """

    models: dict[str, object]
    features: list[str]
    target_col: str
    base_col: str
    residual_std: float
    model_version: str = "0.5.0"


def _make_members(random_state: int = 42) -> dict[str, object]:
    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "huber": make_pipeline(StandardScaler(), HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=300)),
        "random_forest": RandomForestRegressor(
            n_estimators=250,
            random_state=random_state,
            n_jobs=1,
            min_samples_leaf=2,
            max_features="sqrt",
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=250,
            random_state=random_state,
            n_jobs=1,
            min_samples_leaf=2,
            max_features="sqrt",
        ),
        "gradient_boosting": GradientBoostingRegressor(random_state=random_state, n_estimators=180, learning_rate=0.05),
    }


def _weighted_average(preds: dict[str, np.ndarray]) -> np.ndarray:
    # Stable weights for small datasets. Can be tuned using cross-validation later.
    weights = {
        "ridge": 0.12,
        "huber": 0.14,
        "random_forest": 0.30,
        "extra_trees": 0.24,
        "gradient_boosting": 0.20,
    }
    total = np.zeros_like(next(iter(preds.values())), dtype=float)
    used = 0.0
    for name, arr in preds.items():
        w = weights.get(name, 1.0)
        total += w * arr
        used += w
    return total / max(used, 1e-9)


def train_advanced_bias_model(
    df: pd.DataFrame,
    target_col: str = "observed_precip_24h_in",
    base_col: str = "base_precip_24h_in",
    random_state: int = 42,
    test_size: float = 0.2,
) -> tuple[AdvancedTrainedModel, dict[str, float]]:
    """Train an advanced local bias-correction ensemble.

    For the included demo data, the train/test split is intentionally relaxed so
    that users can verify the pipeline. A real production model should train with
    multiple years of observations and archived forecasts.
    """
    data = prepare_features(df).copy()
    data["bias_target"] = data[target_col] - data[base_col]
    features = model_feature_columns(data)
    if not features:
        raise ValueError("No usable model features were found.")

    if len(data) < 12:
        train_df, test_df = data, data
    else:
        train_df, test_df = train_test_split(data, test_size=test_size, random_state=random_state)

    models = _make_members(random_state=random_state)
    trained_models: dict[str, object] = {}
    train_x = train_df[features]
    train_y = train_df["bias_target"]
    for name, model in models.items():
        try:
            model.fit(train_x, train_y)
            trained_models[name] = model
        except Exception:
            # On very tiny demo tables, robust models can fail. Keep the pipeline alive.
            fallback = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            fallback.fit(train_x, train_y)
            trained_models[name] = fallback

    test_x = test_df[features]
    member_preds = {name: model.predict(test_x) for name, model in trained_models.items()}
    bias_pred = _weighted_average(member_preds)
    corrected = (test_df[base_col] + bias_pred).clip(lower=0)
    residuals = test_df[target_col].to_numpy(dtype=float) - corrected
    residual_std = float(np.nanstd(residuals)) if len(residuals) else 0.0
    metrics = regression_metrics(test_df[target_col], corrected)
    metrics["residual_std"] = residual_std
    metrics["members"] = float(len(trained_models))

    trained = AdvancedTrainedModel(
        models=trained_models,
        features=features,
        target_col=target_col,
        base_col=base_col,
        residual_std=residual_std,
    )
    return trained, metrics


def _tree_interval(model: object, x: pd.DataFrame, base: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    estimators = getattr(model, "estimators_", None)
    if estimators is None:
        return None
    try:
        x_values = x.to_numpy() if hasattr(x, "to_numpy") else x
        tree_preds = np.vstack([est.predict(x_values) for est in estimators])
        low = np.percentile(tree_preds, 10, axis=0) + base
        high = np.percentile(tree_preds, 90, axis=0) + base
        return np.maximum(low, 0), np.maximum(high, 0)
    except Exception:
        return None


def predict_advanced_corrected(trained: AdvancedTrainedModel, df: pd.DataFrame) -> pd.DataFrame:
    data = prepare_features(df).copy()
    missing = [c for c in trained.features if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required model features: {missing}")

    x = data[trained.features]
    member_preds = {name: model.predict(x) for name, model in trained.models.items()}
    bias = _weighted_average(member_preds)
    out = df.copy()
    base = out[trained.base_col].to_numpy(dtype=float)
    corrected = np.maximum(base + bias, 0)
    out["predicted_bias_in"] = bias
    out["corrected_precip_24h_in"] = corrected

    # Member spread and approximate probabilistic intervals.
    stack = np.vstack(list(member_preds.values()))
    out["ensemble_spread_in"] = np.nanstd(stack, axis=0)
    out["precip_p10_in"] = np.maximum(np.percentile(stack, 10, axis=0) + base - trained.residual_std, 0)
    out["precip_p90_in"] = np.maximum(np.percentile(stack, 90, axis=0) + base + trained.residual_std, 0)

    rf_interval = _tree_interval(trained.models.get("random_forest"), x, base)
    if rf_interval is not None:
        out["rf_p10_in"], out["rf_p90_in"] = rf_interval

    # Probability-like indicators for impact thresholds.
    samples = []
    for arr in member_preds.values():
        samples.append(np.maximum(base + arr, 0))
    sample_stack = np.vstack(samples)
    out["prob_ge_1in"] = (sample_stack >= 1.0).mean(axis=0)
    out["prob_ge_2in"] = (sample_stack >= 2.0).mean(axis=0)
    out["prob_ge_4in"] = (sample_stack >= 4.0).mean(axis=0)
    return out


def save_advanced_model(trained: AdvancedTrainedModel, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(trained, path)


def load_advanced_model(path: str | Path) -> AdvancedTrainedModel:
    return joblib.load(path)
