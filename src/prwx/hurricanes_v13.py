from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

NHC_CURRENT_STORMS_JSON = "https://www.nhc.noaa.gov/CurrentStorms.json"
ATLANTIC_BASIN_CODES = {"AL", "AT", "NA", "EP"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class HurricaneUpdateResult:
    status: str
    generated_at_utc: str
    tracks_path: str
    summary_path: str
    message: str


def _coerce_float(v: Any) -> float | None:
    try:
        return float(v)
    except Exception:
        return None


def build_sample_hurricane_tracks(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    base = datetime.fromisoformat(generated_at_utc.replace('Z', '+00:00'))
    storms = [
        {"storm_name": "Ariadna", "storm_type": "Huracán", "advisory_number": 12, "start_lat": 14.8, "start_lon": -47.5, "dlat": 0.8, "dlon": -2.2, "wind_mph": 95, "status": "Activo"},
        {"storm_name": "Boreal", "storm_type": "Tormenta Tropical", "advisory_number": 7, "start_lat": 22.1, "start_lon": -59.0, "dlat": 0.5, "dlon": -1.4, "wind_mph": 60, "status": "Activo"},
        {"storm_name": "Celeste", "storm_type": "Depresión Tropical", "advisory_number": 3, "start_lat": 11.9, "start_lon": -34.0, "dlat": 0.6, "dlon": -1.7, "wind_mph": 35, "status": "Vigilancia"},
    ]
    rows = []
    for s in storms:
        for hr in [0, 12, 24, 36, 48, 72, 96, 120]:
            rows.append({
                "storm_name": s["storm_name"],
                "storm_type": s["storm_type"],
                "status": s["status"],
                "advisory_number": s["advisory_number"],
                "forecast_hour": hr,
                "forecast_label": f"+{hr}h",
                "point_time_utc": (base + timedelta(hours=hr)).isoformat(),
                "lat": round(s["start_lat"] + (hr/12)*s["dlat"], 2),
                "lon": round(s["start_lon"] + (hr/12)*s["dlon"], 2),
                "max_wind_mph": max(20, s["wind_mph"] - int(hr*0.15)),
                "source": "offline educational sample",
                "screen_reader_label": f"{s['storm_name']} {s['storm_type']} en +{hr} horas cerca de latitud {round(s['start_lat'] + (hr/12)*s['dlat'],2)} y longitud {round(s['start_lon'] + (hr/12)*s['dlon'],2)} con viento máximo aproximado de {max(20, s['wind_mph'] - int(hr*0.15))} millas por hora.",
            })
    return pd.DataFrame(rows)


def fetch_live_hurricane_tracks(timeout: int = 12) -> pd.DataFrame:
    """Attempt to fetch a simple live Atlantic storms view from NHC.

    This parser is intentionally defensive because upstream structures can vary.
    If parsing fails, callers should fall back to the sample dataset.
    """
    try:
        r = requests.get(NHC_CURRENT_STORMS_JSON, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.3 educational"})
        r.raise_for_status()
        payload = r.json()
    except Exception:
        return pd.DataFrame()

    # Normalize a few plausible structures.
    storms = payload if isinstance(payload, list) else payload.get("activeStorms") or payload.get("storms") or payload.get("items") or []
    rows: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for item in storms:
        basin = str(item.get("basin") or item.get("id") or item.get("stormId") or "")
        if not any(code in basin for code in ATLANTIC_BASIN_CODES):
            # keep Atlantic/Caribbean systems; ignore if unknown but Atlantic-related name present
            text = (str(item.get("name") or "") + " " + str(item.get("stormName") or "")).lower()
            if not text:
                continue
        name = item.get("name") or item.get("stormName") or item.get("storm_name") or "Sistema tropical"
        lat = _coerce_float(item.get("lat") or item.get("latitude"))
        lon = _coerce_float(item.get("lon") or item.get("longitude"))
        wind = _coerce_float(item.get("wind") or item.get("maxWind") or item.get("windMph")) or 35.0
        storm_type = item.get("classification") or item.get("type") or item.get("stormType") or "Sistema Tropical"
        status = item.get("status") or item.get("stage") or "Activo"
        adv = item.get("advisory") or item.get("advisoryNumber") or item.get("advisory_number") or 0
        if lat is None or lon is None:
            continue
        # Build a small forward path for visualization if no official track points are available.
        for hr in [0, 12, 24, 36, 48, 72]:
            rows.append({
                "storm_name": name,
                "storm_type": storm_type,
                "status": status,
                "advisory_number": adv,
                "forecast_hour": hr,
                "forecast_label": f"+{hr}h",
                "point_time_utc": (now + timedelta(hours=hr)).isoformat(),
                "lat": round(lat + (0.08 * (hr/12)), 2),
                "lon": round(lon - (0.35 * (hr/12)), 2),
                "max_wind_mph": max(20, float(wind) - int(hr*0.1)),
                "source": "NHC CurrentStorms simplified",
                "screen_reader_label": f"{name} {storm_type} en +{hr} horas cerca de latitud {round(lat + (0.08 * (hr/12)),2)} y longitud {round(lon - (0.35 * (hr/12)),2)} con viento máximo aproximado de {max(20, float(wind) - int(hr*0.1))} millas por hora.",
            })
    return pd.DataFrame(rows)


def build_hurricane_summary(df: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    if df.empty:
        return {
            "generated_at_utc": generated_at_utc,
            "model_version": "1.3.0",
            "headline": "No hay trayectorias de huracanes disponibles en este momento.",
            "active_storms": [],
        }
    latest = df.sort_values(["storm_name", "forecast_hour"]).groupby("storm_name", as_index=False).first()
    active = latest[["storm_name", "storm_type", "status", "lat", "lon", "max_wind_mph"]].to_dict(orient="records")
    headline = f"Hay {len(active)} sistemas tropicales o muestras visibles en el Atlántico para animación de trayectoria."
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.3.0",
        "headline": headline,
        "active_storms": active,
        "notes": [
            "La trayectoria animada es un apoyo visual del prototipo.",
            "Siempre valide trayectorias oficiales con el National Hurricane Center.",
        ],
    }


def write_hurricane_artifacts(root: Path, *, use_live: bool = True, generated_at_utc: str | None = None) -> HurricaneUpdateResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    tracks = fetch_live_hurricane_tracks() if use_live else pd.DataFrame()
    if tracks.empty:
        tracks = build_sample_hurricane_tracks(generated_at_utc)

    summary = build_hurricane_summary(tracks, generated_at_utc)
    tracks_path = processed / "atlantic_hurricane_tracks_v13.csv"
    summary_path = processed / "atlantic_hurricane_summary_v13.json"
    tracks.to_csv(tracks_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return HurricaneUpdateResult("ok", generated_at_utc, str(tracks_path), str(summary_path), "Atlantic hurricane artifacts generated.")
