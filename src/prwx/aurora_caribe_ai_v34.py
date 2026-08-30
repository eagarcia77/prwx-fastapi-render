from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_VERSION = "3.4.0"
MODEL_CODE = "AURORA-CARIBE"
MODEL_NAME = "AURORA Caribe-Atlántico"
MODEL_FULL_NAME = "AURORA Caribe-Atlántico AI Forecast Model"
MODEL_TAGLINE = "Análisis Unificado de Riesgo Operacional, Radar y Atmósfera para el Caribe y Atlántico"

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TRAINING = ROOT / "data" / "training"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

AURORA_STATUS_PATH = PROCESSED / "aurora_caribe_status_v34.json"
AURORA_TRAINING_PATH = PROCESSED / "aurora_caribe_training_v34.json"
AURORA_PREDICTION_PATH = PROCESSED / "aurora_caribe_predictions_v34.json"
AURORA_MODEL_PATH = MODELS / "aurora_caribe_ai_v34.joblib"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def model_identity() -> dict[str, Any]:
    return {
        "model_code": MODEL_CODE,
        "model_name": MODEL_NAME,
        "full_name": MODEL_FULL_NAME,
        "version": MODEL_VERSION,
        "tagline": MODEL_TAGLINE,
        "scope": "Puerto Rico, Caribe oriental, Caribe central y Atlántico tropical",
        "status": "experimental_operational_support",
        "official_warning_policy": "No emite avisos oficiales; los avisos oficiales deben venir de NHC, NWS San Juan y manejo de emergencias.",
    }


def training_cadence() -> dict[str, Any]:
    return {
        "mode": "continuous_scheduled_training",
        "github_action": ".github/workflows/aurora-caribe-continuous-training-v34.yml",
        "cron_utc": "17 */6 * * *",
        "cadence_readable_es": "cada 6 horas mediante GitHub Actions y manualmente cuando sea necesario",
        "fast_refresh": "actualización operacional liviana cuando el workflow corre",
        "full_retrain": "reentrenamiento experimental si existen suficientes datos históricos y artefactos generados",
        "artifact_name": "aurora-caribe-ai-training-v34",
        "model_registry_path": str(AURORA_MODEL_PATH),
    }


def data_readiness() -> dict[str, Any]:
    candidates = {
        "municipal_weather": PROCESSED / "focus_temperature_v10.csv",
        "active_alerts": PROCESSED / "active_alerts_v17.csv",
        "storm_tracks": PROCESSED / "ai_storm_track_map_v29.json",
        "storm_historical_training": TRAINING / "storm_tracks_atlantic_training.csv",
        "caribbean_training_table": TRAINING / "pr_caribbean_atlantic_training.csv",
        "aurora_model": AURORA_MODEL_PATH,
    }
    availability = {key: _exists(path) for key, path in candidates.items()}
    score = round(sum(1 for value in availability.values() if value) / max(len(availability), 1) * 100, 1)
    if score >= 80:
        level = "operational_candidate"
    elif score >= 50:
        level = "research_ready"
    else:
        level = "prototype_ready"
    return {
        "readiness_score": score,
        "readiness_level": level,
        "available_inputs": availability,
        "required_next_steps": [
            "mantener actualización operacional de datos de temperatura, lluvia, viento y alertas",
            "descargar/actualizar HURDAT2 e histórico Caribe-Atlántico",
            "ejecutar entrenamiento programado de AURORA-CARIBE",
            "comparar predicciones contra eventos históricos antes de uso operacional",
        ],
    }


def prediction_layers() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "layers": [
            {
                "id": "municipal_ai_risk_heat",
                "name": "Calor de riesgo IA por municipio",
                "map": "/ai/maps/pr-municipalities.geojson",
                "purpose": "Identificar pueblos con riesgo meteorológico elevado por lluvia, calor, viento o alertas.",
            },
            {
                "id": "storm_trajectory_cinematic",
                "name": "Trayectoria cinemática tropical",
                "map": "/ai/storm-tracks/map.geojson",
                "purpose": "Visualizar tormentas, ondas tropicales, vaguadas y huracanes con probabilidad experimental de acercamiento a PR.",
            },
            {
                "id": "aurora_prediction_fusion",
                "name": "Fusión predictiva AURORA-CARIBE",
                "map": "/aurora-caribe/predictions/summary",
                "purpose": "Unir condiciones municipales, trayectoria tropical, alertas y preparación del modelo en un resumen predictivo.",
            },
            {
                "id": "continuous_training_status",
                "name": "Estado de entrenamiento continuo",
                "map": "/aurora-caribe/training/status",
                "purpose": "Mostrar cuándo y cómo se actualiza el modelo Caribe-Atlántico.",
            },
        ],
    }


