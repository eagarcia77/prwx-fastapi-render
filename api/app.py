from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from prwx.immersive import build_briefing, predictions_to_geojson, simulate_scenario
from prwx.accessibility import add_accessibility_columns, build_accessible_summary, focus_municipalities_table
from prwx.seismic import build_seismic_briefing, evaluate_android_trigger_cluster
from prwx.realtime_v9 import build_safety_alerts
from prwx.temperature_v10 import add_temperature_columns, build_weather_animation_v10, build_temperature_table

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
WEB_CLIENT = ROOT / "mobile"
LEGACY_WEB_CLIENT = ROOT / "web_mobile_bridge"
PRED_PATHS = [PROCESSED / "live_predictions_v10.csv",
    PROCESSED / "live_predictions_v9.csv", PROCESSED / "live_predictions_v8.csv", PROCESSED / "live_predictions_v6.csv", PROCESSED / "live_predictions_v5.csv", PROCESSED / "live_predictions.csv"]
META_PATH = PROCESSED / "latest_run.json"
BRIEFING_PATH = PROCESSED / "prwx_briefing_v6.json"
ACCESSIBLE_SUMMARY_PATH = PROCESSED / "accessible_summary_v8.json"
REALTIME_SUMMARY_PATH = PROCESSED / "realtime_summary_v10.json"
ANIMATION_PATH = PROCESSED / "weather_animation_v10.csv"
SAFETY_ALERTS_PATH = PROCESSED / "safety_alerts_v9.csv"
FOCUS_PATH = PROCESSED / "focus_temperature_v10.csv"
TEMPERATURE_PATH = PROCESSED / "temperature_municipalities_v10.csv"
GRID_PATH = PROCESSED / "immersive_grid_v6.csv"
GEOJSON_PATH = PROCESSED / "live_predictions_v6.geojson"
EARTHQUAKES_PATH = PROCESSED / "live_earthquakes_v7.csv"
SEISMIC_EEW_PATH = PROCESSED / "seismic_eew_v7.csv"
SEISMIC_BRIEFING_PATH = PROCESSED / "seismic_briefing_v7.json"
ANDROID_TRIGGERS_PATH = PROCESSED / "android_triggers_sample_v7.csv"

app = FastAPI(title="PR-WX v2.2.1 Web Mobile Sensor Bridge", version="2.2.1")


class AndroidTrigger(BaseModel):
    trigger_time_utc: str | None = Field(default=None, description="UTC timestamp. If omitted, server time is used.")
    coarse_lat: float = Field(..., ge=-90, le=90, description="Approximate/coarse latitude, not exact home address.")
    coarse_lon: float = Field(..., ge=-180, le=180, description="Approximate/coarse longitude, not exact home address.")
    pga_g: float = Field(..., ge=0, le=3, description="Approximate peak ground acceleration in g.")
    confidence: float = Field(..., ge=0, le=1, description="Client-side trigger confidence 0-1.")
    source: str = Field(default="android_sensor_bridge", max_length=80)


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def safe_read_predictions() -> pd.DataFrame:
    for path in PRED_PATHS:
        df = _safe_read_csv(path)
        if not df.empty:
            return df
    raise HTTPException(status_code=404, detail="Predictions not found or empty. Run scripts/21_operational_update_v10.py first.")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}



def _csv_records(path: Path):
    df = _safe_read_csv(path)
    return df.to_dict(orient="records")

def _json_file(path: Path):
    data = read_json(path)
    return data if data else {"status": "not_found_or_empty", "path": str(path)}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()



@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "PR-WX FastAPI",
        "version": "2.2.1",
        "platform": "render",
        "timestamp_utc": utc_now_iso(),
    }


@app.get("/readyz")
def readyz():
    return {
        "status": "ready" if META_PATH.exists() else "bootstrap_needed",
        "metadata_exists": META_PATH.exists(),
        "processed_dir_exists": PROCESSED.exists(),
        "timestamp_utc": utc_now_iso(),
    }


