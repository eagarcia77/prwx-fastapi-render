from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from prwx.caribbean_model_v20 import MODEL_NAME, MODEL_VERSION, bundle_summary, load_caribbean_model, training_readiness
from prwx.caribbean_sources import EXCLUDED_CORE_MODELS, source_registry, sources_for_area

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MODEL_PATH = ROOT / "models" / "pr_caribe_wx_v20.joblib"
MODEL_META_PATH = PROCESSED / "pr_caribe_wx_v20_training.json"
TRAINING_CANDIDATES = (
    ROOT / "data" / "training" / "pr_caribbean_training.parquet",
    ROOT / "data" / "training" / "pr_caribbean_training.csv",
)
PREDICTION_CANDIDATES = (
    PROCESSED / "live_predictions_v10.csv",
    PROCESSED / "live_predictions_v9.csv",
    PROCESSED / "live_predictions_v8.csv",
    PROCESSED / "live_predictions_v6.csv",
    PROCESSED / "live_predictions_v5.csv",
    PROCESSED / "live_predictions.csv",
)
ALERT_CANDIDATES = (
    PROCESSED / "safety_alerts_v9.csv",
    PROCESSED / "live_nws_alerts.csv",
)

router = APIRouter(tags=["PR-CARIBE WX v2"])


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.stat().st_size:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _read_table(path: Path) -> pd.DataFrame:
    try:
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame()
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _first_table(paths: tuple[Path, ...]) -> tuple[pd.DataFrame, str | None]:
    for path in paths:
        frame = _read_table(path)
        if not frame.empty:
            return frame, str(path)
    return pd.DataFrame(), None


def _first_value(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = row.get(name)
        if value is None:
            continue
        try:
            if pd.isna(value):
                continue
        except Exception:
            pass
        return value
    return None


def _model_status_payload() -> dict[str, Any]:
    metadata = _read_json(MODEL_META_PATH)
    payload: dict[str, Any] = {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "model_file_exists": MODEL_PATH.exists(),
        "training_metadata_exists": bool(metadata),
        "production_validated": False,
        "status": "training_required",
        "message": "The new Caribbean model is not considered operational until real historical training and independent validation are completed.",
    }
    if MODEL_PATH.exists():
        try:
            bundle = load_caribbean_model(MODEL_PATH)
            payload["bundle"] = bundle_summary(bundle)
            payload["status"] = "research_model_available"
        except Exception as exc:
            payload["status"] = "model_load_error"
            payload["error"] = str(exc)
    if metadata:
        payload["training"] = metadata
        payload["production_validated"] = bool(metadata.get("production_validated", False))
        if payload["production_validated"]:
            payload["status"] = "production_validated"
    return payload


@router.get("/caribbean/model/sources")
def caribbean_model_sources():
    return {
        "model": MODEL_NAME,
        "version": MODEL_VERSION,
        "sources": source_registry(),
        "excluded_as_core": EXCLUDED_CORE_MODELS,
        "design_rule": "A source is only used where its documented operational domain covers the requested location.",
    }


@router.get("/caribbean/model/status")
def caribbean_model_status():
    return _model_status_payload()


@router.get("/caribbean/model/readiness")
def caribbean_model_readiness():
    frame, path = _first_table(TRAINING_CANDIDATES)
    if frame.empty:
        return {
            "model": MODEL_NAME,
            "version": MODEL_VERSION,
            "training_dataset": None,
            "research_ready": False,
            "operational_candidate": False,
            "production_validated": False,
            "message": "Create data/training/pr_caribbean_training.csv or .parquet with real archived forecasts and observations.",
        }
    readiness = training_readiness(frame)
    readiness["training_dataset"] = path
    readiness["model"] = MODEL_NAME
    readiness["version"] = MODEL_VERSION
    return readiness


@router.get("/weather/report/{municipality}")
def weather_report(municipality: str):
    predictions, prediction_path = _first_table(PREDICTION_CANDIDATES)
    if predictions.empty or "municipality" not in predictions.columns:
        raise HTTPException(status_code=404, detail="No operational municipality forecast is available yet.")

    match = predictions[predictions["municipality"].astype(str).str.casefold() == municipality.casefold()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Municipality not found: {municipality}")
    row = match.iloc[0].to_dict()

    alerts, alerts_path = _first_table(ALERT_CANDIDATES)
    alert_records: list[dict[str, Any]] = []
    if not alerts.empty:
        if "municipality" in alerts.columns:
            selected = alerts[alerts["municipality"].astype(str).str.casefold() == municipality.casefold()]
            alert_records = selected.head(20).to_dict(orient="records")
        else:
            alert_records = alerts.head(20).to_dict(orient="records")

    temp = _first_value(row, "temp_f", "temperature_f", "base_temp_f", "forecast_temp_f")
    feels = _first_value(row, "feels_like_f", "heat_index_f", "base_heat_index_f")
    rain24 = _first_value(row, "forecast_precip_24h_in", "corrected_precip_24h_in", "base_precip_24h_in")
    pop = _first_value(row, "precip_probability_max", "probability_precipitation", "pop")
    wind = _first_value(row, "forecast_wind_speed_mph", "wind_speed_mph", "wind_mph")
    gust = _first_value(row, "forecast_wind_gust_mph", "wind_gust_mph", "gust_mph")
    rh = _first_value(row, "forecast_relative_humidity", "relative_humidity", "humidity")
    risk = _first_value(row, "impact_level", "risk_level", "operational_risk_level")
    p10 = _first_value(row, "forecast_precip_24h_in_p10", "precip_p10_in", "rf_p10_in")
    p90 = _first_value(row, "forecast_precip_24h_in_p90", "precip_p90_in", "rf_p90_in")

    summary_parts = [f"Informe experimental para {row.get('municipality', municipality)}."]
    if temp is not None:
        summary_parts.append(f"Temperatura estimada {temp} °F.")
    if feels is not None:
        summary_parts.append(f"Sensación térmica aproximada {feels} °F.")
    if rain24 is not None:
        summary_parts.append(f"Lluvia estimada en 24 horas {rain24} pulgadas.")
    if wind is not None:
        summary_parts.append(f"Viento aproximado {wind} mph.")
    if risk is not None:
        summary_parts.append(f"Nivel de impacto {risk}.")

    return {
        "municipality": row.get("municipality", municipality),
        "generated_at_utc": row.get("generated_at_utc") or row.get("run_generated_at_utc"),
        "summary_es": " ".join(summary_parts),
        "conditions": {
            "temperature_f": temp,
            "feels_like_f": feels,
            "relative_humidity_pct": rh,
            "wind_mph": wind,
            "wind_gust_mph": gust,
        },
        "precipitation": {
            "forecast_24h_in": rain24,
            "probability_max_pct": pop,
            "p10_in": p10,
            "p90_in": p90,
        },
        "hazards": {
            "risk_level": risk,
            "alerts": alert_records,
        },
        "model": _model_status_payload(),
        "applicable_sources": sources_for_area("Puerto Rico"),
        "data_files": {"predictions": prediction_path, "alerts": alerts_path},
        "disclaimer": "Experimental PR-WX product. Official warnings and emergency decisions must follow NOAA/NWS San Juan, NHC and relevant emergency-management agencies.",
    }