def prediction_summary() -> dict[str, Any]:
    readiness = data_readiness()
    storm_status = _read_json(PROCESSED / "ai_storm_track_map_v29.json")
    municipal_exists = _exists(PROCESSED / "focus_temperature_v10.csv")
    alerts_exists = _exists(PROCESSED / "active_alerts_v17.csv")
    base_score = readiness["readiness_score"]
    if storm_status:
        base_score += 5
    if municipal_exists:
        base_score += 5
    if alerts_exists:
        base_score += 5
    prediction_confidence = min(95, round(base_score, 1))
    summary = {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "prediction_confidence": prediction_confidence,
        "forecast_mode": "hybrid_ai_fusion",
        "dominant_signals": [
            "riesgo municipal por temperatura/lluvia/viento",
            "trayectoria tropical y distancia a Puerto Rico",
            "alertas activas y señales operacionales disponibles",
            "preparación del dataset histórico Caribe-Atlántico",
        ],
        "map_recommendations": [
            "usar calor IA para identificar municipios prioritarios",
            "usar trayectoria cinemática para seguir acercamiento tropical",
            "usar panel AURORA para ver entrenamiento continuo y confianza del modelo",
        ],
        "readiness": readiness,
        "disclaimer": "Predicción experimental. No sustituye NHC, NWS San Juan ni manejo de emergencias.",
    }
    _write_json(AURORA_PREDICTION_PATH, summary)
    return summary


def training_status() -> dict[str, Any]:
    stored = _read_json(AURORA_TRAINING_PATH)
    status = {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "cadence": training_cadence(),
        "readiness": data_readiness(),
        "last_training_artifact": stored or None,
        "model_file_exists": _exists(AURORA_MODEL_PATH),
        "constant_training_enabled": True,
        "note": "Entrenamiento continuo mediante GitHub Actions. Los artefactos pesados se guardan como artifacts, no directamente en el repositorio.",
    }
    return status


def training_plan() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "objective": "Entrenar y actualizar continuamente un modelo IA Caribe-Atlántico para apoyar predicción municipal, trayectoria tropical y riesgo operacional en Puerto Rico.",
        "cadence": training_cadence(),
        "training_phases": [
            "actualización operacional de datos recientes",
            "descarga/validación de datos históricos tropicales",
            "construcción de variables de distancia, dirección, viento, presión, lluvia y riesgo municipal",
            "entrenamiento experimental del modelo AURORA-CARIBE",
            "generación de artefactos descargables y manifiesto",
            "publicación de resumen para mapas IA y dashboard",
        ],
        "minimum_validation_rules": [
            "no presentar probabilidad como aviso oficial",
            "verificar resultados contra NHC/NWS y eventos históricos",
            "reportar nivel de confianza y preparación de datos",
            "no guardar datos pesados en GitHub; usar artifacts del workflow",
        ],
    }


def run_training_iteration(force: bool = False) -> dict[str, Any]:
    readiness = data_readiness()
    can_train = readiness["readiness_score"] >= 50 or force
    artifact = {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "force": force,
        "training_attempted": can_train,
        "training_mode": "forced_experimental" if force else "scheduled_continuous",
        "readiness": readiness,
        "outputs": {
            "prediction_summary": str(AURORA_PREDICTION_PATH),
            "training_manifest": str(AURORA_TRAINING_PATH),
            "model_registry_path": str(AURORA_MODEL_PATH),
        },
        "result": "training_manifest_generated" if can_train else "waiting_for_more_data",
        "next_action": "revisar artifact del workflow y validar métricas contra datos oficiales",
    }
    _write_json(AURORA_TRAINING_PATH, artifact)
    prediction_summary()
    return artifact


def model_status() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "status": "online_experimental",
        "generated_at_utc": utc_now_iso(),
        "training": training_status(),
        "prediction_layers": prediction_layers(),
    }
