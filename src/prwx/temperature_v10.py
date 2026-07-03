from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .accessibility import focus_municipalities_table
from .realtime_v9 import add_realtime_columns, build_weather_animation, utc_now_iso

FOCUS_ORDER = ["Juana Díaz", "Ponce", "San Juan", "San Germán"]
TEMP_COLUMNS = [
    "generated_at_utc", "municipality", "municipality_display", "region", "lat", "lon",
    "temperature_f", "feels_like_f", "relative_humidity", "heat_risk_level",
    "heat_action", "temperature_plain_text", "is_focus_municipality",
]


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def heat_risk_level(feels_like_f: float | int | None) -> str:
    try:
        value = float(feels_like_f)
    except Exception:
        return "no disponible"
    if value >= 108:
        return "crítico"
    if value >= 103:
        return "alto"
    if value >= 95:
        return "moderado"
    if value >= 90:
        return "vigilancia"
    return "bajo"


def heat_action(level: str) -> str:
    text = str(level or "").lower()
    if text in {"crítico", "critico"}:
        return "Evitar exposición al calor, activar pausas de hidratación y revisar avisos oficiales."
    if text == "alto":
        return "Reducir actividades al aire libre, vigilar adultos mayores, niños y personas con condiciones de salud."
    if text == "moderado":
        return "Mantener hidratación, sombra y monitoreo de sensación térmica."
    if text == "vigilancia":
        return "Observar cambios durante la tarde y preparar comunicación preventiva si aumenta el calor."
    if text == "bajo":
        return "Monitoreo normal."
    return "Verificar datos de temperatura y fuentes oficiales."


def add_temperature_columns(predictions: pd.DataFrame, *, generated_at_utc: str | None = None) -> pd.DataFrame:
    """Add clear temperature fields for v1.0 dashboard and API.

    The NWS live connector already collects base_temp_f and relative_humidity when
    available. This layer makes the values visible, accessible and sortable. If a
    data source is unavailable, it uses conservative fallback fields so the page
    remains readable instead of failing.
    """
    if predictions is None or predictions.empty:
        return pd.DataFrame(columns=TEMP_COLUMNS)
    out = add_realtime_columns(predictions, generated_at_utc=generated_at_utc).copy()
    generated = generated_at_utc or str(out.get("generated_at_utc", pd.Series([utc_now_iso()])).iloc[0] or utc_now_iso())

    if "base_temp_f" in out.columns:
        temp = pd.to_numeric(out["base_temp_f"], errors="coerce")
    elif "temperature_f" in out.columns:
        temp = pd.to_numeric(out["temperature_f"], errors="coerce")
    else:
        temp = pd.Series(np.nan, index=out.index)
    # Coastal and southern fallback is intentionally warm because PR heat risk is
    # operationally important; the source_status field still tells the user when
    # live data failed.
    region = out.get("region", pd.Series([""] * len(out), index=out.index)).astype(str).str.lower()
    fallback = pd.Series(86.0, index=out.index)
    fallback = fallback.mask(region.str.contains("south|sur|coast|costa", regex=True, na=False), 89.0)
    fallback = fallback.mask(region.str.contains("central|mountain|montaña|montana", regex=True, na=False), 81.0)
    out["temperature_f"] = temp.fillna(fallback).round(1)

    if "base_heat_index_f" in out.columns:
        feels = pd.to_numeric(out["base_heat_index_f"], errors="coerce")
    elif "heat_index_f" in out.columns:
        feels = pd.to_numeric(out["heat_index_f"], errors="coerce")
    else:
        feels = pd.Series(np.nan, index=out.index)
    humidity = pd.to_numeric(out.get("relative_humidity", pd.Series([np.nan] * len(out), index=out.index)), errors="coerce").fillna(75)
    simple_feels_like = out["temperature_f"] + np.maximum(0, humidity - 60) * 0.18
    out["feels_like_f"] = feels.fillna(simple_feels_like).round(1)
    out["relative_humidity"] = humidity.round(0).astype(int)
    out["heat_risk_level"] = out["feels_like_f"].map(heat_risk_level)
    out["heat_action"] = out["heat_risk_level"].map(heat_action)
    out["generated_at_utc"] = generated
    out["temperature_version"] = "1.0.0"
    out["temperature_plain_text"] = out.apply(
        lambda r: (
            f"{r.get('municipality_display', r.get('municipality', 'Municipio'))}: "
            f"temperatura {float(r.get('temperature_f', 0)):.1f} °F, "
            f"sensación térmica {float(r.get('feels_like_f', 0)):.1f} °F, "
            f"humedad {int(float(r.get('relative_humidity', 0)))} %, "
            f"riesgo de calor {r.get('heat_risk_level', 'no disponible')}. "
            f"{r.get('heat_action', '')}"
        ),
        axis=1,
    )
    out["weather_plain_text"] = out.apply(
        lambda r: (
            f"{r.get('municipality_display', r.get('municipality', 'Municipio'))}: "
            f"temperatura {float(r.get('temperature_f', 0)):.1f} °F, "
            f"sensación {float(r.get('feels_like_f', 0)):.1f} °F, "
            f"lluvia 24h {float(r.get('corrected_precip_24h_in', 0)):.2f} pulgadas, "
            f"viento {float(r.get('wind_speed_mph', 0)):.1f} mph desde {r.get('wind_direction_text', 'N/D')}, "
            f"riesgo operacional {float(r.get('operational_risk_score', 0)):.0f} de 100."
        ),
        axis=1,
    )
    out["screen_reader_label"] = out["weather_plain_text"]
    return out


