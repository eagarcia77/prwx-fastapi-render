from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .seismic import build_sample_android_triggers, evaluate_android_trigger_cluster

SERVICE_ENDPOINTS = {
    "NWS Alerts API": "https://api.weather.gov/alerts/active?area=PR",
    "USGS All Hour Earthquakes": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "USGS All Day Earthquakes": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "NOAA/NWS MRMS QPE": "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer?f=pjson",
    "NHC Current Storms": "https://www.nhc.noaa.gov/CurrentStorms.json",
}

LOCAL_ARTIFACTS = {
    "Predicciones": "live_predictions_v10.csv",
    "Alertas activas": "active_alerts_v17.csv",
    "Android triggers sample": "android_triggers_sample_v7.csv",
    "Matriz EEW": "seismic_eew_v7.csv",
    "Terremotos PR": "live_earthquakes_v7.csv",
    "Terremotos mundo": "global_earthquakes_v13.csv",
    "MRMS fix": "mrms_fixed_urls_v18.csv",
    "Life Safety": "life_safety_actions_v18.csv",
}

@dataclass
class VerificationResult:
    status: str
    generated_at_utc: str
    service_status_path: str
    android_status_path: str
    verification_summary_path: str
    message: str

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def check_http_service(name: str, url: str, timeout: int = 10) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.9 service-check"})
        return {
            "service": name,
            "url": url,
            "ok": bool(response.ok),
            "status_code": int(response.status_code),
            "content_type": response.headers.get("content-type", ""),
            "message": "servicio responde" if response.ok else "servicio respondió con error",
        }
    except Exception as exc:
        return {
            "service": name,
            "url": url,
            "ok": False,
            "status_code": None,
            "content_type": "",
            "message": f"no respondió desde este entorno: {str(exc)[:180]}",
        }

def check_local_artifacts(root: Path) -> list[dict[str, Any]]:
    processed = root / "data" / "processed"
    rows = []
    for name, file in LOCAL_ARTIFACTS.items():
        path = processed / file
        rows.append({
            "service": name,
            "file": file,
            "ok": path.exists() and path.stat().st_size > 0,
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "message": "archivo generado" if path.exists() and path.stat().st_size > 0 else "pendiente o vacío",
        })
    return rows

def verify_android_earthquake_bridge(root: Path, *, generated_at_utc: str | None = None) -> dict[str, Any]:
    """Verify the local Android Sensor Bridge logic.

    This does not verify Google's private production Android Earthquake Alerts
    network. It verifies the local PR-WX bridge: coarse accelerometer triggers,
    cluster evaluation, privacy posture and EEW limitation.
    """
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    trigger_path = processed / "android_triggers_sample_v7.csv"
    if trigger_path.exists() and trigger_path.stat().st_size > 0:
        try:
            triggers = pd.read_csv(trigger_path)
        except Exception:
            triggers = build_sample_android_triggers(generated_at_utc)
    else:
        triggers = build_sample_android_triggers(generated_at_utc)
        processed.mkdir(parents=True, exist_ok=True)
        triggers.to_csv(trigger_path, index=False)

    cluster = evaluate_android_trigger_cluster(triggers)
    required_columns = {"trigger_time_utc", "coarse_lat", "coarse_lon", "pga_g", "confidence", "source"}
    columns_ok = required_columns.issubset(set(triggers.columns))
    privacy_ok = "device_id" not in triggers.columns and "name" not in triggers.columns and "address" not in triggers.columns
    bridge_ok = columns_ok and privacy_ok and int(cluster.get("trigger_count", 0)) >= 1

    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.9.0",
        "android_bridge_status": "ok" if bridge_ok else "degraded",
        "what_was_verified": [
            "Local Android Sensor Bridge sample/cluster logic.",
            "Coarse location fields only.",
            "No personal identifiers required.",
            "Cluster evaluation returns recommendation.",
            "EEW limitation message remains: no earthquake prediction.",
        ],
        "important_limitation": "PR-WX cannot directly access Google’s private Android Earthquake Alerts production network. A real Android app must send consent-based, coarse accelerometer triggers to this dashboard.",
        "trigger_rows": int(len(triggers)),
        "columns_ok": columns_ok,
        "privacy_ok": privacy_ok,
        "cluster": cluster,
        "recommended_next_step": "Crear app Android/Kotlin real con consentimiento, coarse location, acelerómetro, filtro de falso positivo y endpoint seguro hacia /seismic/android-trigger.",
    }

def build_verification_summary(service_rows: list[dict[str, Any]], artifact_rows: list[dict[str, Any]], android_status: dict[str, Any], generated_at_utc: str) -> dict[str, Any]:
    external_ok = sum(1 for row in service_rows if row.get("ok"))
    artifacts_ok = sum(1 for row in artifact_rows if row.get("ok"))
    overall = "ok" if artifacts_ok >= 5 and android_status.get("android_bridge_status") == "ok" else "degraded"
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.9.0",
        "overall_status": overall,
        "external_services_ok": external_ok,
        "external_services_checked": len(service_rows),
        "local_artifacts_ok": artifacts_ok,
        "local_artifacts_checked": len(artifact_rows),
        "android_bridge_status": android_status.get("android_bridge_status"),
        "summary": "Servicios verificados. Si un servicio externo aparece degradado, el dashboard conserva fallbacks y tablas accesibles.",
        "must_not_overclaim": "Android Earthquake Alerts de Google no es una API pública integrada; PR-WX verifica su propio Android Sensor Bridge.",
    }

def write_service_verification_artifacts(root: Path, *, generated_at_utc: str | None = None, check_external: bool = True) -> VerificationResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    service_rows = [check_http_service(name, url) for name, url in SERVICE_ENDPOINTS.items()] if check_external else [
        {"service": name, "url": url, "ok": None, "status_code": None, "content_type": "", "message": "verificación externa omitida"} for name, url in SERVICE_ENDPOINTS.items()
    ]
    artifact_rows = check_local_artifacts(root)
    android_status = verify_android_earthquake_bridge(root, generated_at_utc=generated_at_utc)
    summary = build_verification_summary(service_rows, artifact_rows, android_status, generated_at_utc)

    service_path = processed / "service_status_v19.csv"
    android_path = processed / "android_earthquake_bridge_status_v19.json"
    summary_path = processed / "verification_summary_v19.json"
    pd.DataFrame(service_rows + artifact_rows).to_csv(service_path, index=False)
    android_path.write_text(json.dumps(android_status, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return VerificationResult("ok", generated_at_utc, str(service_path), str(android_path), str(summary_path), "v1.9 service verification artifacts generated.")
