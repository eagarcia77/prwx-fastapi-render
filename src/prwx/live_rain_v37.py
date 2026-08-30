from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

VERSION = "3.7.0"
MODEL_CODE = "AURORA-RAIN"
MODEL_NAME = "AURORA RainCast PR"
MODEL_FULL_NAME = "AURORA RainCast Puerto Rico Live Rain and Flood Intelligence"

NWS_ALERTS_PR = "https://api.weather.gov/alerts/active?area=PR"
NOAA_RADAR_MAPSERVER = "https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity/MapServer"
NOAA_RADAR_TIME_IMAGESERVER = "https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity_time/ImageServer"
NOAA_MRMS_QPE_IMAGESERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"
NOAA_RFC_QPE_MAPSERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/rfc_qpe/MapServer"
WPC_QPF_MAPSERVER = "https://mapservices.weather.noaa.gov/vector/rest/services/precip/wpc_qpf/MapServer"

PR_TOWNS = [
    {"name": "San Juan", "lat": 18.4655, "lon": -66.1057, "risk_weight": 1.0, "region": "Metro/Norte"},
    {"name": "Ponce", "lat": 18.0111, "lon": -66.6141, "risk_weight": 0.82, "region": "Sur"},
    {"name": "Juana Díaz", "lat": 18.0525, "lon": -66.5063, "risk_weight": 0.76, "region": "Sur central"},
    {"name": "San Germán", "lat": 18.0816, "lon": -67.0449, "risk_weight": 0.68, "region": "Oeste interior"},
    {"name": "Mayagüez", "lat": 18.2011, "lon": -67.1396, "risk_weight": 0.72, "region": "Oeste"},
    {"name": "Fajardo", "lat": 18.3258, "lon": -65.6524, "risk_weight": 0.70, "region": "Este"},
    {"name": "Arecibo", "lat": 18.4724, "lon": -66.7157, "risk_weight": 0.66, "region": "Norte"},
    {"name": "Caguas", "lat": 18.2341, "lon": -66.0485, "risk_weight": 0.78, "region": "Interior este"},
]

FLOOD_RAIN_PATTERNS = re.compile(r"flood|inund|lluv|rain|hydrologic|aguacero|flash", re.IGNORECASE)
HIGH_RISK_PATTERNS = re.compile(r"flash flood warning|flash flood|inundaci[oó]n repentina|flood warning", re.IGNORECASE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def model_identity() -> dict[str, Any]:
    return {
        "model_code": MODEL_CODE,
        "model_name": MODEL_NAME,
        "full_name": MODEL_FULL_NAME,
        "version": VERSION,
        "scope": "Puerto Rico, radar en vivo, lluvia observada, QPE, QPF y alertas de inundación/lluvia",
        "status": "experimental_operational_support",
        "official_warning_policy": "No emite avisos oficiales. Validar siempre con NWS San Juan, NOAA y manejo de emergencias.",
    }


def source_catalog() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "sources": [
            {
                "id": "nws_alerts_pr",
                "name": "NWS Active Alerts Puerto Rico",
                "url": NWS_ALERTS_PR,
                "use": "Avisos, advertencias y alertas oficiales activas para Puerto Rico.",
                "refresh_seconds": 60,
            },
            {
                "id": "noaa_radar_base_reflectivity",
                "name": "NOAA/NWS MRMS Radar Base Reflectivity",
                "url": NOAA_RADAR_MAPSERVER,
                "use": "Capa visual de radar/lluvia actual para Puerto Rico y el Caribe.",
                "refresh_seconds": 300,
            },
            {
                "id": "noaa_radar_time",
                "name": "NOAA/NWS Time-Enabled Radar Base Reflectivity",
                "url": NOAA_RADAR_TIME_IMAGESERVER,
                "use": "Radar con ventana de tiempo móvil de hasta cuatro horas cuando el cliente use tiempo.",
                "refresh_seconds": 300,
            },
            {
                "id": "noaa_mrms_qpe",
                "name": "NOAA/NWS MRMS QPE",
                "url": NOAA_MRMS_QPE_IMAGESERVER,
                "use": "Estimado de precipitación acumulada por ventanas 1h, 3h, 6h, 12h, 24h, 48h y 72h.",
                "refresh_seconds": 3600,
            },
            {
                "id": "noaa_wpc_qpf",
                "name": "NOAA/WPC Quantitative Precipitation Forecast",
                "url": WPC_QPF_MAPSERVER,
                "use": "Pronóstico cuantitativo de precipitación para próximos periodos operacionales.",
                "refresh_seconds": 21600,
            },
        ],
    }


