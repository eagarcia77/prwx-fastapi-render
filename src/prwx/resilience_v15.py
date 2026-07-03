from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

MRMS_QPE_SERVICE_URL = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"
MRMS_LAYER_GUIDANCE = {
    "QPE 1h": "Radar acumulado estimado por MRMS para 1 hora.",
    "QPE 3h": "Radar acumulado estimado por MRMS para 3 horas.",
    "QPE 6h": "Radar acumulado estimado por MRMS para 6 horas.",
    "QPE 24h": "Radar acumulado estimado por MRMS para 24 horas.",
}

@dataclass
class ResilienceResult:
    status: str
    generated_at_utc: str
    health_path: str
    mrms_manifest_path: str
    message: str

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def safe_read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns or [])
    try:
        df = pd.read_csv(path)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = pd.NA
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns or [])
    except Exception:
        return pd.DataFrame(columns=columns or [])

def check_url(url: str, timeout: int = 8) -> dict[str, Any]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.5 educational"})
        return {"url": url, "ok": bool(r.ok), "status_code": int(r.status_code), "error": ""}
    except Exception as exc:
        return {"url": url, "ok": False, "status_code": None, "error": str(exc)[:200]}

def build_mrms_manifest(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    return pd.DataFrame([
        {
            "generated_at_utc": generated_at_utc,
            "layer": layer,
            "service_url": MRMS_QPE_SERVICE_URL,
            "description": description,
            "implementation_status": "MRMS-ready: manifest and dashboard support included; raster tile integration is the next deployment step.",
            "screen_reader_label": f"{layer}: {description} Fuente recomendada: MRMS QPE de NOAA.",
        }
        for layer, description in MRMS_LAYER_GUIDANCE.items()
    ])

def build_health_report(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    required_files = [
        "live_predictions_v10.csv",
        "weather_animation_v10.csv",
        "safety_alerts_v9.csv",
        "global_earthquakes_v13.csv",
        "global_tsunami_watch_v13.csv",
        "atlantic_hurricane_tracks_v13.csv",
        "radar_layers_v14.csv",
        "atlantic_hurricane_cone_v14.csv",
        "hurricane_pr_risk_v14.csv",
    ]
    file_status = []
    for name in required_files:
        path = processed / name
        file_status.append({
            "file": name,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "empty": (not path.exists()) or path.stat().st_size == 0,
        })
    mrms_status = check_url(MRMS_QPE_SERVICE_URL)
    ok_count = sum(1 for item in file_status if item["exists"] and not item["empty"])
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.5.0",
        "overall_status": "ok" if ok_count >= 4 else "degraded",
        "files_checked": len(file_status),
        "files_ready": ok_count,
        "mrms_qpe_service": mrms_status,
        "recommended_action": "Dashboard can run with fallback data. For operational use, validate official sources and enable live services.",
        "file_status": file_status,
    }

def write_resilience_artifacts(root: Path, *, generated_at_utc: str | None = None) -> ResilienceResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    manifest = build_mrms_manifest(generated_at_utc)
    health = build_health_report(root, generated_at_utc)
    manifest_path = processed / "mrms_manifest_v15.csv"
    health_path = processed / "system_health_v15.json"
    manifest.to_csv(manifest_path, index=False)
    health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
    return ResilienceResult("ok", generated_at_utc, str(health_path), str(manifest_path), "v1.5 resilience and MRMS-ready artifacts generated.")
