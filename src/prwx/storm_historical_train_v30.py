from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from prwx.storm_historical_ingest_v30 import TRAINING_TABLE, sample_schema, training_readiness

TRAIN_VERSION = "3.0.0"
ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"
PROCESSED = ROOT / "data" / "processed"
MODEL_PATH = MODELS / "storm_pr_trajectory_ai_v30.joblib"
MODEL_META = PROCESSED / "storm_pr_trajectory_ai_v30.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_training_table() -> pd.DataFrame:
    if not TRAINING_TABLE.exists() or TRAINING_TABLE.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(TRAINING_TABLE)


def _feature_columns(df: pd.DataFrame) -> list[str]:
    allowed = set(sample_schema()["core_features"])
    return [col for col in df.columns if col in allowed and pd.to_numeric(df[col], errors="coerce").notna().any()]


def train_model(*, force: bool = False, test_size: float = 0.2, random_state: int = 42) -> dict[str, Any]:
    MODELS.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df = _load_training_table()
    readiness = training_readiness(df)
    if df.empty:
        result = {"version": TRAIN_VERSION, "status": "missing_training_table", "readiness": readiness, "model_file_exists": False}
        MODEL_META.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
    if not force and not readiness.get("research_ready"):
        result = {
            "version": TRAIN_VERSION,
            "status": "not_enough_data_for_research_training",
            "readiness": readiness,
            "required_action": "Run scripts/38_download_historical_storm_data_v30.py and verify enough approach cases.",
            "model_file_exists": MODEL_PATH.exists(),
        }
        MODEL_META.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    features = _feature_columns(df)
    if not features:
        raise ValueError("No usable historical storm features found.")
    work = df.copy()
    for col in features:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    targets = {
        "approach_500km_72h": "target_approach_500km_72h",
        "approach_300km_72h": "target_approach_300km_72h",
        "direct_pr_150km_72h": "target_direct_pr_150km_72h",
        "min_distance_72h_km": "target_min_distance_72h_km",
    }
    models: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    for model_name, target in targets.items():
        if target not in work.columns:
            continue
        subset = work.loc[pd.to_numeric(work[target], errors="coerce").notna()].copy()
        if len(subset) < 20:
            continue
        x = subset[features]
        y = pd.to_numeric(subset[target], errors="coerce")
        stratify = y if set(y.dropna().unique()).issubset({0, 1}) and y.nunique() == 2 and y.value_counts().min() >= 2 else None
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=random_state, stratify=stratify)
        if set(y.dropna().unique()).issubset({0, 1}):
            model = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(n_estimators=260, min_samples_leaf=2, random_state=random_state, n_jobs=1))
            model.fit(x_train, y_train.astype(int))
            pred = model.predict(x_test)
            metric = {"accuracy": float(accuracy_score(y_test.astype(int), pred)), "test_rows": int(len(y_test))}
            try:
                proba = model.predict_proba(x_test)[:, 1]
                metric["roc_auc"] = float(roc_auc_score(y_test.astype(int), proba))
            except Exception:
                metric["roc_auc"] = None
        else:
            model = make_pipeline(SimpleImputer(strategy="median"), RandomForestRegressor(n_estimators=320, min_samples_leaf=2, random_state=random_state, n_jobs=1))
            model.fit(x_train, y_train.astype(float))
            pred = model.predict(x_test)
            metric = {"mae": float(mean_absolute_error(y_test.astype(float), pred)), "test_rows": int(len(y_test))}
        models[model_name] = model
        metrics[model_name] = metric

    bundle = {"version": TRAIN_VERSION, "features": features, "models": models, "readiness": readiness, "trained_at_utc": utc_now_iso()}
    joblib.dump(bundle, MODEL_PATH)
    result = {
        "version": TRAIN_VERSION,
        "status": "trained_experimental" if force and not readiness.get("operational_candidate") else "trained_candidate",
        "model_path": str(MODEL_PATH),
        "model_file_exists": MODEL_PATH.exists(),
        "features": features,
        "metrics": metrics,
        "readiness": readiness,
        "production_validated": False,
        "disclaimer": "Experimental AI training only. Forecast and emergency guidance must follow NHC, NWS and emergency-management agencies.",
    }
    MODEL_META.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def model_status() -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if MODEL_META.exists() and MODEL_META.stat().st_size:
        try:
            meta = json.loads(MODEL_META.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    return {"version": TRAIN_VERSION, "model_file_exists": MODEL_PATH.exists(), "model_path": str(MODEL_PATH), "metadata": meta}
