from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

STORM_AI_VERSION = "2.9.0"
STORM_AI_NAME = "PR-WX AI Storm Trajectory Intelligence"
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TRAINING = ROOT / "data" / "training"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

PR_CENTER = {"name": "Puerto Rico", "lat": 18.2208, "lon": -66.5901}
SAN_JUAN = {"name": "San Juan", "lat": 18.4655, "lon": -66.1057}

TRACK_CANDIDATES = (
    PROCESSED / "atlantic_hurricane_tracks_v13.csv",
    PROCESSED / "hurricane_cone_v14.csv",
    PROCESSED / "nhc_current_storms.csv",
    PROCESSED / "active_tropical_tracks.csv",
    PROCESSED / "storm_tracks_atlantic.csv",
)
TRAINING_CANDIDATES = (
    TRAINING / "storm_tracks_atlantic_training.parquet",
    TRAINING / "storm_tracks_atlantic_training.csv",
    TRAINING / "hurdat2_pr_features.parquet",
    TRAINING / "hurdat2_pr_features.csv",
)
MODEL_PATH = MODELS / "pr_storm_track_ai_v29.joblib"
TRAINING_REPORT_PATH = PROCESSED / "ai_storm_track_training_v29.json"
MAP_REPORT_PATH = PROCESSED / "ai_storm_track_map_v29.json"