@app.get("/render/status")
def render_status_v21():
    return _json_file(PROCESSED / "render_status_v21.json")


@app.get("/")
def root():
    return {
        "name": "PR-WX Web Mobile Sensor Bridge",
        "version": "2.2.1",
        "status": "experimental",
        "note": "Accessible weather risk + earthquake early warning visualization. Not official emergency guidance.",
    }


@app.get("/metadata")
def metadata():
    data = read_json(META_PATH)
    return data if data else {"status": "no metadata yet"}


@app.get("/predictions")
def predictions():
    return safe_read_predictions().to_dict(orient="records")


@app.get("/municipality/{name}")
def municipality(name: str):
    df = safe_read_predictions()
    match = df[df["municipality"].astype(str).str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail="Municipality not found.")
    return match.iloc[0].to_dict()


@app.get("/briefing")
def briefing():
    data = read_json(BRIEFING_PATH)
    if data:
        return data
    df = safe_read_predictions()
    return build_briefing(df, meta=read_json(META_PATH))


@app.get("/accessible-summary")
def accessible_summary():
    data = read_json(ACCESSIBLE_SUMMARY_PATH)
    if data:
        return data
    df = add_accessibility_columns(safe_read_predictions())
    return build_accessible_summary(df, generated_at_utc=read_json(META_PATH).get("generated_at_utc"))


@app.get("/focus-municipalities")
def focus_municipalities():
    df = _safe_read_csv(FOCUS_PATH)
    if df.empty:
        df = focus_municipalities_table(add_accessibility_columns(safe_read_predictions()))
    return df.to_dict(orient="records")


@app.get("/geojson")
def geojson():
    data = read_json(GEOJSON_PATH)
    if data:
        return data
    return predictions_to_geojson(safe_read_predictions())


@app.get("/immersive-grid")
def immersive_grid():
    df = _safe_read_csv(GRID_PATH)
    if df.empty:
        raise HTTPException(status_code=404, detail="Immersive grid not found. Run scripts/21_operational_update_v10.py first.")
    return df.to_dict(orient="records")


@app.get("/scenario")
def scenario(rain_multiplier: float = 1.25, soil_saturation_boost: float = 0.5, heat_boost_f: float = 2.0, alert_override: int | None = None):
    df = safe_read_predictions()
    simulated = simulate_scenario(
        df,
        rain_multiplier=rain_multiplier,
        soil_saturation_boost=soil_saturation_boost,
        heat_boost_f=heat_boost_f,
        alert_override=alert_override,
    )
    return simulated.to_dict(orient="records")


@app.get("/realtime-summary")
def realtime_summary():
    data = read_json(REALTIME_SUMMARY_PATH)
    if data:
        return data
    df = add_temperature_columns(safe_read_predictions())
    return {"status": "generated_on_request", "rows": len(df), "model_version": "1.0.0"}


@app.get("/weather-animation")
def weather_animation():
    df = _safe_read_csv(ANIMATION_PATH)
    if df.empty:
        df = build_weather_animation_v10(add_temperature_columns(safe_read_predictions()))
    return df.to_dict(orient="records")


@app.get("/temperature")
def temperature():
    df = _safe_read_csv(TEMPERATURE_PATH)
    if df.empty:
        df = build_temperature_table(add_temperature_columns(safe_read_predictions()))
    return df.to_dict(orient="records")


@app.get("/temperature/focus")
def temperature_focus():
    df = _safe_read_csv(FOCUS_PATH)
    if df.empty:
        df = focus_municipalities_table(add_temperature_columns(safe_read_predictions()))
    return df.to_dict(orient="records")