def map_layers() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "layers": [
            {
                "id": "radar_live",
                "label": "Radar en vivo",
                "service_type": "ArcGIS MapServer export",
                "url": NOAA_RADAR_MAPSERVER,
                "layers": "show:3",
                "opacity": 0.78,
                "description": "Reflectividad base MRMS para lluvia/radar actual.",
            },
            {
                "id": "rain_1h",
                "label": "Lluvia observada 1h",
                "service_type": "ArcGIS MapServer export",
                "url": NOAA_RFC_QPE_MAPSERVER,
                "layers": "show:8",
                "opacity": 0.70,
                "description": "Lluvia observada durante la última hora.",
            },
            {
                "id": "rain_3h",
                "label": "Lluvia observada 3h",
                "service_type": "ArcGIS MapServer export",
                "url": NOAA_RFC_QPE_MAPSERVER,
                "layers": "show:16",
                "opacity": 0.70,
                "description": "Lluvia observada durante las últimas tres horas.",
            },
            {
                "id": "rain_24h",
                "label": "Lluvia observada 24h",
                "service_type": "ArcGIS MapServer export",
                "url": NOAA_RFC_QPE_MAPSERVER,
                "layers": "show:28",
                "opacity": 0.70,
                "description": "Lluvia observada durante las últimas 24 horas.",
            },
            {
                "id": "qpf_forecast",
                "label": "Pronóstico de lluvia WPC",
                "service_type": "ArcGIS MapServer export",
                "url": WPC_QPF_MAPSERVER,
                "layers": "show:1,2,3",
                "opacity": 0.54,
                "description": "Pronóstico experimental de lluvia acumulada usando WPC QPF.",
            },
        ],
        "refresh_policy": {
            "alerts_seconds": 60,
            "radar_seconds": 300,
            "qpe_seconds": 3600,
            "nws_rate_limit_note": "NWS recomienda no consultar alertas con frecuencia mayor a cada 30 segundos; PR-WX usa 60 segundos.",
        },
    }


def _http_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "PR-WX AURORA RainCast PR/3.7.0 (educational experimental dashboard)",
            "Accept": "application/geo+json, application/json",
        },
    )
    with urlopen(request, timeout=18) as response:  # noqa: S310 - public NOAA endpoint
        return json.loads(response.read().decode("utf-8"))


