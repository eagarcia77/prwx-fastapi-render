from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_csv(path: Path, columns: list[str], rows: list[dict] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    pd.DataFrame(rows or [], columns=columns).to_csv(path, index=False)


def ensure_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    now = utc_now_iso()
    PROCESSED.mkdir(parents=True, exist_ok=True)

    ensure_json(PROCESSED / "latest_run.json", {
        "status": "ok",
        "model_version": "2.2.1",
        "generated_at_utc": now,
        "runtime": "render-fastapi",
        "message": "Render bootstrap completed. Run operational updater for live data.",
    })

    ensure_csv(
        PROCESSED / "active_alerts_v17.csv",
        ["generated_at_utc", "alert_type", "severity", "source", "headline", "area", "recommended_action"],
        [{
            "generated_at_utc": now,
            "alert_type": "sistema",
            "severity": "informativo",
            "source": "PR-WX Render Bootstrap",
            "headline": "API desplegada; esperando datos operacionales.",
            "area": "Puerto Rico",
            "recommended_action": "Ejecutar actualización operacional y validar fuentes oficiales.",
        }],
    )

    ensure_csv(
        PROCESSED / "android_triggers_sample_v7.csv",
        ["trigger_time_utc", "coarse_lat", "coarse_lon", "pga_g", "confidence", "source"],
        [{
            "trigger_time_utc": now,
            "coarse_lat": 18.02,
            "coarse_lon": -66.61,
            "pga_g": 0.05,
            "confidence": 0.35,
            "source": "render_bootstrap_sample",
        }],
    )

    ensure_json(PROCESSED / "android_app_bridge_status_v20.json", {
        "generated_at_utc": now,
        "model_version": "2.2.1",
        "overall_status": "ok",
        "render_ready": True,
        "endpoint": "/seismic/android-trigger",
        "note": "Android app can post to the public Render API URL.",
    })

    ensure_json(PROCESSED / "verification_summary_v19.json", {
        "generated_at_utc": now,
        "model_version": "2.2.1",
        "overall_status": "ok",
        "summary": "Render API bootstrap ready.",
    })

    ensure_json(PROCESSED / "render_status_v21.json", {
        "generated_at_utc": now,
        "model_version": "2.2.1",
        "platform": "Render",
        "fastapi": True,
        "github_ready": True,
        "health_endpoint": "/healthz",
        "web_mobile_bridge": "/mobile/",
        "web_trigger_endpoint": "/seismic/web-trigger",
    })

    ensure_csv(
        PROCESSED / "service_status_v19.csv",
        ["service", "url", "ok", "status_code", "content_type", "message"],
        [{
            "service": "Render FastAPI",
            "url": "/healthz",
            "ok": True,
            "status_code": 200,
            "content_type": "application/json",
            "message": "API bootstrap ready",
        }],
    )

    print("Render bootstrap completed.")


if __name__ == "__main__":
    main()
