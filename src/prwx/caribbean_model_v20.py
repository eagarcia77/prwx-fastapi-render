from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MODEL_NAME = "PR-CARIBE WX Hybrid"
MODEL_VERSION = "2.0.0"

TARGET_SPECS: dict[str, dict[str, Any]] = {
    "observed_temp_f": {"output": "forecast_temp_f", "floor": None},
    "observed_precip_1h_in": {"output": "forecast_precip_1h_in", "floor": 0.0},
    "observed_precip_6h_in": {"output": "forecast_precip_6h_in", "floor": 0.0},
    "observed_precip_24h_in": {"output": "forecast_precip_24h_in", "floor": 0.0},
    "observed_wind_speed_mph": {"output": "forecast_wind_speed_mph", "floor": 0.0},
    "observed_wind_gust_mph": {"output": "forecast_wind_gust_mph", "floor": 0.0},
    "observed_relative_humidity": {"output": "forecast_relative_humidity", "floor": 0.0, "ceiling": 100.0},
    "observed_pressure_hpa": {"output": "forecast_pressure_hpa", "floor": 800.0, "ceiling": 1100.0},
}

STATIC_FEATURES = {
    "lat", "lon", "elevation_m", "coastal", "distance_to_coast_km", "slope_deg", "aspect_deg",
    "month", "hour", "dayofyear", "month_sin", "month_cos", "hour_sin", "hour_cos",
    "dayofyear_sin", "dayofyear_cos", "land_fraction", "sea_surface_temp_c",
}
SOURCE_PREFIXES = (
    "nws_", "nam_pr_", "gfs_", "gefs_", "mrms_", "tjua_", "goes_", "nhc_", "hafs_",
    "gfs_wave_", "ndbc_", "soil_", "dust_", "sst_", "pw_",
)
LEAKAGE_PREFIXES = ("observed_", "verified_", "target_", "error_")


@dataclass
class TargetModel:
    target: str
    output: str
    features: list[str]
    members: dict[str, object]
    metrics: dict[str, float]
    train_rows: int
    validation_rows: int


@dataclass
class CaribbeanModelBundle:
    model_name: str = MODEL_NAME
    model_version: str = MODEL_VERSION
    targets: dict[str, TargetModel] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def _time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    date_col = next((c for c in ("valid_time_utc", "timestamp_utc", "date", "time") if c in out.columns), None)
    if date_col:
        dt = pd.to_datetime(out[date_col], errors="coerce", utc=True)
        if "month" not in out.columns:
            out["month"] = dt.dt.month
        if "hour" not in out.columns:
            out["hour"] = dt.dt.hour
        out["dayofyear"] = dt.dt.dayofyear
    if "month" in out.columns:
        out["month_sin"] = np.sin(2 * np.pi * pd.to_numeric(out["month"], errors="coerce") / 12)
        out["month_cos"] = np.cos(2 * np.pi * pd.to_numeric(out["month"], errors="coerce") / 12)
    if "hour" in out.columns:
        out["hour_sin"] = np.sin(2 * np.pi * pd.to_numeric(out["hour"], errors="coerce") / 24)
        out["hour_cos"] = np.cos(2 * np.pi * pd.to_numeric(out["hour"], errors="coerce") / 24)
    if "dayofyear" in out.columns:
        doy = pd.to_numeric(out["dayofyear"], errors="coerce")
        out["dayofyear_sin"] = np.sin(2 * np.pi * doy / 365.25)
        out["dayofyear_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return out


def prepare_caribbean_features(df: pd.DataFrame) -> pd.DataFrame:
    out = _time_features(df)
    for col in list(out.columns):
        if col in STATIC_FEATURES or col.startswith(SOURCE_PREFIXES):
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def select_features(df: pd.DataFrame) -> list[str]:
    selected: list[str] = []
    for col in df.columns:
        if col.startswith(LEAKAGE_PREFIXES):
            continue
        if col in STATIC_FEATURES or col.startswith(SOURCE_PREFIXES):
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().any():
                selected.append(col)
    return selected


def _member_models(random_state: int) -> dict[str, object]:
    return {
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.5)),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(
                n_estimators=320,
                min_samples_leaf=2,
                max_features="sqrt",
                n_jobs=1,
                random_state=random_state,
            ),
        ),
        "extra_trees": make_pipeline(
            SimpleImputer(strategy="median"),
            ExtraTreesRegressor(
                n_estimators=320,
                min_samples_leaf=2,
                max_features="sqrt",
                n_jobs=1,
                random_state=random_state,
            ),
        ),
        "hist_gradient_boosting": make_pipeline(
            SimpleImputer(strategy="median"),
            HistGradientBoostingRegressor(
                learning_rate=0.055,
                max_iter=260,
                max_leaf_nodes=31,
                l2_regularization=0.35,
                random_state=random_state,
            ),
        ),
    }


