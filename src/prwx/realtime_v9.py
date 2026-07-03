from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .accessibility import add_accessibility_columns, build_accessible_summary, focus_municipalities_table
from .seismic import evaluate_android_trigger_cluster

FOCUS_ORDER = ["Juana Díaz", "Ponce", "San Juan", "San Germán"]
SAFETY_COLUMNS = [
    "generated_at_utc", "hazard_type", "source", "severity", "status", "headline",
    "municipality", "lat", "lon", "recommended_action", "is_official", "confidence_note",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _cardinal_from_degrees(deg: float | int | None) -> str:
    try:
        value = float(deg) % 360
    except Exception:
        value = 90.0
    labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return labels[int((value + 11.25) // 22.5) % 16]


def _wind_arrow(deg: float | int | None) -> str:
    """Arrow points toward approximate wind movement direction for display."""
    try:
        value = float(deg) % 360
    except Exception:
        value = 90.0
    arrows = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"]
    return arrows[int((value + 22.5) // 45) % 8]


def _region_wind_direction(region: Any) -> float:
    text = str(region or "").lower()
    if "south" in text or "sur" in text:
        return 120.0
    if "west" in text or "oeste" in text:
        return 95.0
    if "east" in text or "este" in text:
        return 85.0
    if "mountain" in text or "central" in text:
        return 110.0
    return 75.0


def add_realtime_columns(predictions: pd.DataFrame, *, generated_at_utc: str | None = None) -> pd.DataFrame:
    """Add v0.9 real-time display fields without changing source forecast data."""
    if predictions is None or predictions.empty:
        return pd.DataFrame()
    out = add_accessibility_columns(predictions).copy()
    generated = generated_at_utc or utc_now_iso()

    out["corrected_precip_24h_in"] = pd.to_numeric(out.get("corrected_precip_24h_in", 0), errors="coerce").fillna(0).clip(lower=0)
    out["operational_risk_score"] = pd.to_numeric(out.get("operational_risk_score", 0), errors="coerce").fillna(0).clip(0, 100)
    out["base_heat_index_f"] = pd.to_numeric(out["base_heat_index_f"] if "base_heat_index_f" in out.columns else pd.Series([88] * len(out), index=out.index), errors="coerce").fillna(88)

    if "wind_speed_mph" in out.columns:
        wind_speed = pd.to_numeric(out["wind_speed_mph"], errors="coerce")
    elif "base_wind_speed_mph" in out.columns:
        wind_speed = pd.to_numeric(out["base_wind_speed_mph"], errors="coerce")
    else:
        wind_speed = pd.Series(np.nan, index=out.index)
    synthetic_speed = 8.0 + (out["operational_risk_score"] * 0.08) + (out["corrected_precip_24h_in"] * 1.4)
    out["wind_speed_mph"] = wind_speed.fillna(synthetic_speed).clip(0, 60).round(1)

    if "wind_dir_deg" in out.columns:
        wind_dir = pd.to_numeric(out["wind_dir_deg"], errors="coerce")
    elif "base_wind_dir_deg" in out.columns:
        wind_dir = pd.to_numeric(out["base_wind_dir_deg"], errors="coerce")
    else:
        wind_dir = pd.Series(np.nan, index=out.index)
    out["wind_dir_deg"] = wind_dir.fillna(out.get("region", "").map(_region_wind_direction) if "region" in out.columns else 90.0).round(1)
    out["wind_direction_text"] = out["wind_dir_deg"].map(_cardinal_from_degrees)
    out["wind_arrow"] = out["wind_dir_deg"].map(_wind_arrow)
    out["rain_rate_est_in_hr"] = (out["corrected_precip_24h_in"] / 24.0).clip(lower=0).round(3)
    out["rapid_update_status"] = "actualizable cada minuto"
    out["generated_at_utc"] = generated
    out["realtime_version"] = "0.9.0"
    out["weather_plain_text"] = out.apply(
        lambda r: (
            f"{r.get('municipality_display', r.get('municipality', 'Municipio'))}: "
            f"lluvia 24h {float(r.get('corrected_precip_24h_in', 0)):.2f} pulgadas, "
            f"riesgo {float(r.get('operational_risk_score', 0)):.0f} de 100, "
            f"viento {float(r.get('wind_speed_mph', 0)):.1f} mph desde {r.get('wind_direction_text', 'N/D')}."
        ),
        axis=1,
    )
    return out


def build_weather_animation(predictions: pd.DataFrame, *, generated_at_utc: str | None = None, minutes: int = 60, step_minutes: int = 5) -> pd.DataFrame:
    base = add_realtime_columns(predictions, generated_at_utc=generated_at_utc)
    if base.empty:
        return pd.DataFrame()
    generated = generated_at_utc or utc_now_iso()
    frame_minutes = list(range(0, max(step_minutes, minutes) + 1, step_minutes))
    rows: list[dict[str, Any]] = []
    for frame_index, minute in enumerate(frame_minutes):
        # Smooth pulse gives a radar-like animation without claiming new observations.
        pulse = 0.85 + 0.35 * math.sin((minute / max(1, minutes)) * math.pi * 2)
        for _, row in base.iterrows():
            rain_rate = max(0.0, float(row.get("rain_rate_est_in_hr", 0)) * pulse)
            wind_speed = max(0.0, float(row.get("wind_speed_mph", 0)) * (0.96 + 0.08 * math.cos(frame_index / 2)))
            risk = float(row.get("operational_risk_score", 0))
            rows.append({
                "generated_at_utc": generated,
                "frame_index": frame_index,
                "forecast_minute": minute,
                "time_label": f"+{minute:02d} min",
                "municipality": row.get("municipality"),
                "municipality_display": row.get("municipality_display", row.get("municipality")),
                "region": row.get("region"),
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "rain_frame_in_hr": round(rain_rate, 3),
                "rain_24h_in": round(float(row.get("corrected_precip_24h_in", 0)), 2),
                "wind_speed_mph": round(wind_speed, 1),
                "wind_dir_deg": row.get("wind_dir_deg"),
                "wind_direction_text": row.get("wind_direction_text"),
                "wind_arrow": row.get("wind_arrow"),
                "operational_risk_score": round(risk, 0),
                "impact_level": row.get("impact_level", "bajo"),
                "is_focus_municipality": bool(row.get("is_focus_municipality", False)),
                "screen_reader_label": row.get("weather_plain_text", ""),
            })
    return pd.DataFrame(rows)


def _nws_tsunami_alerts(nws_alerts: pd.DataFrame, generated_at_utc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if nws_alerts.empty:
        return rows
    for _, row in nws_alerts.iterrows():
        text = " ".join(str(row.get(c, "")) for c in ["event", "headline", "description", "instruction", "area_desc"])
        if "tsunami" not in text.lower():
            continue
        rows.append({
            "generated_at_utc": generated_at_utc,
            "hazard_type": "tsunami",
            "source": "NWS/NOAA CAP",
            "severity": str(row.get("severity", "alerta")) or "alerta",
            "status": str(row.get("status", "active")) or "active",
            "headline": str(row.get("headline") or row.get("event") or "Posible aviso de tsunami"),
            "municipality": str(row.get("area_desc", "Puerto Rico")),
            "lat": np.nan,
            "lon": np.nan,
            "recommended_action": "Seguir instrucciones oficiales de NWS, NOAA, Red Sísmica y manejo de emergencias. No usar este prototipo como fuente primaria.",
            "is_official": True,
            "confidence_note": "Alerta oficial leída desde CAP/NWS si está disponible.",
        })
    return rows


def _earthquake_alerts(earthquakes: pd.DataFrame, generated_at_utc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if earthquakes.empty:
        return rows
    for _, row in earthquakes.iterrows():
        mag = pd.to_numeric(pd.Series([row.get("magnitude")]), errors="coerce").iloc[0]
        tsunami_flag = int(float(row.get("tsunami", 0) or 0)) if str(row.get("tsunami", 0)).replace(".", "", 1).isdigit() else 0
        if pd.isna(mag) or float(mag) < 4.0:
            continue
        severity = "crítico" if float(mag) >= 6.5 or tsunami_flag else "alto" if float(mag) >= 5.0 else "vigilancia"
        rows.append({
            "generated_at_utc": generated_at_utc,
            "hazard_type": "terremoto",
            "source": str(row.get("source", "USGS")),
            "severity": severity,
            "status": str(row.get("status", "reviewed")),
            "headline": f"Evento sísmico M{float(mag):.1f}: {row.get('place', 'región de Puerto Rico')}",
            "municipality": "Puerto Rico",
            "lat": row.get("lat"),
            "lon": row.get("lon"),
            "recommended_action": "Consultar USGS y Red Sísmica de Puerto Rico. Si hay movimiento fuerte, seguir protocolos oficiales de seguridad.",
            "is_official": True,
            "confidence_note": "Evento sísmico de fuente oficial; la alerta temprana no es predicción previa.",
        })
    return rows


def _android_cluster_alerts(triggers: pd.DataFrame, generated_at_utc: str) -> list[dict[str, Any]]:
    cluster = evaluate_android_trigger_cluster(triggers) if triggers is not None and not triggers.empty else evaluate_android_trigger_cluster(pd.DataFrame())
    if cluster.get("cluster_status") != "posible señal colectiva":
        return []
    return [{
        "generated_at_utc": generated_at_utc,
        "hazard_type": "android_sensor_bridge",
        "source": "Android Sensor Bridge experimental",
        "severity": "vigilancia",
        "status": "requiere verificación oficial",
        "headline": f"Señal colectiva experimental: {cluster.get('trigger_count', 0)} teléfonos con posible movimiento.",
        "municipality": "zona aproximada",
        "lat": cluster.get("centroid_lat"),
        "lon": cluster.get("centroid_lon"),
        "recommended_action": "No emitir alerta pública automática. Validar con USGS, Red Sísmica de PR y fuentes oficiales.",
        "is_official": False,
        "confidence_note": "Señal agregada y anónima; inspirada en redes de acelerómetros tipo Android, no conectada al sistema privado de Google.",
    }]


def _weather_alerts(predictions: pd.DataFrame, generated_at_utc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if predictions.empty:
        return rows
    d = predictions.copy()
    d["operational_risk_score"] = pd.to_numeric(d.get("operational_risk_score", 0), errors="coerce").fillna(0)
    top = d[d["operational_risk_score"] >= 65].sort_values("operational_risk_score", ascending=False).head(8)
    for _, row in top.iterrows():
        rows.append({
            "generated_at_utc": generated_at_utc,
            "hazard_type": "lluvia/viento",
            "source": "PR-WX v0.9 experimental",
            "severity": "alto" if float(row.get("operational_risk_score", 0)) < 80 else "crítico",
            "status": "experimental",
            "headline": f"Riesgo meteorológico elevado en {row.get('municipality_display', row.get('municipality'))}",
            "municipality": row.get("municipality_display", row.get("municipality")),
            "lat": row.get("lat"),
            "lon": row.get("lon"),
            "recommended_action": "Revisar NWS San Juan y fuentes oficiales antes de tomar decisiones.",
            "is_official": False,
            "confidence_note": "Índice experimental; apoyo visual, no aviso oficial.",
        })
    return rows


def build_safety_alerts(
    predictions: pd.DataFrame,
    earthquakes: pd.DataFrame,
    nws_alerts: pd.DataFrame,
    android_triggers: pd.DataFrame,
    *,
    generated_at_utc: str | None = None,
) -> pd.DataFrame:
    generated = generated_at_utc or utc_now_iso()
    rows: list[dict[str, Any]] = []
    rows.extend(_nws_tsunami_alerts(nws_alerts, generated))
    rows.extend(_earthquake_alerts(earthquakes, generated))
    rows.extend(_android_cluster_alerts(android_triggers, generated))
    rows.extend(_weather_alerts(predictions, generated))
    if not rows:
        return pd.DataFrame(columns=SAFETY_COLUMNS)
    out = pd.DataFrame(rows)
    for col in SAFETY_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    severity_order = {"crítico": 5, "critical": 5, "alto": 4, "severe": 4, "alerta": 3, "vigilancia": 2, "moderado": 2, "bajo": 1}
    out["severity_rank"] = out["severity"].astype(str).str.lower().map(severity_order).fillna(1)
    return out.sort_values(["severity_rank", "hazard_type"], ascending=[False, True]).drop(columns=["severity_rank"])


def build_realtime_summary(predictions: pd.DataFrame, safety_alerts: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    base_summary = build_accessible_summary(predictions, generated_at_utc=generated_at_utc)
    alert_count = 0 if safety_alerts is None or safety_alerts.empty else int(len(safety_alerts))
    tsunami_count = 0 if safety_alerts is None or safety_alerts.empty else int((safety_alerts["hazard_type"].astype(str).str.lower() == "tsunami").sum())
    earthquake_count = 0 if safety_alerts is None or safety_alerts.empty else int((safety_alerts["hazard_type"].astype(str).str.lower() == "terremoto").sum())
    focus = focus_municipalities_table(predictions)
    base_summary.update({
        "model_version": "0.9.0",
        "realtime_interval_seconds": 60,
        "headline": "Centro PR-WX v0.9 en modo actualización cada minuto.",
        "alert_count": alert_count,
        "earthquake_alert_count": earthquake_count,
        "tsunami_alert_count": tsunami_count,
        "focus_order": FOCUS_ORDER,
        "focus_weather": focus.to_dict(orient="records") if not focus.empty else [],
        "plain_language_summary": (
            f"El panel se actualiza cada minuto y muestra lluvia, viento, terremotos y posible tsunami en lectura clara. "
            f"Hay {alert_count} alertas o señales relevantes en la tabla de seguridad. "
            f"Los pueblos de prioridad son Juana Díaz, Ponce, San Juan y San Germán. "
            "Las señales Android son experimentales y deben validarse con fuentes oficiales."
        ),
        "wave_accessibility_notes": list(base_summary.get("wave_accessibility_notes", [])) + [
            "La animación tiene una alternativa textual en tabla para cumplir mejor con accesibilidad.",
            "El panel incluye aviso de reducir movimiento para usuarios sensibles a animaciones.",
            "Las alertas no dependen solo de color; incluyen texto, severidad y acción sugerida.",
        ],
    })
    return base_summary


def write_realtime_v9_artifacts(root: Path, *, generated_at_utc: str | None = None) -> dict[str, str]:
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    generated = generated_at_utc or utc_now_iso()

    pred = pd.DataFrame()
    for name in ["live_predictions_v8.csv", "live_predictions_v6.csv", "live_predictions_v5.csv", "live_predictions.csv"]:
        pred = _safe_read_csv(processed / name)
        if not pred.empty:
            break
    pred_v9 = add_realtime_columns(pred, generated_at_utc=generated)
    animation = build_weather_animation(pred_v9, generated_at_utc=generated, minutes=60, step_minutes=5)
    earthquakes = _safe_read_csv(processed / "live_earthquakes_v7.csv")
    nws_alerts = _safe_read_csv(processed / "live_nws_alerts.csv")
    android_triggers = _safe_read_csv(processed / "android_triggers_sample_v7.csv")
    safety = build_safety_alerts(pred_v9, earthquakes, nws_alerts, android_triggers, generated_at_utc=generated)
    summary = build_realtime_summary(pred_v9, safety, generated)

    pred_path = processed / "live_predictions_v9.csv"
    animation_path = processed / "weather_animation_v9.csv"
    safety_path = processed / "safety_alerts_v9.csv"
    summary_path = processed / "realtime_summary_v9.json"
    focus_path = processed / "focus_municipalities_v9.csv"

    pred_v9.to_csv(pred_path, index=False)
    animation.to_csv(animation_path, index=False)
    safety.to_csv(safety_path, index=False)
    focus_municipalities_table(pred_v9).to_csv(focus_path, index=False)
    _write_json(summary_path, summary)
    return {
        "predictions_v9": str(pred_path),
        "weather_animation_v9": str(animation_path),
        "safety_alerts_v9": str(safety_path),
        "realtime_summary_v9": str(summary_path),
        "focus_municipalities_v9": str(focus_path),
    }
