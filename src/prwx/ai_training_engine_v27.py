from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from prwx.caribbean_model_v20 import MODEL_NAME, MODEL_VERSION, TARGET_SPECS, select_features, train_caribbean_model
from prwx.caribbean_sources import source_registry

AI_ENGINE_VERSION = "2.7.0"
AI_ENGINE_NAME = "PR-WX AI Caribbean-Atlantic Trainer"

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TRAINING = ROOT / "data" / "training"
MODELS = ROOT / "models"

TRAINING_CANDIDATES = (
    TRAINING / "pr_caribbean_atlantic_training.parquet",
    TRAINING / "pr_caribbean_atlantic_training.csv",
    TRAINING / "pr_caribbean_training.parquet",
    TRAINING / "pr_caribbean_training.csv",
)

AI_MODEL_PATH = MODELS / "pr_caribe_atlantic_ai_v27.joblib"
AI_ANALYSIS_PATH = PROCESSED / "ai_model_analysis_v27.json"
AI_TRAINING_REPORT_PATH = PROCESSED / "ai_training_report_v27.json"
AI_TRAINING_PLAN_PATH = PROCESSED / "ai_training_plan_v27.md"

REQUIRED_REGION_FIELDS = ("lat", "lon", "valid_time_utc")
TARGET_GROUPS = {
    "temperature": ("observed_temp_f",),
    "rainfall": ("observed_precip_1h_in", "observed_precip_6h_in", "observed_precip_24h_in"),
    "wind": ("observed_wind_speed_mph", "observed_wind_gust_mph"),
    "moisture_pressure": ("observed_relative_humidity", "observed_pressure_hpa"),
}


@dataclass
class AIReadiness:
    rows: int
    columns: int
    stations: int
    territories: int
    span_days: int
    usable_features: int
    trainable_targets: int
    missing_required_fields: list[str]
    leakage_risk_columns: list[str]
    duplicate_rows: int
    missing_rate: float
    research_ready: bool
    operational_candidate: bool
    production_validated: bool
    recommendation: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_training_table(path: str | Path | None = None) -> tuple[pd.DataFrame, str | None]:
    candidates = (Path(path),) if path else TRAINING_CANDIDATES
    for candidate in candidates:
        try:
            if not candidate.exists() or candidate.stat().st_size == 0:
                continue
            if candidate.suffix.lower() == ".parquet":
                return pd.read_parquet(candidate), str(candidate)
            return pd.read_csv(candidate), str(candidate)
        except Exception:
            continue
    return pd.DataFrame(), None


