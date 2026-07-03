from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from .municipalities import load_municipalities

PR_BOUNDS = {
    "min_lat": 17.2,
    "max_lat": 19.6,
    "min_lon": -68.4,
    "max_lon": -64.4,
}

USGS_ALL_DAY_GEOJSON = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
USGS_ALL_WEEK_GEOJSON = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"


@dataclass
class SeismicUpdateResult:
    status: str
    generated_at_utc: str
    earthquakes_path: str
    warning_path: str
    briefing_path: str
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def in_pr_region(lat: float, lon: float) -> bool:
    return PR_BOUNDS["min_lat"] <= lat <= PR_BOUNDS["max_lat"] and PR_BOUNDS["min_lon"] <= lon <= PR_BOUNDS["max_lon"]


def usgs_geojson_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates") or [None, None, None]
        if len(coords) < 2 or coords[0] is None or coords[1] is None:
            continue
        lon = float(coords[0])
        lat = float(coords[1])
        depth_km = float(coords[2]) if len(coords) > 2 and coords[2] is not None else np.nan
        if not in_pr_region(lat, lon):
            continue
        t_ms = props.get("time")
        event_time = pd.to_datetime(t_ms, unit="ms", utc=True).isoformat() if t_ms else None
        rows.append({
            "event_id": props.get("ids") or props.get("code") or props.get("url"),
            "event_time_utc": event_time,
            "place": props.get("place"),
            "magnitude": props.get("mag"),
            "mmi": props.get("mmi"),
            "alert": props.get("alert"),
            "status": props.get("status"),
            "tsunami": props.get("tsunami"),
            "lat": lat,
            "lon": lon,
            "depth_km": depth_km,
            "source": "USGS realtime GeoJSON",
            "detail_url": props.get("url"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce")
        df = df.sort_values(["event_time_utc", "magnitude"], ascending=[False, False]).reset_index(drop=True)
    return df


def fetch_usgs_earthquakes(timeout: int = 12, *, week_fallback: bool = True) -> pd.DataFrame:
    urls = [USGS_ALL_DAY_GEOJSON]
    if week_fallback:
        urls.append(USGS_ALL_WEEK_GEOJSON)
    for url in urls:
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model-v0.7/educational"})
            r.raise_for_status()
            df = usgs_geojson_to_dataframe(r.json())
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def build_sample_earthquakes(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    return pd.DataFrame([
        {
            "event_id": "sample-pr-eew-001",
            "event_time_utc": generated_at_utc,
            "place": "Muestra educativa: zona sísmica suroeste de Puerto Rico",
            "magnitude": 4.2,
            "mmi": None,
            "alert": None,
            "status": "sample_offline",
            "tsunami": 0,
            "lat": 17.94,
            "lon": -66.92,
            "depth_km": 10.0,
            "source": "offline educational sample",
            "detail_url": "",
        },
        {
            "event_id": "sample-pr-eew-002",
            "event_time_utc": generated_at_utc,
            "place": "Muestra educativa: noreste de Puerto Rico / Trinchera",
            "magnitude": 3.6,
            "mmi": None,
            "alert": None,
            "status": "sample_offline",
            "tsunami": 0,
            "lat": 19.02,
            "lon": -65.62,
            "depth_km": 25.0,
            "source": "offline educational sample",
            "detail_url": "",
        },
    ])


def estimate_warning_seconds(
    event_lat: float,
    event_lon: float,
    target_lat: float,
    target_lon: float,
    *,
    depth_km: float = 10.0,
    p_wave_km_s: float = 6.0,
    s_wave_km_s: float = 3.5,
    detection_delay_s: float = 6.0,
    network_processing_s: float = 2.0,
) -> float:
    """Estimate simplified EEW lead time, not earthquake prediction.

    The estimate assumes an earthquake has already started and uses a rough
    P-wave/S-wave arrival difference minus detection/processing delays. It is
    a decision-support approximation only.
    """
    surface_km = haversine_km(event_lat, event_lon, target_lat, target_lon)
    hypo_km = math.sqrt(surface_km**2 + max(0.0, depth_km) ** 2)
    p_arrival = hypo_km / p_wave_km_s
    s_arrival = hypo_km / s_wave_km_s
    lead = s_arrival - (p_arrival + detection_delay_s + network_processing_s)
    return round(max(0.0, lead), 1)


def classify_shaking_watch(magnitude: float | int | None, warning_seconds: float) -> str:
    try:
        mag = float(magnitude)
    except Exception:
        mag = 0.0
    if mag >= 6.0 and warning_seconds >= 5:
        return "alerta temprana significativa"
    if mag >= 5.0 and warning_seconds >= 3:
        return "posible alerta temprana"
    if mag >= 4.0:
        return "monitoreo sísmico"
    return "informativo"


def build_eew_matrix(earthquakes: pd.DataFrame, municipalities: pd.DataFrame, *, top_events: int = 3) -> pd.DataFrame:
    if earthquakes.empty or municipalities.empty:
        return pd.DataFrame(columns=[
            "event_id", "event_place", "event_magnitude", "event_depth_km", "municipality", "region",
            "distance_km", "estimated_warning_seconds", "shaking_watch", "eew_limitation"
        ])
    eq = earthquakes.head(top_events).copy()
    rows: list[dict[str, Any]] = []
    for _, e in eq.iterrows():
        for _, m in municipalities.iterrows():
            distance = haversine_km(float(e["lat"]), float(e["lon"]), float(m["lat"]), float(m["lon"]))
            seconds = estimate_warning_seconds(
                float(e["lat"]), float(e["lon"]), float(m["lat"]), float(m["lon"]),
                depth_km=float(e.get("depth_km") or 10.0),
            )
            rows.append({
                "event_id": e.get("event_id"),
                "event_place": e.get("place"),
                "event_magnitude": e.get("magnitude"),
                "event_depth_km": e.get("depth_km"),
                "event_lat": e.get("lat"),
                "event_lon": e.get("lon"),
                "municipality": m.get("municipality"),
                "region": m.get("region"),
                "lat": m.get("lat"),
                "lon": m.get("lon"),
                "distance_km": round(distance, 1),
                "estimated_warning_seconds": seconds,
                "shaking_watch": classify_shaking_watch(e.get("magnitude"), seconds),
                "eew_limitation": "No predice terremotos; estima segundos de alerta luego de detectar P-waves.",
            })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["event_magnitude", "estimated_warning_seconds"], ascending=[False, False])
    return out


def build_sample_android_triggers(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    # Coarse demo triggers: no device IDs, no personal names, no exact addresses.
    return pd.DataFrame([
        {"trigger_time_utc": generated_at_utc, "coarse_lat": 17.98, "coarse_lon": -66.91, "pga_g": 0.022, "confidence": 0.71, "source": "android_sensor_bridge_sample"},
        {"trigger_time_utc": generated_at_utc, "coarse_lat": 17.99, "coarse_lon": -66.88, "pga_g": 0.019, "confidence": 0.68, "source": "android_sensor_bridge_sample"},
        {"trigger_time_utc": generated_at_utc, "coarse_lat": 18.01, "coarse_lon": -66.90, "pga_g": 0.026, "confidence": 0.76, "source": "android_sensor_bridge_sample"},
        {"trigger_time_utc": generated_at_utc, "coarse_lat": 18.03, "coarse_lon": -66.86, "pga_g": 0.017, "confidence": 0.61, "source": "android_sensor_bridge_sample"},
    ])


def evaluate_android_trigger_cluster(triggers: pd.DataFrame, *, min_triggers: int = 4, min_avg_confidence: float = 0.60) -> dict[str, Any]:
    if triggers.empty:
        return {
            "cluster_status": "sin señales",
            "trigger_count": 0,
            "avg_confidence": 0.0,
            "centroid_lat": None,
            "centroid_lon": None,
            "recommendation": "Esperar señales o consultar USGS/Red Sísmica.",
        }
    conf = pd.to_numeric(triggers.get("confidence", pd.Series(dtype=float)), errors="coerce").fillna(0)
    lat = pd.to_numeric(triggers.get("coarse_lat", pd.Series(dtype=float)), errors="coerce")
    lon = pd.to_numeric(triggers.get("coarse_lon", pd.Series(dtype=float)), errors="coerce")
    count = int(len(triggers))
    avg_conf = float(conf.mean()) if count else 0.0
    ok = count >= min_triggers and avg_conf >= min_avg_confidence
    return {
        "cluster_status": "posible señal colectiva" if ok else "insuficiente para alerta",
        "trigger_count": count,
        "avg_confidence": round(avg_conf, 3),
        "centroid_lat": round(float(lat.mean()), 4) if lat.notna().any() else None,
        "centroid_lon": round(float(lon.mean()), 4) if lon.notna().any() else None,
        "recommendation": "Validar inmediatamente contra fuentes oficiales antes de alertar." if ok else "No emitir alerta; continuar monitoreo.",
        "privacy_note": "Usar ubicación aproximada, sin identificadores personales ni historial individual.",
    }


def build_seismic_briefing(earthquakes: pd.DataFrame, eew: pd.DataFrame, triggers: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    cluster = evaluate_android_trigger_cluster(triggers)
    if earthquakes.empty:
        headline = "Sin eventos sísmicos recientes en la región de Puerto Rico."
        top_event = None
    else:
        first = earthquakes.iloc[0]
        headline = f"Monitoreo sísmico: evento M{float(first.get('magnitude') or 0):.1f} - {first.get('place', 'región PR')}."
        top_event = first.to_dict()
    top_eew = [] if eew.empty else eew.sort_values("estimated_warning_seconds", ascending=False).head(10).to_dict(orient="records")
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "0.7.0",
        "headline": headline,
        "earthquake_prediction_policy": "Los terremotos no se predicen con certeza. El módulo implementa alerta temprana posterior al inicio del evento, no predicción previa.",
        "android_sensor_bridge": cluster,
        "top_event": top_event,
        "estimated_warning_examples": top_eew,
        "recommended_actions": [
            "Usar este módulo solo como visualización experimental y validarlo contra USGS, Red Sísmica de Puerto Rico y manejo de emergencias.",
            "No emitir alertas públicas automáticas desde señales Android sin verificación institucional y control de falsas alarmas.",
            "Para un piloto real, usar app Android propia con consentimiento, ubicación aproximada y datos agregados.",
        ],
    }


def write_seismic_artifacts(root: Path, *, use_live: bool = True, generated_at_utc: str | None = None) -> SeismicUpdateResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    muni_path = root / "data" / "sample" / "pr_municipalities.csv"
    municipalities = load_municipalities(muni_path)

    earthquakes = fetch_usgs_earthquakes() if use_live else pd.DataFrame()
    if earthquakes.empty:
        earthquakes = build_sample_earthquakes(generated_at_utc)

    eew = build_eew_matrix(earthquakes, municipalities, top_events=3)
    triggers = build_sample_android_triggers(generated_at_utc)
    briefing = build_seismic_briefing(earthquakes, eew, triggers, generated_at_utc)

    earthquakes_path = processed / "live_earthquakes_v7.csv"
    eew_path = processed / "seismic_eew_v7.csv"
    triggers_path = processed / "android_triggers_sample_v7.csv"
    briefing_path = processed / "seismic_briefing_v7.json"

    earthquakes.to_csv(earthquakes_path, index=False)
    eew.to_csv(eew_path, index=False)
    triggers.to_csv(triggers_path, index=False)
    briefing_path.write_text(json.dumps(briefing, ensure_ascii=False, indent=2), encoding="utf-8")

    return SeismicUpdateResult(
        status="ok",
        generated_at_utc=generated_at_utc,
        earthquakes_path=str(earthquakes_path),
        warning_path=str(eew_path),
        briefing_path=str(briefing_path),
        message="Seismic v0.7 artifacts generated.",
    )