@app.get("/safety-alerts")
def safety_alerts():
    df = _safe_read_csv(SAFETY_ALERTS_PATH)
    if df.empty:
        pred = add_realtime_columns(safe_read_predictions())
        eq = _safe_read_csv(EARTHQUAKES_PATH)
        triggers = _safe_read_csv(ANDROID_TRIGGERS_PATH)
        nws_alerts = _safe_read_csv(PROCESSED / "live_nws_alerts.csv")
        df = build_safety_alerts(pred, eq, nws_alerts, triggers)
    return df.to_dict(orient="records")


@app.get("/seismic/earthquakes")
def seismic_earthquakes():
    df = _safe_read_csv(EARTHQUAKES_PATH)
    if df.empty:
        raise HTTPException(status_code=404, detail="No seismic data. Run scripts/17_update_seismic_v7.py first.")
    return df.to_dict(orient="records")


@app.get("/seismic/eew")
def seismic_eew():
    df = _safe_read_csv(SEISMIC_EEW_PATH)
    if df.empty:
        raise HTTPException(status_code=404, detail="No EEW matrix. Run scripts/17_update_seismic_v7.py first.")
    return df.to_dict(orient="records")


@app.get("/seismic/briefing")
def seismic_briefing():
    data = read_json(SEISMIC_BRIEFING_PATH)
    if data:
        return data
    eq = _safe_read_csv(EARTHQUAKES_PATH)
    eew = _safe_read_csv(SEISMIC_EEW_PATH)
    triggers = _safe_read_csv(ANDROID_TRIGGERS_PATH)
    return build_seismic_briefing(eq, eew, triggers, utc_now_iso())


@app.post("/seismic/android-trigger")
def ingest_android_trigger(trigger: AndroidTrigger):
    """Experimental endpoint for a future Android app.

    Stores coarse, anonymized trigger rows only. It does not issue public alerts.
    """
    row = trigger.model_dump()
    row["trigger_time_utc"] = row.get("trigger_time_utc") or utc_now_iso()
    existing = _safe_read_csv(ANDROID_TRIGGERS_PATH)
    updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    # Keep only a small recent demo buffer to avoid collecting long-term location histories.
    if len(updated) > 500:
        updated = updated.tail(500).copy()
    _write_csv(ANDROID_TRIGGERS_PATH, updated)
    return {
        "status": "stored_experimental_trigger",
        "privacy": "No names, phone numbers or device IDs are stored by this prototype endpoint.",
        "cluster": evaluate_android_trigger_cluster(updated),
    }



@app.post("/seismic/web-trigger")
def ingest_web_trigger(trigger: AndroidTrigger):
    """Experimental endpoint for the browser-based Web Sensor Bridge.

    Stores coarse, anonymized trigger rows only. It does not issue public alerts.
    Requires validation against official sources before any public action.
    """
    row = trigger.model_dump()
    row["trigger_time_utc"] = row.get("trigger_time_utc") or utc_now_iso()
    if not row.get("source") or row.get("source") == "android_sensor_bridge":
        row["source"] = "web_sensor_bridge"
    existing = _safe_read_csv(ANDROID_TRIGGERS_PATH)
    updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    if len(updated) > 500:
        updated = updated.tail(500).copy()
    _write_csv(ANDROID_TRIGGERS_PATH, updated)
    return {
        "status": "stored_experimental_web_trigger",
        "privacy": "No names, phone numbers, exact addresses or device IDs are stored by this prototype endpoint.",
        "cluster": evaluate_android_trigger_cluster(updated),
    }


@app.get("/seismic/mobile-cluster")
def mobile_cluster():
    """Combined mobile cluster view for Android app and Web Sensor Bridge triggers."""
    triggers = _safe_read_csv(ANDROID_TRIGGERS_PATH)
    return evaluate_android_trigger_cluster(triggers)


@app.get("/web-bridge/status")
def web_bridge_status():
    return {
        "status": "ok",
        "version": "2.2.1",
        "web_app_path": "/mobile/",
        "trigger_endpoint": "/seismic/web-trigger",
        "cluster_endpoint": "/seismic/mobile-cluster",
        "privacy": "coarse location only; no device ID required",
    }