def build_temperature_table(predictions: pd.DataFrame, *, generated_at_utc: str | None = None) -> pd.DataFrame:
    out = add_temperature_columns(predictions, generated_at_utc=generated_at_utc)
    if out.empty:
        return pd.DataFrame(columns=TEMP_COLUMNS)
    cols = [c for c in TEMP_COLUMNS if c in out.columns]
    return out[cols].sort_values(["is_focus_municipality", "feels_like_f"], ascending=[False, False])


def build_weather_animation_v10(predictions: pd.DataFrame, *, generated_at_utc: str | None = None) -> pd.DataFrame:
    base = add_temperature_columns(predictions, generated_at_utc=generated_at_utc)
    anim = build_weather_animation(base, generated_at_utc=generated_at_utc, minutes=60, step_minutes=5)
    if anim.empty or base.empty:
        return anim
    temp_cols = base[["municipality", "temperature_f", "feels_like_f", "heat_risk_level", "temperature_plain_text"]].copy()
    merged = anim.merge(temp_cols, on="municipality", how="left")
    # Gentle visible pulse for map animation; keeps the same forecast source.
    merged["temperature_frame_f"] = (
        pd.to_numeric(merged["temperature_f"], errors="coerce").fillna(86)
        + np.sin(pd.to_numeric(merged["forecast_minute"], errors="coerce").fillna(0) / 60 * np.pi) * 1.2
    ).round(1)
    merged["screen_reader_label"] = merged.apply(
        lambda r: (
            f"{r.get('municipality_display', r.get('municipality', 'Municipio'))}: "
            f"lluvia {float(r.get('rain_frame_in_hr', 0)):.3f} pulgadas por hora, "
            f"viento {float(r.get('wind_speed_mph', 0)):.1f} mph, "
            f"temperatura {float(r.get('temperature_frame_f', 0)):.1f} °F, "
            f"sensación {float(r.get('feels_like_f', 0)):.1f} °F."
        ),
        axis=1,
    )
    return merged


