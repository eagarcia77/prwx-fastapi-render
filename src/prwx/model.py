from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import prepare_features, model_feature_columns
from .evaluate import regression_metrics


@dataclass
class TrainedModel:
    model: object
    features: list[str]
    target_col: str
    base_col: str


def make_model(algorithm: str = "HistGradientBoostingRegressor", random_state: int = 42):
    if algorithm == "RandomForestRegressor":
        return RandomForestRegressor(n_estimators=200, random_state=random_state, n_jobs=1, min_samples_leaf=2)
    # Ridge is intentionally the default for the starter because it is fast, stable,
    # and works with small sample tables. For production, test tree/boosting models.
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


def train_bias_model(
    df: pd.DataFrame,
    target_col: str = "observed_precip_24h_in",
    base_col: str = "base_precip_24h_in",
    algorithm: str = "Ridge",
    random_state: int = 42,
    test_size: float = 0.2,
) -> tuple[TrainedModel, dict[str, float]]:
    """Train a model to predict local bias: observed - base forecast."""
    data = prepare_features(df)
    data["bias_target"] = data[target_col] - data[base_col]
    features = model_feature_columns(data)

    if len(data) < 8:
        # Small sample fallback for the included demo data. Real training should use thousands of rows.
        train_df, test_df = data, data
    else:
        train_df, test_df = train_test_split(data, test_size=test_size, random_state=random_state)

    model = make_model(algorithm, random_state=random_state)
    model.fit(train_df[features], train_df["bias_target"])

    predicted_bias = model.predict(test_df[features])
    corrected = test_df[base_col] + predicted_bias
    metrics = regression_metrics(test_df[target_col], corrected)

    return TrainedModel(model=model, features=features, target_col=target_col, base_col=base_col), metrics


def predict_corrected(trained: TrainedModel, df: pd.DataFrame) -> pd.DataFrame:
    data = prepare_features(df)
    missing = [c for c in trained.features if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required model features: {missing}")
    bias = trained.model.predict(data[trained.features])
    out = df.copy()
    out["predicted_bias_in"] = bias
    out["corrected_precip_24h_in"] = out[trained.base_col] + out["predicted_bias_in"]
    out["corrected_precip_24h_in"] = out["corrected_precip_24h_in"].clip(lower=0)
    return out


def save_model(trained: TrainedModel, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(trained, path)


def load_model(path: str | Path) -> TrainedModel:
    return joblib.load(path)