APPROACH_CORRIDORS = [
    {
        "id": "east_atlantic_approach",
        "name": "Corredor este-atlántico hacia PR",
        "type": "training_corridor",
        "coordinates": [[-58.0, 14.0], [-60.5, 15.5], [-63.5, 17.0], [-66.6, 18.2]],
        "risk_context": "Trayectorias que se acercan desde el Atlántico tropical al este de las Antillas Menores.",
    },
    {
        "id": "caribbean_south_approach",
        "name": "Corredor sur del Caribe",
        "type": "training_corridor",
        "coordinates": [[-62.0, 12.0], [-64.0, 13.2], [-66.0, 15.2], [-67.5, 17.5]],
        "risk_context": "Sistemas que entran por el Caribe oriental y pasan al sur o suroeste de Puerto Rico.",
    },
    {
        "id": "north_recurve_corridor",
        "name": "Corredor norte/recurvatura",
        "type": "training_corridor",
        "coordinates": [[-60.5, 19.5], [-62.5, 21.0], [-65.0, 22.0], [-68.0, 23.0]],
        "risk_context": "Sistemas que recurvan al norte; pueden generar oleaje, lluvia indirecta y ráfagas aunque el centro no toque PR.",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _col(df: pd.DataFrame, *names: str) -> str | None:
    lookup = {c.casefold(): c for c in df.columns}
    for name in names:
        if name.casefold() in lookup:
            return lookup[name.casefold()]
    for c in df.columns:
        key = c.casefold()
        if any(name.casefold() in key for name in names):
            return c
    return None


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        value = float(value)
        if math.isfinite(value):
            return value
    except Exception:
        pass
    return default


def haversine_km(lat1: float, lon1: float, lat2: float = PR_CENTER["lat"], lon2: float = PR_CENTER["lon"]) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def bearing_to_pr(lat: float, lon: float) -> float:
    lat1, lat2 = math.radians(lat), math.radians(PR_CENTER["lat"])
    dlon = math.radians(PR_CENTER["lon"] - lon)
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def normalize_tracks(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    lat_c = _col(frame, "lat", "latitude", "storm_lat")
    lon_c = _col(frame, "lon", "longitude", "storm_lon")
    if not lat_c or not lon_c:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["lat"] = pd.to_numeric(frame[lat_c], errors="coerce")
    out["lon"] = pd.to_numeric(frame[lon_c], errors="coerce")
    out = out.dropna(subset=["lat", "lon"])
    if out.empty:
        return out
    id_c = _col(frame, "storm_id", "id", "system_id", "cyclone_id", "name")
    name_c = _col(frame, "storm_name", "name", "system_name")
    type_c = _col(frame, "storm_type", "type", "status", "classification")
    time_c = _col(frame, "valid_time_utc", "forecast_time_utc", "timestamp_utc", "time", "date")
    wind_c = _col(frame, "max_wind_mph", "wind_mph", "max_wind_kt", "wind_kt")
    pressure_c = _col(frame, "pressure_hpa", "minimum_pressure", "central_pressure")
    lead_c = _col(frame, "forecast_hour", "lead_hour", "tau")

    out["event_id"] = frame[id_c].astype(str).values[: len(out)] if id_c else "event_unknown"
    out["event_name"] = frame[name_c].astype(str).values[: len(out)] if name_c else out["event_id"]
    out["event_type"] = frame[type_c].astype(str).values[: len(out)] if type_c else "tropical_system"
    out["valid_time_utc"] = pd.to_datetime(frame[time_c], errors="coerce", utc=True).astype(str).values[: len(out)] if time_c else None
    out["forecast_hour"] = pd.to_numeric(frame[lead_c], errors="coerce").values[: len(out)] if lead_c else np.nan
    wind = pd.to_numeric(frame[wind_c], errors="coerce").values[: len(out)] if wind_c else np.nan
    if wind_c and "kt" in wind_c.casefold():
        wind = wind * 1.15078
    out["max_wind_mph"] = wind
    out["pressure_hpa"] = pd.to_numeric(frame[pressure_c], errors="coerce").values[: len(out)] if pressure_c else np.nan
    out["distance_to_pr_km"] = [haversine_km(float(r.lat), float(r.lon)) for r in out.itertuples()]
    out["bearing_to_pr_deg"] = [bearing_to_pr(float(r.lat), float(r.lon)) for r in out.itertuples()]
    return out.reset_index(drop=True)


def load_current_tracks() -> tuple[pd.DataFrame, str | None]:
    frames: list[pd.DataFrame] = []
    used: list[str] = []
    for path in TRACK_CANDIDATES:
        frame = normalize_tracks(_read_table(path))
        if not frame.empty:
            frames.append(frame)
            used.append(str(path))
    if not frames:
        return pd.DataFrame(), None
    return pd.concat(frames, ignore_index=True), "; ".join(used)


def _risk_level(score: float) -> str:
    if score >= 65:
        return "alto"
    if score >= 35:
        return "moderado"
    return "bajo"


def _probability(distance_km: float, wind_mph: float | None, approaching: bool, forecast_hours: float | None) -> float:
    distance_component = max(0.0, 1.0 - min(distance_km, 1200.0) / 1200.0)
    wind_component = min(max((wind_mph or 25.0) / 120.0, 0.0), 1.0)
    approach_component = 0.22 if approaching else 0.05
    lead_penalty = 0.0
    if forecast_hours is not None and math.isfinite(forecast_hours):
        lead_penalty = min(max(forecast_hours - 72.0, 0.0) / 240.0, 0.20)
    probability = 0.12 + 0.55 * distance_component + 0.22 * wind_component + approach_component - lead_penalty
    return round(float(min(max(probability, 0.02), 0.95)), 3)


def analyze_events() -> dict[str, Any]:
    tracks, source_path = load_current_tracks()
    events: list[dict[str, Any]] = []
    if not tracks.empty:
        for event_id, group in tracks.groupby("event_id", dropna=False):
            group = group.copy()
            if "valid_time_utc" in group.columns:
                group["__time"] = pd.to_datetime(group["valid_time_utc"], errors="coerce", utc=True)
                group = group.sort_values(["__time", "forecast_hour"], na_position="last")
            min_row = group.loc[group["distance_to_pr_km"].idxmin()].to_dict()
            last_row = group.iloc[-1].to_dict()
            first_dist = float(group["distance_to_pr_km"].iloc[0])
            last_dist = float(group["distance_to_pr_km"].iloc[-1])
            approaching = last_dist < first_dist
            min_distance = float(min_row.get("distance_to_pr_km", 9999))
            wind = _to_float(min_row.get("max_wind_mph"), 30.0)
            fh = _to_float(min_row.get("forecast_hour"), None)
            prob = _probability(min_distance, wind, approaching, fh)
            score = round(prob * 100, 1)
            level = _risk_level(score)
            name = str(min_row.get("event_name") or event_id)
            event_type = str(min_row.get("event_type") or "tropical_system")
            events.append(
                {
                    "event_id": str(event_id),
                    "event_name": name,
                    "event_type": event_type,
                    "closest_distance_km": round(min_distance, 1),
                    "closest_lat": round(float(min_row.get("lat")), 3),
                    "closest_lon": round(float(min_row.get("lon")), 3),
                    "max_wind_mph": round(float(wind or 0), 1),
                    "approaching_pr": bool(approaching),
                    "bearing_to_pr_deg": round(float(min_row.get("bearing_to_pr_deg", 0)), 1),
                    "impact_probability": prob,
                    "ai_risk_score": score,
                    "risk_level": level,
                    "confidence": round(0.42 + min(len(group), 12) * 0.03 + (0.08 if source_path else 0), 2),
                    "summary_es": f"{name}: el análisis IA estima riesgo {level} para Puerto Rico. Distancia mínima aproximada {min_distance:.0f} km; probabilidad experimental {prob:.0%}.",
                    "recommendation_es": "Validar inmediatamente con productos oficiales del NHC/NWS. Este resultado es apoyo analítico, no aviso oficial.",
                    "point_count": int(len(group)),
                }
            )
    events = sorted(events, key=lambda x: x["ai_risk_score"], reverse=True)
    return {
        "engine": STORM_AI_NAME,
        "version": STORM_AI_VERSION,
        "generated_at_utc": utc_now_iso(),
        "source_path": source_path,
        "active_or_archived_track_rows": int(len(tracks)),
        "event_count": len(events),
        "events": events,
        "training_status": training_status(),
        "disclaimer": "Producto experimental. La trayectoria y avisos oficiales deben venir del NHC, NWS San Juan y manejo de emergencias.",
    }


def _feature_line(coords: list[list[float]], props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": props}


def _feature_point(lon: float, lat: float, props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


def storm_geojson() -> dict[str, Any]:
    tracks, source_path = load_current_tracks()
    analysis = analyze_events()
    features: list[dict[str, Any]] = []
    features.append(_feature_point(PR_CENTER["lon"], PR_CENTER["lat"], {"kind": "reference", "name": "Centro de Puerto Rico"}))
    features.append(_feature_point(SAN_JUAN["lon"], SAN_JUAN["lat"], {"kind": "reference", "name": "San Juan"}))

    for corridor in APPROACH_CORRIDORS:
        features.append(
            _feature_line(
                corridor["coordinates"],
                {
                    "kind": "training_corridor",
                    "event_id": corridor["id"],
                    "event_name": corridor["name"],
                    "event_type": corridor["type"],
                    "risk_level": "moderado",
                    "ai_risk_score": 30,
                    "impact_probability": 0.30,
                    "summary_es": corridor["risk_context"],
                },
            )
        )
    if not tracks.empty:
        event_lookup = {e["event_id"]: e for e in analysis["events"]}
        for event_id, group in tracks.groupby("event_id", dropna=False):
            group = group.copy()
            if "valid_time_utc" in group.columns:
                group["__time"] = pd.to_datetime(group["valid_time_utc"], errors="coerce", utc=True)
                group = group.sort_values(["__time", "forecast_hour"], na_position="last")
            coords = [[float(r.lon), float(r.lat)] for r in group.itertuples()]
            props = event_lookup.get(str(event_id), {"event_id": str(event_id), "risk_level": "bajo", "ai_risk_score": 0})
            props = {**props, "kind": "storm_track"}
            if len(coords) >= 2:
                features.append(_feature_line(coords, props))
            for idx, r in enumerate(group.itertuples()):
                p = {**props, "kind": "storm_point", "point_index": idx, "lat": float(r.lat), "lon": float(r.lon)}
                features.append(_feature_point(float(r.lon), float(r.lat), p))

    return {
        "type": "FeatureCollection",
        "name": "PR-WX AI Storm Trajectory Map",
        "generated_at_utc": utc_now_iso(),
        "source_path": source_path,
        "analysis": analysis,
        "features": features,
    }


def status() -> dict[str, Any]:
    tracks, source_path = load_current_tracks()
    return {
        "engine": STORM_AI_NAME,
        "version": STORM_AI_VERSION,
        "status": "ok",
        "tracks_available": not tracks.empty,
        "track_rows": int(len(tracks)),
        "source_path": source_path,
        "model_file_exists": MODEL_PATH.exists(),
        "training_report_exists": TRAINING_REPORT_PATH.exists(),
        "runtime_training_enabled": False,
        "official_validation_required": True,
    }


def training_status() -> dict[str, Any]:
    frame, path = _first_table(TRAINING_CANDIDATES)
    if frame.empty:
        return {
            "available": False,
            "path": None,
            "rows": 0,
            "events": 0,
            "research_ready": False,
            "operational_candidate": False,
            "production_validated": False,
            "message": "Cargue un dataset historico HURDAT2/NHC/GFS/GEFS/HAFS con verificacion de impacto a PR para entrenar el modelo IA.",
        }
    event_col = _col(frame, "storm_id", "event_id", "sid", "name")
    time_col = _col(frame, "valid_time_utc", "date", "time")
    rows = int(len(frame))
    events = int(frame[event_col].nunique()) if event_col else 0
    span_days = 0
    if time_col:
        dates = pd.to_datetime(frame[time_col], errors="coerce", utc=True).dropna()
        if not dates.empty:
            span_days = int((dates.max() - dates.min()).total_seconds() // 86400)
    return {
        "available": True,
        "path": path,
        "rows": rows,
        "events": events,
        "span_days": span_days,
        "research_ready": rows >= 5000 and events >= 20,
        "operational_candidate": rows >= 50000 and events >= 100 and span_days >= 3650,
        "production_validated": False,
        "model_file_exists": MODEL_PATH.exists(),
    }


def training_plan() -> dict[str, Any]:
    return {
        "engine": STORM_AI_NAME,
        "version": STORM_AI_VERSION,
        "objective": "Predecir probabilidad experimental de acercamiento e impacto a Puerto Rico para ciclones tropicales, ondas tropicales y vaguadas usando variables historicas y pronosticos de ensamble.",
        "target_variables": [
            "closest_approach_km_to_pr",
            "impact_probability_0_1",
            "risk_level_low_moderate_high",
            "rain_wind_swell_impact_class",
            "lead_time_hours_to_closest_approach",
        ],
        "minimum_dataset": {
            "research_ready": {"rows": 5000, "events": 20, "years": 5},
            "operational_candidate": {"rows": 50000, "events": 100, "years": 10},
            "production_validated": "Validacion independiente por temporada, por intensidad, por distancia a PR y por eventos extremos.",
        },
        "features": [
            "lat", "lon", "distance_to_pr_km", "bearing_to_pr_deg", "translation_speed_kt", "heading_deg",
            "max_wind_kt", "minimum_pressure_hpa", "forecast_hour", "ensemble_spread_km", "sst_c",
            "vertical_wind_shear_kt", "mid_level_humidity_pct", "precipitable_water_mm", "goes_cloud_top_temp_c",
            "nhc_cone_distance_to_pr_km", "hafs_track_distance_to_pr_km", "gfs_member_distance_to_pr_km", "gefs_probability_near_pr",
        ],
        "official_sources": ["NHC advisories and GIS", "HURDAT2 best track", "GFS", "GEFS", "HAFS", "GOES-East", "ERA5", "OISST", "NWS San Juan alerts"],
        "commands": {
            "analyze": "python scripts/37_ai_storm_track_map_v29.py",
            "train": "python scripts/37_ai_storm_track_map_v29.py --train",
        },
        "safety_rule": "Nunca publicar avisos publicos desde el modelo. Validar con NHC/NWS y autoridades de emergencia.",
    }


def train_if_possible(force: bool = False) -> dict[str, Any]:
    frame, path = _first_table(TRAINING_CANDIDATES)
    status_payload = training_status()
    if frame.empty:
        return {"status": "training_data_missing", "training": status_payload}
    if not force and not status_payload.get("research_ready"):
        return {"status": "not_enough_data", "training": status_payload}
    lat_c = _col(frame, "lat", "latitude")
    lon_c = _col(frame, "lon", "longitude")
    target_c = _col(frame, "impact_probability", "impact_to_pr", "target", "label")
    if not lat_c or not lon_c or not target_c:
        return {"status": "missing_required_columns", "required": ["lat/lon", "impact_probability or label"], "training": status_payload}
    work = frame.copy()
    work["distance_to_pr_km"] = [haversine_km(float(a), float(b)) for a, b in zip(pd.to_numeric(work[lat_c], errors="coerce"), pd.to_numeric(work[lon_c], errors="coerce"))]
    numeric = work.select_dtypes(include=["number"]).copy()
    numeric = numeric.replace([np.inf, -np.inf], np.nan).dropna(subset=[target_c]) if target_c in numeric.columns else numeric
    if target_c not in numeric.columns or len(numeric) < 20:
        return {"status": "insufficient_numeric_training_rows", "rows": int(len(numeric)), "training": status_payload}
    y = pd.to_numeric(numeric[target_c], errors="coerce")
    x = numeric.drop(columns=[target_c], errors="ignore")
    if y.dropna().nunique() <= 2:
        y_class = y.fillna(0).astype(int)
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), RandomForestClassifier(n_estimators=220, random_state=29, min_samples_leaf=2))
        model.fit(x, y_class)
        metric = None
        try:
            pred = model.predict_proba(x)[:, -1]
            metric = float(roc_auc_score(y_class, pred)) if y_class.nunique() > 1 else None
        except Exception:
            pass
        problem_type = "classification"
    else:
        y_reg = y.fillna(y.median()).astype(float)
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), RandomForestRegressor(n_estimators=220, random_state=29, min_samples_leaf=2))
        model.fit(x, y_reg)
        pred = model.predict(x)
        metric = float(mean_absolute_error(y_reg, pred))
        problem_type = "regression"
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": list(x.columns), "version": STORM_AI_VERSION, "problem_type": problem_type}, MODEL_PATH)
    report = {"status": "trained_experimental", "version": STORM_AI_VERSION, "problem_type": problem_type, "metric": metric, "rows": int(len(x)), "source": path, "production_validated": False, "generated_at_utc": utc_now_iso()}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TRAINING_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def generate_artifacts() -> dict[str, Any]:
    payload = storm_geojson()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    MAP_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"status": "ok", "path": str(MAP_REPORT_PATH), "feature_count": len(payload.get("features", [])), "event_count": payload.get("analysis", {}).get("event_count", 0)}