def _split_chronological(df: pd.DataFrame, validation_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = df.copy()
    date_col = next((c for c in ("valid_time_utc", "timestamp_utc", "date", "time") if c in work.columns), None)
    if date_col:
        work["__sort_time"] = pd.to_datetime(work[date_col], errors="coerce", utc=True)
        work = work.sort_values("__sort_time", kind="stable").drop(columns=["__sort_time"])
    n_val = max(1, int(round(len(work) * validation_fraction)))
    if len(work) < 20:
        return work, work
    return work.iloc[:-n_val].copy(), work.iloc[-n_val:].copy()


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "bias": float(np.nanmean(y_pred - y_true)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else 0.0,
    }


def _ensemble_predict(members: dict[str, object], x: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    stack = np.vstack([model.predict(x) for model in members.values()])
    mean = np.nanmean(stack, axis=0)
    p10 = np.nanpercentile(stack, 10, axis=0)
    p90 = np.nanpercentile(stack, 90, axis=0)
    return mean, p10, p90


def training_readiness(df: pd.DataFrame) -> dict[str, Any]:
    rows = int(len(df))
    date_col = next((c for c in ("valid_time_utc", "timestamp_utc", "date", "time") if c in df.columns), None)
    span_days = 0
    if date_col and rows:
        dates = pd.to_datetime(df[date_col], errors="coerce", utc=True).dropna()
        if not dates.empty:
            span_days = int((dates.max() - dates.min()).total_seconds() // 86400)
    station_col = next((c for c in ("station_id", "location_id") if c in df.columns), None)
    stations = int(df[station_col].nunique()) if station_col else 0
    island_col = next((c for c in ("island", "country", "territory") if c in df.columns), None)
    islands = int(df[island_col].nunique()) if island_col else 0
    target_count = sum(1 for target in TARGET_SPECS if target in df.columns and pd.to_numeric(df[target], errors="coerce").notna().sum() >= 20)

    research_ready = rows >= 5000 and span_days >= 90 and stations >= 8 and target_count >= 2
    operational_candidate = rows >= 50000 and span_days >= 365 and stations >= 25 and islands >= 5 and target_count >= 4
    return {
        "rows": rows,
        "span_days": span_days,
        "stations": stations,
        "islands_or_territories": islands,
        "trainable_targets": target_count,
        "research_ready": research_ready,
        "operational_candidate": operational_candidate,
        "production_validated": False,
        "note": "Production validation requires independent backtesting, extreme-event verification and meteorological review; row thresholds alone are not sufficient.",
    }


def train_caribbean_model(
    df: pd.DataFrame,
    *,
    random_state: int = 42,
    validation_fraction: float = 0.2,
) -> tuple[CaribbeanModelBundle, dict[str, Any]]:
    data = prepare_caribbean_features(df)
    features = select_features(data)
    if not features:
        raise ValueError("No PR-CARIBE model features were found. Add official NWP/observation/static predictors first.")

    bundle = CaribbeanModelBundle(metadata={"readiness": training_readiness(data), "features_available": features})
    report: dict[str, Any] = {"model": MODEL_NAME, "version": MODEL_VERSION, "targets": {}, "readiness": bundle.metadata["readiness"]}

    for target, spec in TARGET_SPECS.items():
        if target not in data.columns:
            continue
        target_values = pd.to_numeric(data[target], errors="coerce")
        subset = data.loc[target_values.notna()].copy()
        subset[target] = target_values.loc[target_values.notna()]
        if len(subset) < 20:
            continue

        train_df, val_df = _split_chronological(subset, validation_fraction=validation_fraction)
        x_train, y_train = train_df[features], train_df[target].astype(float).to_numpy()
        x_val, y_val = val_df[features], val_df[target].astype(float).to_numpy()
        members = _member_models(random_state)
        for model in members.values():
            model.fit(x_train, y_train)
        pred, _, _ = _ensemble_predict(members, x_val)
        floor = spec.get("floor")
        ceiling = spec.get("ceiling")
        if floor is not None:
            pred = np.maximum(pred, float(floor))
        if ceiling is not None:
            pred = np.minimum(pred, float(ceiling))
        metrics = _metrics(y_val, pred)
        target_model = TargetModel(
            target=target,
            output=str(spec["output"]),
            features=list(features),
            members=members,
            metrics=metrics,
            train_rows=int(len(train_df)),
            validation_rows=int(len(val_df)),
        )
        bundle.targets[target] = target_model
        report["targets"][target] = {
            "output": target_model.output,
            "metrics": metrics,
            "train_rows": target_model.train_rows,
            "validation_rows": target_model.validation_rows,
        }

    if not bundle.targets:
        raise ValueError("No target has at least 20 valid rows. The demonstration file is not sufficient for PR-CARIBE v2 training.")
    return bundle, report


def predict_caribbean(bundle: CaribbeanModelBundle, df: pd.DataFrame) -> pd.DataFrame:
    data = prepare_caribbean_features(df)
    out = df.copy()
    for target, model in bundle.targets.items():
        missing = [feature for feature in model.features if feature not in data.columns]
        if missing:
            raise ValueError(f"Missing required features for {target}: {missing}")
        mean, p10, p90 = _ensemble_predict(model.members, data[model.features])
        spec = TARGET_SPECS[target]
        floor = spec.get("floor")
        ceiling = spec.get("ceiling")
        if floor is not None:
            mean, p10, p90 = (np.maximum(values, float(floor)) for values in (mean, p10, p90))
        if ceiling is not None:
            mean, p10, p90 = (np.minimum(values, float(ceiling)) for values in (mean, p10, p90))
        out[model.output] = mean
        out[f"{model.output}_p10"] = p10
        out[f"{model.output}_p90"] = p90
        out[f"{model.output}_spread"] = p90 - p10
    out["pr_caribe_model"] = MODEL_NAME
    out["pr_caribe_model_version"] = MODEL_VERSION
    return out


def save_caribbean_model(bundle: CaribbeanModelBundle, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_caribbean_model(path: str | Path) -> CaribbeanModelBundle:
    return joblib.load(Path(path))


def bundle_summary(bundle: CaribbeanModelBundle) -> dict[str, Any]:
    return {
        "model_name": bundle.model_name,
        "model_version": bundle.model_version,
        "targets": {
            key: {
                "output": value.output,
                "features": len(value.features),
                "metrics": value.metrics,
                "train_rows": value.train_rows,
                "validation_rows": value.validation_rows,
            }
            for key, value in bundle.targets.items()
        },
        "metadata": bundle.metadata,
    }
