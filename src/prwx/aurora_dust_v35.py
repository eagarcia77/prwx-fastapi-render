from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "3.5.0"
MODEL_CODE = "AURORA-SAHARA"
MODEL_NAME = "AURORA Sahara-Caribe"
MODEL_FULL_NAME = "AURORA Sahara-Caribe Dust and Aerosol Intelligence"
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TRAINING = ROOT / "data" / "training"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

DUST_STATUS_PATH = PROCESSED / "aurora_sahara_dust_status_v35.json"
DUST_ANALYSIS_PATH = PROCESSED / "aurora_sahara_dust_analysis_v35.json"
DUST_GEOJSON_PATH = PROCESSED / "aurora_sahara_dust_map_v35.geojson"
DUST_TRAINING_PATH = PROCESSED / "aurora_sahara_dust_training_v35.json"
DUST_MODEL_PATH = MODELS / "aurora_sahara_dust_ai_v35.joblib"

DUST_DATA_CANDIDATES = (
    PROCESSED / "saharan_dust_observations.csv",
    PROCESSED / "cams_aerosol_forecast.csv",
    PROCESSED / "aerosol_dust_forecast.csv",
    PROCESSED / "air_quality_pm25.csv",
    TRAINING / "saharan_dust_caribbean_training.csv",
)

PR_TOWNS = [
    {"name": "San Juan", "lat": 18.4655, "lon": -66.1057, "population_weight": 1.0, "coastal": True},
    {"name": "Ponce", "lat": 18.0111, "lon": -66.6141, "population_weight": 0.72, "coastal": True},
    {"name": "Juana Díaz", "lat": 18.0525, "lon": -66.5063, "population_weight": 0.42, "coastal": False},
    {"name": "San Germán", "lat": 18.0816, "lon": -67.0449, "population_weight": 0.38, "coastal": False},
    {"name": "Fajardo", "lat": 18.3258, "lon": -65.6524, "population_weight": 0.44, "coastal": True},
    {"name": "Mayagüez", "lat": 18.2011, "lon": -67.1396, "population_weight": 0.56, "coastal": True},
    {"name": "Arecibo", "lat": 18.4724, "lon": -66.7157, "population_weight": 0.50, "coastal": True},
    {"name": "Caguas", "lat": 18.2341, "lon": -66.0485, "population_weight": 0.78, "coastal": False},
]