@app.get("/seismic/android-cluster")
def android_cluster():
    triggers = _safe_read_csv(ANDROID_TRIGGERS_PATH)
    return evaluate_android_trigger_cluster(triggers)


@app.get("/radar/layers")
def radar_layers_v14():
    return _csv_records(PROCESSED / "radar_layers_v14.csv")

@app.get("/hurricanes/cone")
def hurricane_cone_v14():
    return _csv_records(PROCESSED / "atlantic_hurricane_cone_v14.csv")

@app.get("/hurricanes/pr-risk")
def hurricane_pr_risk_v14():
    return _csv_records(PROCESSED / "hurricane_pr_risk_v14.csv")

@app.get("/seismic/global")
def global_earthquakes_v14():
    return _csv_records(PROCESSED / "global_earthquakes_v13.csv")

@app.get("/seismic/global-tsunami")
def global_tsunami_v14():
    return _csv_records(PROCESSED / "global_tsunami_watch_v13.csv")


@app.get("/system/health")
def system_health_v15():
    return _json_file(PROCESSED / "system_health_v15.json")

@app.get("/radar/mrms-manifest")
def mrms_manifest_v15():
    return _csv_records(PROCESSED / "mrms_manifest_v15.csv")


@app.get("/radar/mrms-real")
def mrms_real_v16():
    return _csv_records(PROCESSED / "mrms_real_image_urls_v16.csv")

@app.get("/radar/mrms-real-summary")
def mrms_real_summary_v16():
    return _json_file(PROCESSED / "mrms_real_summary_v16.json")


@app.get("/alerts/active")
def active_alerts_v17():
    return _csv_records(PROCESSED / "active_alerts_v17.csv")

@app.get("/alerts/notification-state")
def notification_state_v17():
    return _json_file(PROCESSED / "notification_state_v17.json")

@app.get("/system/hardening")
def hardening_report_v17():
    return _json_file(PROCESSED / "hardening_report_v17.json")


@app.get("/radar/mrms-fixed")
def mrms_fixed_v18():
    return _csv_records(PROCESSED / "mrms_fixed_urls_v18.csv")

@app.get("/radar/mrms-fixed-summary")
def mrms_fixed_summary_v18():
    return _json_file(PROCESSED / "mrms_fixed_summary_v18.json")

@app.get("/life-safety/actions")
def life_safety_actions_v18():
    return _csv_records(PROCESSED / "life_safety_actions_v18.csv")

@app.get("/life-safety/municipal")
def municipal_life_safety_v18():
    return _csv_records(PROCESSED / "municipal_life_safety_v18.csv")

@app.get("/life-safety/summary")
def life_safety_summary_v18():
    return _json_file(PROCESSED / "life_safety_summary_v18.json")


@app.get("/services/status")
def services_status_v19():
    return _csv_records(PROCESSED / "service_status_v19.csv")

@app.get("/services/android-earthquake")
def android_earthquake_bridge_v19():
    return _json_file(PROCESSED / "android_earthquake_bridge_status_v19.json")

@app.get("/services/verification-summary")
def verification_summary_v19():
    return _json_file(PROCESSED / "verification_summary_v19.json")


@app.get("/services/android-app-status")
def android_app_status_v20():
    return _json_file(PROCESSED / "android_app_bridge_status_v20.json")


@app.get("/mobile-app", include_in_schema=False)
def mobile_app_redirect():
    return RedirectResponse(url="/mobile/")


if WEB_CLIENT.exists():
    app.mount("/mobile", StaticFiles(directory=str(WEB_CLIENT), html=True), name="mobile-web-bridge")
elif LEGACY_WEB_CLIENT.exists():
    app.mount("/mobile", StaticFiles(directory=str(LEGACY_WEB_CLIENT), html=True), name="mobile-web-bridge")

