from __future__ import annotations

import math
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

AI_MAP_VERSION = "2.8.0"
AI_MAP_NAME = "PR-WX AI Interactive Municipal Maps"
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

PREDICTION_CANDIDATES = (
    PROCESSED / "live_predictions_v10.csv",
    PROCESSED / "focus_temperature_v10.csv",
    PROCESSED / "focus_municipalities_v8.csv",
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

# Coordenadas aproximadas de centroides municipales para visualizacion.
# No sustituye cartografia oficial; se usa para ubicar marcadores interactivos.
PR_MUNICIPAL_CENTROIDS: list[dict[str, Any]] = [
    {"municipality": "Adjuntas", "lat": 18.16, "lon": -66.72, "region": "montaña"},
    {"municipality": "Aguada", "lat": 18.38, "lon": -67.19, "region": "oeste"},
    {"municipality": "Aguadilla", "lat": 18.43, "lon": -67.15, "region": "noroeste"},
    {"municipality": "Aguas Buenas", "lat": 18.26, "lon": -66.10, "region": "metro-montaña"},
    {"municipality": "Aibonito", "lat": 18.14, "lon": -66.27, "region": "montaña"},
    {"municipality": "Añasco", "lat": 18.28, "lon": -67.14, "region": "oeste"},
    {"municipality": "Arecibo", "lat": 18.47, "lon": -66.72, "region": "norte"},
    {"municipality": "Arroyo", "lat": 17.97, "lon": -66.06, "region": "sur-este"},
    {"municipality": "Barceloneta", "lat": 18.45, "lon": -66.54, "region": "norte"},
    {"municipality": "Barranquitas", "lat": 18.19, "lon": -66.31, "region": "montaña"},
    {"municipality": "Bayamón", "lat": 18.37, "lon": -66.16, "region": "metro"},
    {"municipality": "Cabo Rojo", "lat": 18.09, "lon": -67.15, "region": "suroeste"},
    {"municipality": "Caguas", "lat": 18.23, "lon": -66.04, "region": "centro-este"},
    {"municipality": "Camuy", "lat": 18.48, "lon": -66.84, "region": "norte"},
    {"municipality": "Canóvanas", "lat": 18.38, "lon": -65.90, "region": "noreste"},
    {"municipality": "Carolina", "lat": 18.39, "lon": -65.96, "region": "metro-este"},
    {"municipality": "Cataño", "lat": 18.44, "lon": -66.12, "region": "metro"},
    {"municipality": "Cayey", "lat": 18.11, "lon": -66.17, "region": "montaña"},
    {"municipality": "Ceiba", "lat": 18.26, "lon": -65.65, "region": "este"},
    {"municipality": "Ciales", "lat": 18.29, "lon": -66.47, "region": "montaña-norte"},
    {"municipality": "Cidra", "lat": 18.18, "lon": -66.16, "region": "montaña"},
    {"municipality": "Coamo", "lat": 18.08, "lon": -66.36, "region": "sur-centro"},
    {"municipality": "Comerío", "lat": 18.22, "lon": -66.23, "region": "montaña"},
    {"municipality": "Corozal", "lat": 18.34, "lon": -66.32, "region": "norte-montaña"},
    {"municipality": "Culebra", "lat": 18.31, "lon": -65.30, "region": "isla municipio"},
    {"municipality": "Dorado", "lat": 18.46, "lon": -66.27, "region": "norte"},
    {"municipality": "Fajardo", "lat": 18.33, "lon": -65.65, "region": "este"},
    {"municipality": "Florida", "lat": 18.36, "lon": -66.56, "region": "norte"},
    {"municipality": "Guánica", "lat": 17.97, "lon": -66.91, "region": "suroeste"},
    {"municipality": "Guayama", "lat": 17.98, "lon": -66.11, "region": "sur"},
    {"municipality": "Guayanilla", "lat": 18.02, "lon": -66.79, "region": "sur"},
    {"municipality": "Guaynabo", "lat": 18.36, "lon": -66.11, "region": "metro"},
    {"municipality": "Gurabo", "lat": 18.25, "lon": -65.98, "region": "centro-este"},
    {"municipality": "Hatillo", "lat": 18.49, "lon": -66.83, "region": "norte"},
    {"municipality": "Hormigueros", "lat": 18.14, "lon": -67.13, "region": "oeste"},
    {"municipality": "Humacao", "lat": 18.15, "lon": -65.83, "region": "este"},
    {"municipality": "Isabela", "lat": 18.50, "lon": -67.02, "region": "noroeste"},
    {"municipality": "Jayuya", "lat": 18.22, "lon": -66.59, "region": "montaña"},
    {"municipality": "Juana Díaz", "lat": 18.05, "lon": -66.51, "region": "sur"},
    {"municipality": "Juncos", "lat": 18.23, "lon": -65.92, "region": "este-interior"},
    {"municipality": "Lajas", "lat": 18.05, "lon": -67.06, "region": "suroeste"},
    {"municipality": "Lares", "lat": 18.30, "lon": -66.88, "region": "montaña-oeste"},
    {"municipality": "Las Marías", "lat": 18.25, "lon": -66.99, "region": "oeste-montaña"},
    {"municipality": "Las Piedras", "lat": 18.19, "lon": -65.87, "region": "este-interior"},
    {"municipality": "Loíza", "lat": 18.43, "lon": -65.88, "region": "noreste"},
    {"municipality": "Luquillo", "lat": 18.37, "lon": -65.72, "region": "noreste"},
    {"municipality": "Manatí", "lat": 18.43, "lon": -66.49, "region": "norte"},
    {"municipality": "Maricao", "lat": 18.18, "lon": -66.98, "region": "montaña-oeste"},
    {"municipality": "Maunabo", "lat": 18.01, "lon": -65.90, "region": "sureste"},
    {"municipality": "Mayagüez", "lat": 18.20, "lon": -67.14, "region": "oeste"},
    {"municipality": "Moca", "lat": 18.39, "lon": -67.11, "region": "noroeste"},
    {"municipality": "Morovis", "lat": 18.32, "lon": -66.41, "region": "norte-montaña"},
    {"municipality": "Naguabo", "lat": 18.21, "lon": -65.74, "region": "este"},
    {"municipality": "Naranjito", "lat": 18.30, "lon": -66.24, "region": "centro-norte"},
    {"municipality": "Orocovis", "lat": 18.23, "lon": -66.39, "region": "montaña"},
    {"municipality": "Patillas", "lat": 18.00, "lon": -66.01, "region": "sureste"},
    {"municipality": "Peñuelas", "lat": 18.06, "lon": -66.72, "region": "sur"},
    {"municipality": "Ponce", "lat": 18.01, "lon": -66.61, "region": "sur"},
    {"municipality": "Quebradillas", "lat": 18.47, "lon": -66.94, "region": "norte"},
    {"municipality": "Rincón", "lat": 18.34, "lon": -67.25, "region": "oeste"},
    {"municipality": "Río Grande", "lat": 18.38, "lon": -65.84, "region": "noreste"},
    {"municipality": "Sabana Grande", "lat": 18.08, "lon": -66.96, "region": "suroeste"},
    {"municipality": "Salinas", "lat": 17.98, "lon": -66.30, "region": "sur"},
    {"municipality": "San Germán", "lat": 18.08, "lon": -67.04, "region": "suroeste"},
    {"municipality": "San Juan", "lat": 18.40, "lon": -66.06, "region": "metro"},
    {"municipality": "San Lorenzo", "lat": 18.19, "lon": -65.96, "region": "este-interior"},
    {"municipality": "San Sebastián", "lat": 18.34, "lon": -66.99, "region": "oeste-montaña"},
    {"municipality": "Santa Isabel", "lat": 17.97, "lon": -66.40, "region": "sur"},
    {"municipality": "Toa Alta", "lat": 18.39, "lon": -66.25, "region": "metro-oeste"},
    {"municipality": "Toa Baja", "lat": 18.44, "lon": -66.25, "region": "metro-oeste"},
    {"municipality": "Trujillo Alto", "lat": 18.35, "lon": -66.02, "region": "metro-este"},
    {"municipality": "Utuado", "lat": 18.27, "lon": -66.70, "region": "montaña"},
    {"municipality": "Vega Alta", "lat": 18.41, "lon": -66.33, "region": "norte"},
    {"municipality": "Vega Baja", "lat": 18.44, "lon": -66.39, "region": "norte"},
    {"municipality": "Vieques", "lat": 18.13, "lon": -65.44, "region": "isla municipio"},
    {"municipality": "Villalba", "lat": 18.13, "lon": -66.49, "region": "montaña-sur"},
    {"municipality": "Yabucoa", "lat": 18.06, "lon": -65.88, "region": "sureste"},
    {"municipality": "Yauco", "lat": 18.03, "lon": -66.86, "region": "suroeste"},
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_name(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


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


def _to_float(value: Any) -> float | None:
    try:
        n = float(value)
        if math.isfinite(n):
            return n
    except Exception:
        return None
    return None


def _prediction_lookup() -> tuple[dict[str, dict[str, Any]], str | None]:
    frame, path = _first_table(PREDICTION_CANDIDATES)
    lookup: dict[str, dict[str, Any]] = {}
    if not frame.empty and "municipality" in frame.columns:
        for _, row in frame.iterrows():
            item = row.to_dict()
            lookup[normalize_name(item.get("municipality"))] = item
    return lookup, path


def _alerts_lookup() -> tuple[dict[str, list[dict[str, Any]]], str | None]:
    frame, path = _first_table(ALERT_CANDIDATES)
    lookup: dict[str, list[dict[str, Any]]] = {}
    if not frame.empty:
        if "municipality" in frame.columns:
            for _, row in frame.iterrows():
                item = row.to_dict()
                lookup.setdefault(normalize_name(item.get("municipality")), []).append(item)
        else:
            rows = frame.head(20).to_dict(orient="records")
            for mun in PR_MUNICIPAL_CENTROIDS:
                lookup[normalize_name(mun["municipality"])] = rows
    return lookup, path


def _score(row: dict[str, Any], alerts: list[dict[str, Any]]) -> tuple[int, list[str], dict[str, Any]]:
    temp = _to_float(_first_value(row, "temp_f", "temperature_f", "base_temp_f", "forecast_temp_f"))
    feels = _to_float(_first_value(row, "feels_like_f", "heat_index_f", "base_heat_index_f"))
    rain = _to_float(_first_value(row, "forecast_precip_24h_in", "corrected_precip_24h_in", "base_precip_24h_in", "rain_in"))
    pop = _to_float(_first_value(row, "precip_probability_max", "probability_precipitation", "pop"))
    wind = _to_float(_first_value(row, "forecast_wind_speed_mph", "wind_speed_mph", "wind_mph"))
    gust = _to_float(_first_value(row, "forecast_wind_gust_mph", "wind_gust_mph", "gust_mph"))
    rh = _to_float(_first_value(row, "forecast_relative_humidity", "relative_humidity", "humidity"))
    base = _to_float(_first_value(row, "risk_score", "operational_risk_score", "impact_score"))

    score = 20 if base is None else max(0, min(100, int(round(base))))
    reasons: list[str] = []
    if feels is not None and feels >= 105:
        score += 18; reasons.append("sensación térmica muy alta")
    elif feels is not None and feels >= 100:
        score += 10; reasons.append("calor significativo")
    if temp is not None and temp >= 92:
        score += 8; reasons.append("temperatura elevada")
    if rain is not None and rain >= 3.0:
        score += 25; reasons.append("lluvia fuerte acumulada")
    elif rain is not None and rain >= 1.5:
        score += 15; reasons.append("lluvia moderada a fuerte")
    elif rain is not None and rain >= 0.5:
        score += 6; reasons.append("posibilidad de lluvia")
    if pop is not None and pop >= 70:
        score += 6; reasons.append("probabilidad de precipitación alta")
    if gust is not None and gust >= 40:
        score += 20; reasons.append("ráfagas peligrosas")
    elif wind is not None and wind >= 25:
        score += 10; reasons.append("viento elevado")
    if alerts:
        score += min(25, 8 + len(alerts) * 3); reasons.append("alertas activas o cercanas")
    score = max(0, min(100, int(score)))
    values = {"temperature_f": temp, "feels_like_f": feels, "rain_24h_in": rain, "pop_pct": pop, "wind_mph": wind, "gust_mph": gust, "humidity_pct": rh}
    return score, reasons, values


def _risk_level(score: int) -> str:
    if score >= 75:
        return "alto"
    if score >= 50:
        return "moderado"
    return "bajo"


def _confidence(row: dict[str, Any], alerts: list[dict[str, Any]], values: dict[str, Any]) -> str:
    count = sum(1 for value in values.values() if value is not None)
    if count >= 5 and alerts:
        return "alta"
    if count >= 3:
        return "media"
    if row:
        return "limitada"
    return "baja por falta de datos operacionales locales"


def _ai_text(name: str, region: str, level: str, reasons: list[str], confidence: str, values: dict[str, Any]) -> str:
    if not reasons:
        reasons = ["sin señales críticas detectadas en los datos disponibles"]
    rain = values.get("rain_24h_in")
    feels = values.get("feels_like_f")
    wind = values.get("wind_mph")
    parts = [f"Análisis IA experimental para {name} ({region}). El nivel de riesgo estimado es {level} con confianza {confidence}."]
    parts.append("Factores principales: " + ", ".join(reasons[:4]) + ".")
    if feels is not None:
        parts.append(f"La sensación térmica estimada es {feels:.1f} °F, por lo que se debe observar el riesgo de calor y deshidratación.")
    if rain is not None:
        parts.append(f"La lluvia estimada en 24 horas es {rain:.2f} pulgadas; en zonas urbanas, montañosas o de pobre drenaje puede aumentar el riesgo de acumulación de agua.")
    if wind is not None:
        parts.append(f"El viento estimado es {wind:.1f} mph; si hay ráfagas mayores, se recomienda asegurar objetos livianos.")
    parts.append("Use este mapa como apoyo analítico; las decisiones oficiales deben validarse con NWS San Juan, NHC y manejo de emergencias.")
    return " ".join(parts)


def _recommended_action(level: str, values: dict[str, Any], alerts: list[dict[str, Any]]) -> str:
    if level == "alto":
        return "Revisar alertas oficiales, evitar zonas inundables, limitar exposición al calor y preparar medidas de seguridad municipal."
    if level == "moderado":
        return "Monitorear cambios cada pocas horas, revisar drenajes y planificar actividades al aire libre con precaución."
    if alerts:
        return "Aunque el riesgo calculado es bajo, existen alertas; verifique detalles oficiales antes de tomar decisiones."
    return "Mantener monitoreo regular y verificar fuentes oficiales si cambian las condiciones."


def municipality_feature(mun: dict[str, Any], prediction: dict[str, Any], alerts: list[dict[str, Any]], prediction_path: str | None) -> dict[str, Any]:
    score, reasons, values = _score(prediction, alerts)
    level = _risk_level(score)
    confidence = _confidence(prediction, alerts, values)
    name = mun["municipality"]
    props = {
        "municipality": name,
        "region": mun["region"],
        "risk_score": score,
        "risk_level": level,
        "confidence": confidence,
        "ai_analysis": _ai_text(name, mun["region"], level, reasons, confidence, values),
        "recommended_action": _recommended_action(level, values, alerts),
        "reasons": reasons,
        "conditions": values,
        "alert_count": len(alerts),
        "alerts": alerts[:5],
        "data_status": "operational_data_found" if prediction else "fallback_no_municipal_forecast_found",
        "source_file": prediction_path,
    }
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [mun["lon"], mun["lat"]]},
        "properties": props,
    }


def pr_ai_map_payload() -> dict[str, Any]:
    predictions, prediction_path = _prediction_lookup()
    alerts, alerts_path = _alerts_lookup()
    features = []
    for mun in PR_MUNICIPAL_CENTROIDS:
        key = normalize_name(mun["municipality"])
        features.append(municipality_feature(mun, predictions.get(key, {}), alerts.get(key, []), prediction_path))
    scores = [f["properties"]["risk_score"] for f in features]
    levels = [f["properties"]["risk_level"] for f in features]
    return {
        "type": "FeatureCollection",
        "name": AI_MAP_NAME,
        "version": AI_MAP_VERSION,
        "generated_at_utc": utc_now_iso(),
        "features": features,
        "summary": {
            "municipalities": len(features),
            "average_risk_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "high_risk": levels.count("alto"),
            "moderate_risk": levels.count("moderado"),
            "low_risk": levels.count("bajo"),
            "prediction_source": prediction_path,
            "alert_source": alerts_path,
            "map_type": "interactive_point_centroid_map",
            "cartography_note": "Centroides aproximados para visualizacion; no es una capa GIS oficial.",
        },
        "disclaimer": "Mapa IA experimental. No sustituye pronosticos, avisos ni advertencias oficiales de NOAA/NWS/NHC ni manejo de emergencias.",
    }


def municipality_analysis(name: str) -> dict[str, Any]:
    payload = pr_ai_map_payload()
    key = normalize_name(name)
    for feature in payload["features"]:
        if normalize_name(feature["properties"]["municipality"]) == key:
            return feature
    raise KeyError(name)


def map_layers() -> list[dict[str, Any]]:
    return [
        {"id": "risk_score", "label": "Riesgo IA", "description": "Puntuacion 0-100 integrada por calor, lluvia, viento, alertas y disponibilidad de datos."},
        {"id": "heat", "label": "Calor", "description": "Temperatura y sensacion termica cuando estan disponibles."},
        {"id": "rain", "label": "Lluvia", "description": "Lluvia estimada o corregida a 24 horas cuando existe en el producto operacional."},
        {"id": "wind", "label": "Viento", "description": "Viento y rafagas estimadas por municipio cuando existen en los datos."},
        {"id": "alerts", "label": "Alertas", "description": "Alertas activas o asociadas al municipio cuando estan disponibles."},
        {"id": "confidence", "label": "Confianza", "description": "Indicador cualitativo basado en cantidad de variables disponibles y alertas."},
    ]


def status() -> dict[str, Any]:
    payload = pr_ai_map_payload()
    return {
        "status": "ok",
        "engine": AI_MAP_NAME,
        "version": AI_MAP_VERSION,
        "municipalities": payload["summary"]["municipalities"],
        "prediction_source": payload["summary"].get("prediction_source"),
        "alert_source": payload["summary"].get("alert_source"),
        "endpoints": {
            "map": "/ai/maps/pr-municipalities",
            "geojson": "/ai/maps/pr-municipalities.geojson",
            "summary": "/ai/maps/summary",
            "municipality": "/ai/maps/municipality/{municipality}",
            "layers": "/ai/maps/layers",
        },
        "disclaimer": payload["disclaimer"],
    }