DUST_CORRIDORS = [
    {
        "id": "sahara_atlantic_core",
        "name": "Corredor principal Sahara-Atlántico-Caribe",
        "coordinates": [[-22.0, 17.0], [-35.0, 16.0], [-48.0, 15.3], [-58.0, 16.2], [-66.2, 18.1]],
        "context": "Ruta climatológica de polvo mineral desde África occidental hacia el Caribe oriental.",
    },
    {
        "id": "sal_north_edge",
        "name": "Borde norte de la Capa de Aire del Sahara",
        "coordinates": [[-30.0, 22.0], [-44.0, 21.5], [-57.5, 20.8], [-66.0, 19.2]],
        "context": "Borde seco y polvoriento que puede reducir nubosidad y visibilidad regional.",
    },
    {
        "id": "deep_caribbean_dust",
        "name": "Corredor sur Caribe-profundo",
        "coordinates": [[-38.0, 10.0], [-50.0, 11.0], [-61.5, 13.0], [-68.0, 15.0]],
        "context": "Entrada baja del polvo hacia el Caribe, con posible mezcla con humedad tropical.",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        if not path.exists() or path.stat().st_size == 0:
            return []
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        n = float(value)
        return n if math.isfinite(n) else default
    except Exception:
        return default


def source_catalog() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "official_and_scientific_sources": [
            {
                "id": "nasa_worldview_merra2",
                "name": "NASA Worldview / MERRA-2 aerosol and dust layers",
                "use": "AOD, dust surface mass concentration, PM2.5 dust context and visual plume validation.",
                "priority": "high",
            },
            {
                "id": "noaa_goes_east",
                "name": "NOAA/NESDIS GOES-East imagery",
                "use": "True color, dust RGB and Caribbean/Puerto Rico satellite monitoring.",
                "priority": "high",
            },
            {
                "id": "cams_global",
                "name": "Copernicus Atmosphere Monitoring Service global forecasts",
                "use": "Desert dust AOD, total aerosol optical depth and atmospheric-composition forecast guidance.",
                "priority": "high",
            },
            {
                "id": "epa_airnow_pm25",
                "name": "EPA AirNow / local PM2.5 observations when available",
                "use": "Ground-level air-quality verification and health-risk adjustment.",
                "priority": "medium",
            },
            {
                "id": "nws_sju",
                "name": "NWS San Juan discussions and official statements",
                "use": "Operational context for visibility, haze, respiratory impacts and official messaging.",
                "priority": "safety",
            },
        ],
        "candidate_files": [str(path) for path in DUST_DATA_CANDIDATES],
    }


def model_identity() -> dict[str, Any]:
    return {
        "model_code": MODEL_CODE,
        "model_name": MODEL_NAME,
        "full_name": MODEL_FULL_NAME,
        "version": VERSION,
        "parent_model": "AURORA Caribe-Atlántico",
        "focus": "Polvo del Sahara, aerosoles, bruma, PM2.5, visibilidad y riesgo respiratorio experimental para Puerto Rico y el Caribe.",
        "status": "experimental_operational_support",
        "warning_policy": "No sustituye AirNow, NWS San Juan, NHC, NOAA, NASA ni autoridades de salud o manejo de emergencias.",
    }


def _available_rows() -> tuple[list[dict[str, Any]], str | None]:
    for path in DUST_DATA_CANDIDATES:
        rows = _read_csv(path)
        if rows:
            return rows, str(path)
    return [], None


def _risk_level(score: float) -> str:
    if score >= 70:
        return "alto"
    if score >= 42:
        return "moderado"
    return "bajo"


def _synthetic_dust_index(town: dict[str, Any]) -> dict[str, Any]:
    lon_factor = max(0.0, min(1.0, (float(town["lon"]) + 68.0) / 3.0))
    coastal_boost = 6 if town.get("coastal") else 0
    population_boost = float(town.get("population_weight", 0.5)) * 8
    base = 28 + 18 * lon_factor + coastal_boost + population_boost
    score = max(0, min(100, round(base, 1)))
    aod = round(0.12 + (score / 100) * 0.42, 3)
    pm25 = round(8 + (score / 100) * 22, 1)
    visibility = round(max(3, 12 - (score / 100) * 6.5), 1)
    return {"score": score, "aod": aod, "pm25": pm25, "visibility_mi": visibility}


def _score_from_observation(row: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    aod = _num(row.get("aod") or row.get("dust_aod") or row.get("aerosol_optical_depth"), fallback["aod"])
    pm25 = _num(row.get("pm25") or row.get("pm2_5") or row.get("pm25_ug_m3"), fallback["pm25"])
    visibility = _num(row.get("visibility_mi") or row.get("visibility"), fallback["visibility_mi"])
    dust_surface = _num(row.get("dust_surface_mass") or row.get("dust_mass_concentration"), 0.0)
    score = (min(aod, 1.2) / 1.2) * 42 + (min(pm25, 55) / 55) * 38 + (max(0, 10 - min(visibility, 10)) / 10) * 12 + min(dust_surface, 250) / 250 * 8
    return {"score": round(max(0, min(100, score)), 1), "aod": round(aod, 3), "pm25": round(pm25, 1), "visibility_mi": round(visibility, 1)}


def dust_analysis() -> dict[str, Any]:
    cached = _read_json(DUST_ANALYSIS_PATH)
    if cached:
        return cached
    rows, source_path = _available_rows()
    row_lookup = {str(r.get("municipality") or r.get("name") or "").casefold(): r for r in rows}
    towns: list[dict[str, Any]] = []
    for town in PR_TOWNS:
        fallback = _synthetic_dust_index(town)
        obs = row_lookup.get(str(town["name"]).casefold(), {})
        metrics = _score_from_observation(obs, fallback) if obs else fallback
        level = _risk_level(metrics["score"])
        towns.append(
            {
                "municipality": town["name"],
                "lat": town["lat"],
                "lon": town["lon"],
                "dust_risk_score": metrics["score"],
                "dust_risk_level": level,
                "aod_550nm": metrics["aod"],
                "estimated_pm25_ug_m3": metrics["pm25"],
                "visibility_mi": metrics["visibility_mi"],
                "respiratory_risk": "elevado" if level == "alto" else "precaución" if level == "moderado" else "bajo",
                "ai_summary": f"{MODEL_NAME} estima riesgo {level} de polvo/aerosoles para {town['name']} con AOD {metrics['aod']} y PM2.5 estimado {metrics['pm25']} µg/m³.",
                "recommendation": _recommendation(level),
            }
        )
    max_town = max(towns, key=lambda item: item["dust_risk_score"]) if towns else None
    payload = {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "source_path": source_path,
        "mode": "observational_or_synthetic_readiness" if source_path else "synthetic_readiness_until_live_dust_data_loaded",
        "municipality_count": len(towns),
        "highest_risk_municipality": max_town,
        "regional_summary": _regional_summary(towns),
        "towns": towns,
        "corridors": DUST_CORRIDORS,
        "disclaimer": "Análisis experimental. Confirmar calidad del aire y avisos oficiales con agencias competentes.",
    }
    return payload


def _recommendation(level: str) -> str:
    if level == "alto":
        return "Reducir exposición prolongada al aire libre, vigilar personas con asma/EPOC y validar PM2.5 con fuentes oficiales."
    if level == "moderado":
        return "Monitorear visibilidad y síntomas respiratorios; considerar actividades bajo techo para personas sensibles."
    return "Mantener monitoreo; condiciones estimadas de polvo en rango bajo o manejable."


def _regional_summary(towns: list[dict[str, Any]]) -> str:
    if not towns:
        return "No hay municipios disponibles para análisis de polvo."
    avg = sum(t["dust_risk_score"] for t in towns) / len(towns)
    level = _risk_level(avg)
    return f"AURORA Sahara-Caribe estima un nivel regional {level} de polvo/aerosoles con puntuación promedio {avg:.1f}/100 para pueblos prioritarios de Puerto Rico."


def dust_geojson() -> dict[str, Any]:
    analysis = dust_analysis()
    features: list[dict[str, Any]] = []
    for corridor in DUST_CORRIDORS:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": corridor["coordinates"]},
                "properties": {"kind": "dust_corridor", "name": corridor["name"], "context": corridor["context"], "risk_level": "moderado"},
            }
        )
    for town in analysis.get("towns", []):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [town["lon"], town["lat"]]},
                "properties": {"kind": "dust_municipality", **town},
            }
        )
    return {"type": "FeatureCollection", "model": model_identity(), "generated_at_utc": utc_now_iso(), "features": features}