def build_v10_realtime_summary(predictions: pd.DataFrame, safety_alerts: pd.DataFrame | None, generated_at_utc: str) -> dict[str, Any]:
    out = add_temperature_columns(predictions, generated_at_utc=generated_at_utc)
    if out.empty:
        return {
            "generated_at_utc": generated_at_utc,
            "model_version": "1.0.0",
            "headline": "No hay datos visibles todavía.",
            "plain_language_summary": "Ejecute la actualización v1.0 para crear temperatura, lluvia, viento y alertas.",
            "recommendations_to_improve": [],
        }
    focus = focus_municipalities_table(out)
    hottest = out.sort_values("feels_like_f", ascending=False).iloc[0]
    max_temp = float(pd.to_numeric(out["temperature_f"], errors="coerce").max())
    max_feels = float(pd.to_numeric(out["feels_like_f"], errors="coerce").max())
    max_rain = float(pd.to_numeric(out["corrected_precip_24h_in"], errors="coerce").fillna(0).max())
    max_wind = float(pd.to_numeric(out["wind_speed_mph"], errors="coerce").fillna(0).max())
    alert_count = 0 if safety_alerts is None or safety_alerts.empty else int(len(safety_alerts))
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.0.0",
        "headline": f"Vista v1.0: temperatura visible por pueblo; {hottest.get('municipality_display')} tiene la sensación térmica más alta.",
        "plain_language_summary": (
            f"El panel muestra temperatura, sensación térmica, lluvia, viento y alertas cada minuto. "
            f"La temperatura máxima visible es {max_temp:.1f} °F, la sensación térmica máxima es {max_feels:.1f} °F, "
            f"la lluvia máxima de 24 horas es {max_rain:.2f} pulgadas y el viento máximo es {max_wind:.1f} mph. "
            "Juana Díaz, Ponce, San Juan y San Germán aparecen primero para facilitar la revisión local."
        ),
        "alert_count": alert_count,
        "focus_weather": focus.to_dict(orient="records") if not focus.empty else [],
        "recommendations_to_improve": [
            "Añadir radar MRMS real por capas para lluvia de 1h, 3h y 24h.",
            "Integrar NOAA/NWS alerts con notificación sonora opcional y accesible.",
            "Añadir un modo kiosco para sala de monitoreo en pantalla grande.",
            "Crear notificaciones web push para Juana Díaz, Ponce, San Juan y San Germán.",
            "Conectar sensores IoT locales de lluvia, temperatura y presión barométrica en recintos o municipios.",
            "Añadir pronóstico por hora con tarjetas de mañana, tarde y noche.",
            "Crear mini app Android propia para señales anónimas de acelerómetro, respetando privacidad.",
            "Integrar Red Sísmica de Puerto Rico y NOAA Tsunami como fuentes oficiales visibles.",
        ],
        "wave_accessibility_notes": [
            "La temperatura se muestra con número, etiqueta y explicación textual, no solo con color.",
            "El mapa animado tiene tabla equivalente para lectores de pantalla.",
            "La página ofrece reducir animación para usuarios sensibles al movimiento.",
            "Los pueblos prioritarios se presentan en tarjetas y en tabla descargable.",
            "Los avisos incluyen acción sugerida y fuente para evitar ambigüedad.",
        ],
    }


def write_realtime_v10_artifacts(root: Path, *, generated_at_utc: str | None = None) -> dict[str, str]:
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    generated = generated_at_utc or utc_now_iso()

    pred = pd.DataFrame()
    for name in ["live_predictions_v9.csv", "live_predictions_v8.csv", "live_predictions_v6.csv", "live_predictions_v5.csv", "live_predictions.csv"]:
        pred = _safe_read_csv(processed / name)
        if not pred.empty:
            break
    pred_v10 = add_temperature_columns(pred, generated_at_utc=generated)
    animation = build_weather_animation_v10(pred_v10, generated_at_utc=generated)
    temp_table = build_temperature_table(pred_v10, generated_at_utc=generated)
    safety = _safe_read_csv(processed / "safety_alerts_v9.csv")
    summary = build_v10_realtime_summary(pred_v10, safety, generated)

    pred_path = processed / "live_predictions_v10.csv"
    animation_path = processed / "weather_animation_v10.csv"
    temp_path = processed / "temperature_municipalities_v10.csv"
    focus_temp_path = processed / "focus_temperature_v10.csv"
    summary_path = processed / "realtime_summary_v10.json"

    pred_v10.to_csv(pred_path, index=False)
    animation.to_csv(animation_path, index=False)
    temp_table.to_csv(temp_path, index=False)
    focus_municipalities_table(pred_v10).to_csv(focus_temp_path, index=False)
    _write_json(summary_path, summary)
    return {
        "predictions_v10": str(pred_path),
        "weather_animation_v10": str(animation_path),
        "temperature_municipalities_v10": str(temp_path),
        "focus_temperature_v10": str(focus_temp_path),
        "realtime_summary_v10": str(summary_path),
    }