def _span_days(df: pd.DataFrame) -> int:
    date_col = next((c for c in ("valid_time_utc", "timestamp_utc", "date", "time") if c in df.columns), None)
    if not date_col or df.empty:
        return 0
    dates = pd.to_datetime(df[date_col], errors="coerce", utc=True).dropna()
    if dates.empty:
        return 0
    return max(0, int((dates.max() - dates.min()).total_seconds() // 86400))


def _nunique(df: pd.DataFrame, candidates: tuple[str, ...]) -> int:
    col = next((c for c in candidates if c in df.columns), None)
    if not col or df.empty:
        return 0
    return int(df[col].nunique(dropna=True))


def _missing_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 1.0
    return float(df.isna().mean().mean())


def _trainable_target_count(df: pd.DataFrame) -> int:
    count = 0
    for target in TARGET_SPECS:
        if target in df.columns and pd.to_numeric(df[target], errors="coerce").notna().sum() >= 20:
            count += 1
    return count


def _leakage_columns(df: pd.DataFrame) -> list[str]:
    risky_prefixes = ("future_", "verified_", "target_", "error_")
    risky: list[str] = []
    for col in df.columns:
        lowered = col.casefold()
        if lowered.startswith(risky_prefixes):
            risky.append(col)
    return risky[:50]


def analyze_training_dataset(df: pd.DataFrame) -> AIReadiness:
    if df.empty:
        return AIReadiness(
            rows=0,
            columns=0,
            stations=0,
            territories=0,
            span_days=0,
            usable_features=0,
            trainable_targets=0,
            missing_required_fields=list(REQUIRED_REGION_FIELDS),
            leakage_risk_columns=[],
            duplicate_rows=0,
            missing_rate=1.0,
            research_ready=False,
            operational_candidate=False,
            production_validated=False,
            recommendation="Debe construir primero el dataset histórico con observaciones y pronósticos archivados del Caribe y Atlántico.",
        )

    usable_features = len(select_features(df))
    target_count = _trainable_target_count(df)
    span = _span_days(df)
    stations = _nunique(df, ("station_id", "location_id", "grid_id"))
    territories = _nunique(df, ("territory", "island", "country", "basin"))
    missing_required = [field for field in REQUIRED_REGION_FIELDS if field not in df.columns]
    duplicates = int(df.duplicated().sum())
    missing = _missing_rate(df)

    research_ready = (
        len(df) >= 5000
        and span >= 90
        and stations >= 8
        and usable_features >= 12
        and target_count >= 2
        and missing < 0.45
        and not missing_required
    )
    operational_candidate = (
        len(df) >= 50000
        and span >= 365
        and stations >= 25
        and territories >= 5
        and usable_features >= 25
        and target_count >= 4
        and missing < 0.35
        and not missing_required
    )
    if operational_candidate:
        recommendation = "Dataset candidato para entrenamiento operacional experimental; todavía requiere backtesting independiente y revisión meteorológica."
    elif research_ready:
        recommendation = "Dataset listo para entrenamiento investigativo; ampliar cobertura regional y eventos extremos antes de producción."
    else:
        recommendation = "Dataset insuficiente para entrenamiento confiable; completar backfill histórico, fuentes oficiales y validación temporal."

    return AIReadiness(
        rows=int(len(df)),
        columns=int(len(df.columns)),
        stations=stations,
        territories=territories,
        span_days=span,
        usable_features=usable_features,
        trainable_targets=target_count,
        missing_required_fields=missing_required,
        leakage_risk_columns=_leakage_columns(df),
        duplicate_rows=duplicates,
        missing_rate=round(missing, 4),
        research_ready=research_ready,
        operational_candidate=operational_candidate,
        production_validated=False,
        recommendation=recommendation,
    )


def feature_matrix_catalog() -> list[dict[str, Any]]:
    categories = [
        {
            "category": "atmósfera global",
            "prefixes": ["gfs_", "gefs_"],
            "examples": ["gfs_temp_2m_f", "gfs_wind_10m_mph", "gefs_precip_p90_in"],
            "purpose": "capturar patrón sinóptico, incertidumbre y lluvia regional",
        },
        {
            "category": "alta resolución Puerto Rico",
            "prefixes": ["nam_pr_", "nws_", "tjua_", "mrms_"],
            "examples": ["nam_pr_precip_3h_in", "nws_temp_grid_f", "mrms_qpe_1h_in"],
            "purpose": "corregir microclimas, convección local, lluvia extrema y efectos de topografía",
        },
        {
            "category": "satélite y humedad tropical",
            "prefixes": ["goes_", "pw_", "dust_", "sst_"],
            "examples": ["goes_cloud_top_temp_c", "pw_total_inches", "sst_anomaly_c"],
            "purpose": "identificar ondas tropicales, aire seco, polvo del Sahara y combustible oceánico",
        },
        {
            "category": "ciclones y océano",
            "prefixes": ["nhc_", "hafs_", "gfs_wave_", "ndbc_"],
            "examples": ["nhc_distance_to_track_km", "hafs_max_wind_kt", "gfs_wave_height_ft"],
            "purpose": "riesgo tropical, oleaje, viento costero y marejadas",
        },
        {
            "category": "estática geográfica",
            "prefixes": ["lat", "lon", "elevation_m", "distance_to_coast_km", "slope_deg"],
            "examples": ["elevation_m", "coastal", "land_fraction"],
            "purpose": "ajuste por isla, costa, valle, montaña y exposición marítima",
        },
    ]
    return categories


def ai_training_plan(readiness: AIReadiness | None = None) -> dict[str, Any]:
    readiness_payload = asdict(readiness) if readiness else None
    return {
        "engine": AI_ENGINE_NAME,
        "version": AI_ENGINE_VERSION,
        "base_model": {"name": MODEL_NAME, "version": MODEL_VERSION},
        "generated_at_utc": utc_now_iso(),
        "readiness": readiness_payload,
        "ai_strategy": {
            "approach": "AutoML supervisado con ensamble multiobjetivo y validación cronológica",
            "members": ["Ridge", "RandomForest", "ExtraTrees", "HistGradientBoosting"],
            "targets": list(TARGET_SPECS.keys()),
            "uncertainty": "p10, media y p90 derivados del desacuerdo entre miembros del ensamble",
            "validation": "split cronológico, backtesting por eventos extremos y evaluación por región/estación",
        },
        "minimum_operational_dataset": {
            "rows": 50000,
            "span_days": 365,
            "stations_or_grid_points": 25,
            "territories_or_subregions": 5,
            "trainable_targets": 4,
            "independent_validation": True,
        },
        "steps": [
            "Recolectar observaciones históricas de estaciones, radar, boyas y reanálisis.",
            "Recolectar pronósticos archivados GFS, GEFS, NAM Puerto Rico Nest, HAFS/NHC, oleaje y satélite.",
            "Alinear cada pronóstico con observaciones verificadas por tiempo, punto y horizonte.",
            "Crear variables de topografía, costa, SST, humedad precipitable, polvo, ciclón y estación del año.",
            "Ejecutar análisis IA de calidad, datos faltantes, duplicados, fuga de información y cobertura regional.",
            "Entrenar ensamble multiobjetivo y calcular error, sesgo, RMSE, MAE, R² y percentiles de incertidumbre.",
            "Validar por eventos extremos: lluvia urbana, calor, vientos, ciclones, marejadas y episodios de polvo del Sahara.",
            "Publicar solo como experimental hasta que una revisión meteorológica confirme desempeño operacional.",
        ],
        "official_sources": source_registry(),
    }


def plan_as_markdown(plan: dict[str, Any]) -> str:
    readiness = plan.get("readiness") or {}
    lines = [
        "# PR-WX v2.7 - Inteligencia Artificial para el Caribe y el Atlántico",
        "",
        f"Generado: {plan.get('generated_at_utc')}",
        "",
        "## Estrategia IA",
        "",
        f"Enfoque: {plan['ai_strategy']['approach']}.",
        f"Modelos miembros: {', '.join(plan['ai_strategy']['members'])}.",
        f"Incertidumbre: {plan['ai_strategy']['uncertainty']}.",
        "",
        "## Estado del dataset",
        "",
        f"Filas: {readiness.get('rows', 0)}",
        f"Columnas: {readiness.get('columns', 0)}",
        f"Estaciones/puntos: {readiness.get('stations', 0)}",
        f"Territorios/subregiones: {readiness.get('territories', 0)}",
        f"Días de cobertura: {readiness.get('span_days', 0)}",
        f"Variables útiles: {readiness.get('usable_features', 0)}",
        f"Objetivos entrenables: {readiness.get('trainable_targets', 0)}",
        f"Recomendación: {readiness.get('recommendation', 'Pendiente')}",
        "",
        "## Pasos operacionales",
        "",
    ]
    for i, step in enumerate(plan.get("steps", []), start=1):
        lines.append(f"{i}. {step}")
    lines.extend([
        "",
        "## Nota",
        "",
        "Este módulo no sustituye a NOAA/NWS/NHC ni a las agencias de manejo de emergencias. El entrenamiento IA es experimental hasta completar validación independiente.",
    ])
    return "\n".join(lines) + "\n"


def save_ai_analysis_assets(dataset_path: str | Path | None = None) -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df, path = read_training_table(dataset_path)
    readiness = analyze_training_dataset(df)
    plan = ai_training_plan(readiness)
    payload = {
        "engine": AI_ENGINE_NAME,
        "version": AI_ENGINE_VERSION,
        "generated_at_utc": utc_now_iso(),
        "dataset_path": path,
        "readiness": asdict(readiness),
        "feature_matrix": feature_matrix_catalog(),
        "plan": plan,
    }
    AI_ANALYSIS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    AI_TRAINING_PLAN_PATH.write_text(plan_as_markdown(plan), encoding="utf-8")
    return payload


def train_ai_model_if_ready(dataset_path: str | Path | None = None, *, force: bool = False) -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    df, path = read_training_table(dataset_path)
    readiness = analyze_training_dataset(df)
    if not readiness.research_ready and not force:
        result = {
            "status": "not_trained",
            "reason": readiness.recommendation,
            "dataset_path": path,
            "readiness": asdict(readiness),
            "force_available": True,
            "warning": "No se entrenó porque el dataset todavía no cumple criterios mínimos de investigación.",
        }
        AI_TRAINING_REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    bundle, report = train_caribbean_model(df)
    joblib.dump(bundle, AI_MODEL_PATH)
    result = {
        "status": "trained_research_candidate",
        "model_path": str(AI_MODEL_PATH),
        "dataset_path": path,
        "trained_at_utc": utc_now_iso(),
        "engine": AI_ENGINE_NAME,
        "version": AI_ENGINE_VERSION,
        "readiness": asdict(readiness),
        "training_report": report,
        "production_validated": False,
        "disclaimer": "Modelo entrenado para investigación. Requiere validación independiente antes de uso operacional.",
    }
    AI_TRAINING_REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_ai_analysis() -> dict[str, Any]:
    if AI_ANALYSIS_PATH.exists() and AI_ANALYSIS_PATH.stat().st_size:
        try:
            return json.loads(AI_ANALYSIS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return save_ai_analysis_assets()


def load_training_report() -> dict[str, Any]:
    if AI_TRAINING_REPORT_PATH.exists() and AI_TRAINING_REPORT_PATH.stat().st_size:
        try:
            return json.loads(AI_TRAINING_REPORT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    analysis = load_ai_analysis()
    return {
        "status": "not_trained",
        "reason": analysis.get("readiness", {}).get("recommendation", "Dataset pendiente"),
        "model_path": str(AI_MODEL_PATH),
        "model_file_exists": AI_MODEL_PATH.exists(),
        "analysis": analysis,
    }