def health_guidance() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "general_guidance": [
            "Personas con asma, EPOC, alergias severas, condiciones cardiovasculares, adultos mayores, niños y embarazadas deben vigilar síntomas cuando el riesgo de polvo sube.",
            "Validar PM2.5 y avisos oficiales antes de cancelar clases, eventos o actividades laborales.",
            "En riesgo alto, considerar interiores, filtración de aire, hidratación, medicamentos recetados al día y reducir ejercicios intensos al aire libre.",
        ],
        "institutional_use": "Úsese como apoyo para decisiones preventivas de educación en línea, eventos universitarios y comunicaciones internas, no como aviso médico u oficial.",
    }


def training_plan() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "objective": "Entrenar AURORA Sahara-Caribe para estimar llegada, intensidad, duración e impacto municipal del polvo del Sahara y aerosoles relacionados.",
        "target_variables": [
            "dust_risk_score_0_100",
            "aod_550nm_next_24h_48h_72h",
            "pm25_estimated_or_observed",
            "visibility_reduction",
            "respiratory_sensitive_group_risk",
        ],
        "features": [
            "GOES true color / dust RGB / aerosol proxy",
            "CAMS desert dust AOD and total aerosol optical depth",
            "NASA MERRA-2 dust surface mass concentration",
            "PM2.5 observations where available",
            "wind direction/speed, precipitable water, humidity and stability",
            "municipal exposure, coast/inland classification and population sensitivity proxy",
        ],
        "schedule": "GitHub Actions cada 6 horas y ejecución manual cuando se suban nuevos datos.",
        "minimum_research_dataset": {"rows": 5000, "days": 90, "events": 10, "municipalities": 8},
        "minimum_operational_candidate": {"rows": 50000, "days": 365, "events": 40, "municipalities": 25},
        "safety_rule": "No emitir avisos oficiales; mostrar incertidumbre y validar con fuentes oficiales.",
    }


def training_status() -> dict[str, Any]:
    rows, source_path = _available_rows()
    status = {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "dataset_source": source_path,
        "rows_available": len(rows),
        "model_artifact_exists": DUST_MODEL_PATH.exists(),
        "research_ready": len(rows) >= 5000,
        "operational_candidate": len(rows) >= 50000,
        "workflow": ".github/workflows/aurora-sahara-dust-continuous-training-v35.yml",
        "artifact_name": "aurora-sahara-dust-training-v35",
    }
    return status


def status() -> dict[str, Any]:
    analysis = dust_analysis()
    return {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "analysis_available": bool(analysis.get("towns")),
        "training_status": training_status(),
        "sources": source_catalog(),
        "endpoints": {
            "status": "/aurora-caribe/dust/status",
            "analysis": "/aurora-caribe/dust/analysis",
            "map_geojson": "/aurora-caribe/dust/map.geojson",
            "sources": "/aurora-caribe/dust/sources",
            "training_plan": "/aurora-caribe/dust/training/plan",
            "training_status": "/aurora-caribe/dust/training/status",
            "health_guidance": "/aurora-caribe/dust/health-guidance",
        },
    }


def generate_artifacts() -> dict[str, Any]:
    analysis = dust_analysis()
    geojson = dust_geojson()
    training = training_status()
    _write_json(DUST_ANALYSIS_PATH, analysis)
    _write_json(DUST_GEOJSON_PATH, geojson)
    _write_json(DUST_TRAINING_PATH, training)
    _write_json(DUST_STATUS_PATH, status())
    return {
        "status": "generated",
        "model": model_identity(),
        "files": [str(DUST_ANALYSIS_PATH), str(DUST_GEOJSON_PATH), str(DUST_TRAINING_PATH), str(DUST_STATUS_PATH)],
    }
