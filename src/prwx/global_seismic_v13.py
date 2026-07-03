from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

USGS_ALL_DAY_GEOJSON = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
USGS_ALL_HOUR_GEOJSON = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class GlobalSeismicUpdateResult:
    status: str
    generated_at_utc: str
    quakes_path: str
    tsunami_path: str
    summary_path: str
    message: str


def global_geojson_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates") or [None, None, None]
        if len(coords) < 2 or coords[0] is None or coords[1] is None:
            continue
        lon = float(coords[0]); lat = float(coords[1])
        depth_km = float(coords[2]) if len(coords) > 2 and coords[2] is not None else None
        t_ms = props.get("time")
        event_time = pd.to_datetime(t_ms, unit="ms", utc=True).isoformat() if t_ms else None
        mag = pd.to_numeric(props.get("mag"), errors='coerce')
        rows.append({
            "event_id": props.get("ids") or props.get("code") or props.get("url"),
            "event_time_utc": event_time,
            "place": props.get("place"),
            "magnitude": mag,
            "mmi": props.get("mmi"),
            "alert": props.get("alert"),
            "status": props.get("status"),
            "tsunami": int(props.get("tsunami") or 0),
            "felt_reports": props.get("felt"),
            "lat": lat,
            "lon": lon,
            "depth_km": depth_km,
            "source": "USGS realtime GeoJSON",
            "detail_url": props.get("url"),
            "screen_reader_label": f"Sismo de magnitud {mag if pd.notna(mag) else 'N/D'} cerca de {props.get('place','ubicación no disponible')} en latitud {lat} y longitud {lon}.",
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["magnitude"] = pd.to_numeric(df["magnitude"], errors='coerce')
        df = df.sort_values(["event_time_utc", "magnitude"], ascending=[False, False]).reset_index(drop=True)
    return df


def fetch_global_earthquakes(timeout: int = 12) -> pd.DataFrame:
    for url in [USGS_ALL_HOUR_GEOJSON, USGS_ALL_DAY_GEOJSON]:
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.3 educational"})
            r.raise_for_status()
            df = global_geojson_to_dataframe(r.json())
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def build_sample_global_earthquakes(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    rows = [
        {"event_id":"sample-global-001","event_time_utc":generated_at_utc,"place":"Puerto Rico region","magnitude":4.6,"mmi":None,"alert":None,"status":"sample_offline","tsunami":0,"felt_reports":12,"lat":17.98,"lon":-66.82,"depth_km":12.0,"source":"offline educational sample","detail_url":"","screen_reader_label":"Sismo de magnitud 4.6 en la región de Puerto Rico."},
        {"event_id":"sample-global-002","event_time_utc":generated_at_utc,"place":"Near the coast of Chile","magnitude":5.8,"mmi":None,"alert":None,"status":"sample_offline","tsunami":1,"felt_reports":40,"lat":-29.8,"lon":-71.5,"depth_km":25.0,"source":"offline educational sample","detail_url":"","screen_reader_label":"Sismo de magnitud 5.8 cerca de la costa de Chile con bandera de tsunami."},
        {"event_id":"sample-global-003","event_time_utc":generated_at_utc,"place":"Japan region","magnitude":5.2,"mmi":None,"alert":None,"status":"sample_offline","tsunami":0,"felt_reports":17,"lat":36.1,"lon":140.4,"depth_km":40.0,"source":"offline educational sample","detail_url":"","screen_reader_label":"Sismo de magnitud 5.2 en Japón."},
        {"event_id":"sample-global-004","event_time_utc":generated_at_utc,"place":"Alaska Peninsula","magnitude":6.1,"mmi":None,"alert":None,"status":"sample_offline","tsunami":1,"felt_reports":3,"lat":55.0,"lon":-158.4,"depth_km":19.0,"source":"offline educational sample","detail_url":"","screen_reader_label":"Sismo de magnitud 6.1 en Alaska con bandera de tsunami."},
    ]
    return pd.DataFrame(rows)


def build_global_seismic_summary(df: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    if df.empty:
        return {"generated_at_utc": generated_at_utc, "model_version":"1.3.0", "headline":"No hay datos sísmicos mundiales disponibles.", "tsunami_candidates":0, "earthquake_count":0}
    tsunami_count = int((pd.to_numeric(df.get("tsunami", 0), errors='coerce').fillna(0) > 0).sum())
    max_mag = float(pd.to_numeric(df.get("magnitude", 0), errors='coerce').fillna(0).max())
    top = df.sort_values(["magnitude"], ascending=False).head(5)[["place","magnitude","tsunami","event_time_utc"]].to_dict(orient="records")
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.3.0",
        "headline": f"Se registran {len(df)} eventos sísmicos recientes en el feed usado; {tsunami_count} tienen bandera de tsunami.",
        "earthquake_count": int(len(df)),
        "tsunami_candidates": tsunami_count,
        "max_magnitude": max_mag,
        "top_events": top,
        "notes": [
            "El marcador de tsunami proviene del feed de eventos y no sustituye un centro oficial de alerta de tsunami.",
            "Verifique siempre NOAA Tsunami Warning Center y autoridades locales.",
        ]
    }


def write_global_seismic_artifacts(root: Path, *, use_live: bool = True, generated_at_utc: str | None = None) -> GlobalSeismicUpdateResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    df = fetch_global_earthquakes() if use_live else pd.DataFrame()
    if df.empty:
        df = build_sample_global_earthquakes(generated_at_utc)
    tsunami = df[pd.to_numeric(df.get("tsunami", 0), errors='coerce').fillna(0) > 0].copy()
    summary = build_global_seismic_summary(df, generated_at_utc)
    quakes_path = processed / "global_earthquakes_v13.csv"
    tsunami_path = processed / "global_tsunami_watch_v13.csv"
    summary_path = processed / "global_seismic_summary_v13.json"
    df.to_csv(quakes_path, index=False)
    tsunami.to_csv(tsunami_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return GlobalSeismicUpdateResult('ok', generated_at_utc, str(quakes_path), str(tsunami_path), str(summary_path), 'Global seismic artifacts generated.')
