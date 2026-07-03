from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .hurricanes_v13 import build_sample_hurricane_tracks, fetch_live_hurricane_tracks


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class RadarConeUpdateResult:
    status: str
    generated_at_utc: str
    radar_layers_path: str
    hurricane_cone_path: str
    hurricane_risk_path: str
    summary_path: str
    message: str


def _load_predictions(root: Path) -> pd.DataFrame:
    processed = root / "data" / "processed"
    for name in ["live_predictions_v10.csv", "live_predictions_v9.csv", "live_predictions_v6.csv", "live_predictions.csv"]:
        path = processed / name
        if path.exists() and path.stat().st_size > 0:
            try:
                return pd.read_csv(path)
            except Exception:
                continue
    return pd.DataFrame()


def build_radar_layers(predictions: pd.DataFrame, generated_at_utc: str | None = None) -> pd.DataFrame:
    """Create pseudo-radar layers from municipal precipitation estimates.

    This is not raw radar. It provides a layered visualization while true MRMS raster
    integration is implemented later.
    """
    generated_at_utc = generated_at_utc or utc_now_iso()
    rows: list[dict[str, Any]] = []
    if predictions is None or predictions.empty:
        return pd.DataFrame(columns=["layer", "municipality", "lat", "lon", "rain_in", "rain_rate_in_hr", "reflectivity_est_dbz"])
    layers = [("Radar 1h", 1, 0.16), ("Radar 3h", 3, 0.34), ("Radar 6h", 6, 0.58), ("Radar 24h", 24, 1.00)]
    for _, r in predictions.iterrows():
        rain24 = float(pd.to_numeric(pd.Series([r.get("corrected_precip_24h_in", 0)]), errors="coerce").fillna(0).iloc[0])
        risk = float(pd.to_numeric(pd.Series([r.get("operational_risk_score", 0)]), errors="coerce").fillna(0).iloc[0])
        lat = float(r.get("lat", 0) or 0)
        lon = float(r.get("lon", 0) or 0)
        muni = r.get("municipality", "Municipio")
        muni_display = r.get("municipality_display", muni)
        for layer, hours, factor in layers:
            rain = max(0.0, rain24 * factor)
            rate = rain / max(hours, 1)
            dbz = min(65.0, max(5.0, 18 + 14 * math.log10(max(rate, 0.005) * 100)))
            rows.append({
                "generated_at_utc": generated_at_utc,
                "layer": layer,
                "hours": hours,
                "municipality": muni,
                "municipality_display": muni_display,
                "lat": lat,
                "lon": lon,
                "rain_in": round(rain, 3),
                "rain_rate_in_hr": round(rate, 3),
                "reflectivity_est_dbz": round(dbz, 1),
                "risk_score": round(risk, 1),
                "screen_reader_label": f"{layer}: {muni_display} con lluvia estimada de {rain:.2f} pulgadas, intensidad {rate:.2f} pulgadas por hora y riesgo {risk:.0f} de 100.",
            })
    return pd.DataFrame(rows)


def build_hurricane_cone(tracks: pd.DataFrame) -> pd.DataFrame:
    if tracks is None or tracks.empty:
        return pd.DataFrame(columns=["storm_name", "forecast_hour", "cone_side", "lat", "lon", "uncertainty_nm"])
    rows: list[dict[str, Any]] = []
    for _, r in tracks.iterrows():
        hr = int(float(r.get("forecast_hour", 0) or 0))
        unc_nm = 35 + (hr * 1.15)
        lat = float(r.get("lat", 0) or 0)
        lon = float(r.get("lon", 0) or 0)
        dlat = unc_nm / 60.0
        coslat = max(0.25, abs(math.cos(math.radians(lat))))
        dlon = unc_nm / (60.0 * coslat)
        storm = r.get("storm_name", "Sistema tropical")
        for side, slat, slon in [("centro", lat, lon), ("norte", lat+dlat, lon), ("sur", lat-dlat, lon), ("este", lat, lon+dlon), ("oeste", lat, lon-dlon)]:
            rows.append({
                "storm_name": storm,
                "storm_type": r.get("storm_type", "Sistema Tropical"),
                "forecast_hour": hr,
                "forecast_label": r.get("forecast_label", f"+{hr}h"),
                "cone_side": side,
                "lat": round(slat, 3),
                "lon": round(slon, 3),
                "center_lat": lat,
                "center_lon": lon,
                "uncertainty_nm": round(unc_nm, 1),
                "max_wind_mph": r.get("max_wind_mph", None),
                "screen_reader_label": f"Cono de incertidumbre de {storm} en +{hr} horas con radio aproximado de {unc_nm:.0f} millas náuticas.",
            })
    return pd.DataFrame(rows)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.atan2(math.sqrt(a), math.sqrt(1-a))