def _normalize_alert(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties", {}) if isinstance(feature, dict) else {}
    text = " ".join(str(props.get(key) or "") for key in ("event", "headline", "description", "instruction"))
    if HIGH_RISK_PATTERNS.search(text):
        rain_priority = "alto"
    elif FLOOD_RAIN_PATTERNS.search(text):
        rain_priority = "moderado"
    else:
        rain_priority = "informativo"
    return {
        "id": feature.get("id") or props.get("id"),
        "event": props.get("event"),
        "headline": props.get("headline"),
        "severity": props.get("severity"),
        "certainty": props.get("certainty"),
        "urgency": props.get("urgency"),
        "effective": props.get("effective"),
        "expires": props.get("expires"),
        "area_desc": props.get("areaDesc"),
        "description": props.get("description"),
        "instruction": props.get("instruction"),
        "sender": props.get("senderName"),
        "response": props.get("response"),
        "rain_priority": rain_priority,
        "is_rain_or_flood": bool(FLOOD_RAIN_PATTERNS.search(text)),
    }


def active_pr_alerts() -> dict[str, Any]:
    try:
        raw = _http_json(NWS_ALERTS_PR)
        alerts = [_normalize_alert(item) for item in raw.get("features", [])]
        rain_alerts = [item for item in alerts if item["is_rain_or_flood"]]
        rain_alerts.sort(key=lambda item: ({"alto": 0, "moderado": 1, "informativo": 2}.get(item["rain_priority"], 3), item.get("effective") or ""))
        return {
            "status": "ok",
            "source": NWS_ALERTS_PR,
            "timestamp_utc": utc_now_iso(),
            "total_active_alerts": len(alerts),
            "rain_flood_alerts": len(rain_alerts),
            "alerts": rain_alerts,
            "all_alerts": alerts,
        }
    except (TimeoutError, URLError, OSError, json.JSONDecodeError) as exc:
        return {
            "status": "source_unavailable",
            "source": NWS_ALERTS_PR,
            "timestamp_utc": utc_now_iso(),
            "total_active_alerts": 0,
            "rain_flood_alerts": 0,
            "alerts": [],
            "all_alerts": [],
            "error": str(exc),
        }


def _risk_level(score: int) -> str:
    if score >= 75:
        return "alto"
    if score >= 45:
        return "moderado"
    return "bajo"


def municipal_risk(alert_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = alert_payload or active_pr_alerts()
    alert_count = int(payload.get("rain_flood_alerts") or 0)
    high_count = sum(1 for alert in payload.get("alerts", []) if alert.get("rain_priority") == "alto")
    base = min(70, alert_count * 18 + high_count * 22)
    towns = []
    for town in PR_TOWNS:
        score = int(min(100, round(base * float(town["risk_weight"]))))
        towns.append(
            {
                **town,
                "rain_risk_score": score,
                "rain_risk_level": _risk_level(score),
                "analysis": _municipal_analysis(town["name"], score, alert_count, high_count),
            }
        )
    return {
        "model": model_identity(),
        "timestamp_utc": utc_now_iso(),
        "summary": {
            "rain_flood_alerts": alert_count,
            "high_priority_alerts": high_count,
            "overall_risk_score": min(100, base),
            "overall_risk_level": _risk_level(min(100, base)),
        },
        "municipalities": towns,
    }


def _municipal_analysis(name: str, score: int, alert_count: int, high_count: int) -> str:
    if score >= 75:
        return f"{name} requiere vigilancia alta por lluvia/inundación. Validar radar, drenaje, quebradas y avisos de NWS San Juan."
    if score >= 45:
        return f"{name} mantiene vigilancia moderada. Revisar acumulación de lluvia reciente y posibles avisos hidrológicos."
    if alert_count or high_count:
        return f"{name} se mantiene en vigilancia preventiva, aunque el riesgo municipal estimado no aparece alto en este resumen experimental."
    return f"{name} sin señal prioritaria de lluvia/inundación en las alertas filtradas al momento de la consulta."


def live_rain_summary() -> dict[str, Any]:
    alerts = active_pr_alerts()
    risk = municipal_risk(alerts)
    return {
        "model": model_identity(),
        "timestamp_utc": utc_now_iso(),
        "status": alerts.get("status"),
        "alerts": {
            "source": alerts.get("source"),
            "total_active_alerts": alerts.get("total_active_alerts"),
            "rain_flood_alerts": alerts.get("rain_flood_alerts"),
            "top_alerts": alerts.get("alerts", [])[:8],
        },
        "risk": risk["summary"],
        "recommended_actions": recommended_actions(risk["summary"].get("overall_risk_level")),
        "map_layers": map_layers()["layers"],
    }


def recommended_actions(level: str | None) -> list[str]:
    if level == "alto":
        return [
            "Validar de inmediato con NWS San Juan y manejo de emergencias.",
            "Revisar zonas propensas a inundaciones urbanas, quebradas y carreteras bajas.",
            "Evitar cruzar carreteras inundadas y reforzar comunicación preventiva.",
        ]
    if level == "moderado":
        return [
            "Monitorear radar y lluvia acumulada cada 15 a 30 minutos durante aguaceros fuertes.",
            "Preparar comunicación preventiva para municipios vulnerables.",
            "Verificar drenajes y áreas con historial de inundación.",
        ]
    return [
        "Mantener monitoreo rutinario del radar y alertas oficiales.",
        "Actualizar si aparece nuevo aviso de inundación, lluvia fuerte o producto hidrológico.",
    ]


def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "model": model_identity(),
        "timestamp_utc": utc_now_iso(),
        "endpoints": [
            "/rain/live/model",
            "/rain/live/status",
            "/rain/live/sources",
            "/rain/live/layers",
            "/rain/live/alerts",
            "/rain/live/summary",
            "/rain/live/municipal-risk",
        ],
    }