def build_hurricane_pr_risk(tracks: pd.DataFrame) -> pd.DataFrame:
    if tracks is None or tracks.empty:
        return pd.DataFrame(columns=["storm_name", "forecast_hour", "distance_to_pr_km", "pr_watch_level"])
    rows = []
    pr_lat, pr_lon = 18.22, -66.59
    for _, r in tracks.iterrows():
        dist = _haversine_km(float(r.get("lat", 0) or 0), float(r.get("lon", 0) or 0), pr_lat, pr_lon)
        wind = float(pd.to_numeric(pd.Series([r.get("max_wind_mph", 0)]), errors="coerce").fillna(0).iloc[0])
        hr = int(float(r.get("forecast_hour", 0) or 0))
        level = "informativo"
        if dist <= 350 and wind >= 74:
            level = "vigilancia alta para Puerto Rico"
        elif dist <= 550 and wind >= 50:
            level = "vigilancia"
        elif dist <= 800:
            level = "monitoreo"
        rows.append({
            "storm_name": r.get("storm_name", "Sistema tropical"),
            "forecast_hour": hr,
            "forecast_label": r.get("forecast_label", f"+{hr}h"),
            "distance_to_pr_km": round(dist, 1),
            "max_wind_mph": wind,
            "pr_watch_level": level,
            "screen_reader_label": f"{r.get('storm_name','Sistema tropical')} a {dist:.0f} kilómetros de Puerto Rico en +{hr} horas. Nivel: {level}.",
        })
    return pd.DataFrame(rows)


def build_v14_summary(radar_layers: pd.DataFrame, tracks: pd.DataFrame, cone: pd.DataFrame, hurricane_risk: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    active_storms = [] if tracks.empty else sorted(tracks["storm_name"].dropna().astype(str).unique().tolist())
    highest_radar = 0.0 if radar_layers.empty else float(pd.to_numeric(radar_layers.get("rain_rate_in_hr", 0), errors="coerce").fillna(0).max())
    high_pr = [] if hurricane_risk.empty else hurricane_risk[hurricane_risk["pr_watch_level"].astype(str).str.contains("vigilancia", case=False, na=False)].head(5).to_dict(orient="records")
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.4.0",
        "headline": f"v1.4 activa radar por capas, cono de incertidumbre y {len(active_storms)} sistema(s) tropical(es) visibles.",
        "active_storms": active_storms,
        "highest_radar_rate_in_hr": round(highest_radar, 3),
        "puerto_rico_hurricane_watch_items": high_pr,
        "accessibility_notes": [
            "Cada mapa tiene tabla textual equivalente.",
            "El color no es la única señal de riesgo.",
            "El cono de incertidumbre incluye lectura clara para lectores de pantalla.",
        ],
    }


def write_v14_artifacts(root: Path, *, use_live_hurricanes: bool = True, generated_at_utc: str | None = None) -> RadarConeUpdateResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    predictions = _load_predictions(root)
    radar = build_radar_layers(predictions, generated_at_utc=generated_at_utc)

    tracks = fetch_live_hurricane_tracks() if use_live_hurricanes else pd.DataFrame()
    if tracks.empty:
        tracks = build_sample_hurricane_tracks(generated_at_utc)
    cone = build_hurricane_cone(tracks)
    risk = build_hurricane_pr_risk(tracks)
    summary = build_v14_summary(radar, tracks, cone, risk, generated_at_utc)

    radar_path = processed / "radar_layers_v14.csv"
    tracks_path = processed / "atlantic_hurricane_tracks_v13.csv"
    cone_path = processed / "atlantic_hurricane_cone_v14.csv"
    risk_path = processed / "hurricane_pr_risk_v14.csv"
    summary_path = processed / "v14_operational_summary.json"
    radar.to_csv(radar_path, index=False)
    tracks.to_csv(tracks_path, index=False)
    cone.to_csv(cone_path, index=False)
    risk.to_csv(risk_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return RadarConeUpdateResult("ok", generated_at_utc, str(radar_path), str(cone_path), str(risk_path), str(summary_path), "v1.4 artifacts generated.")
