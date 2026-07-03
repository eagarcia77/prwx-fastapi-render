from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .immersive import add_immersive_columns

FOCUS_MUNICIPALITIES = ["Juana Diaz", "Ponce", "San Juan", "San German"]
FOCUS_DISPLAY_NAMES = {
    "juana diaz": "Juana Díaz",
    "ponce": "Ponce",
    "san juan": "San Juan",
    "san german": "San Germán",
}
FOCUS_REASONS = {
    "juana diaz": "pueblo prioritario del usuario; zona sur con riesgo de calor, lluvia intensa localizada y escorrentías rápidas",
    "ponce": "ciudad principal del sur; vulnerabilidad a lluvia extrema, calor, crecidas urbanas y eventos costeros",
    "san juan": "zona metropolitana; alta exposición poblacional, operación institucional y carreteras críticas",
    "san german": "zona oeste/suroeste; relevancia institucional y exposición a lluvia orográfica/local",
}

IMPACT_EXPLAINERS = {
    "bajo": "Condición general baja. Mantener monitoreo de rutina.",
    "vigilancia": "Condición que merece observación. Preparar comunicación preventiva si el evento aumenta.",
    "moderado": "Puede afectar movilidad, actividades al aire libre o zonas inundables. Revisar avisos oficiales.",
    "alto": "Riesgo operacional elevado. Revisar operación presencial, ríos, carreteras y avisos oficiales.",
    "crítico": "Escenario severo. Contrastar inmediatamente con NWS, manejo de emergencias y autoridades locales.",
}

ACTION_EXPLAINERS = {
    1: "Monitoreo normal",
    2: "Vigilancia normal",
    3: "Preparar comunicación preventiva",
    4: "Monitoreo intensivo",
    5: "Revisar operación presencial y rutas críticas",
}


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def is_focus_municipality(value: Any) -> bool:
    return normalize_text(value) in {normalize_text(x) for x in FOCUS_MUNICIPALITIES}


def focus_display_name(value: Any) -> str:
    key = normalize_text(value)
    return FOCUS_DISPLAY_NAMES.get(key, str(value or ""))


def plain_language_risk(row: pd.Series) -> str:
    muni = focus_display_name(row.get("municipality"))
    risk = float(row.get("operational_risk_score", 0) or 0)
    precip = float(row.get("corrected_precip_24h_in", 0) or 0)
    impact = str(row.get("impact_level", "bajo") or "bajo").lower()
    priority = int(float(row.get("action_priority", 1) or 1))
    action = ACTION_EXPLAINERS.get(priority, "Monitoreo")
    detail = IMPACT_EXPLAINERS.get(impact, "Revisar el panel y fuentes oficiales.")
    return (
        f"{muni}: riesgo {risk:.0f} de 100, lluvia estimada {precip:.2f} pulgadas en 24 horas. "
        f"Nivel {impact}. Acción sugerida: {action}. {detail}"
    )


def add_accessibility_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add clear-language and WAVE-friendly display fields.

    These fields do not alter the meteorological prediction. They make the
    output easier to read, sort, explain, export and validate visually.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    out = add_immersive_columns(df).copy()
    if "municipality" not in out.columns:
        out["municipality"] = "Puerto Rico"
    out["municipality_display"] = out["municipality"].map(focus_display_name)
    out["is_focus_municipality"] = out["municipality"].map(is_focus_municipality)
    out["focus_reason"] = out["municipality"].map(lambda x: FOCUS_REASONS.get(normalize_text(x), ""))
    out["priority_group"] = out["is_focus_municipality"].map(lambda x: "Pueblos prioritarios" if x else "Otros municipios")
    out["impact_explained"] = out.get("impact_level", pd.Series(["bajo"] * len(out))).astype(str).str.lower().map(IMPACT_EXPLAINERS).fillna("Revisar el panel y fuentes oficiales.")
    out["action_explained"] = out.get("action_priority", pd.Series([1] * len(out))).fillna(1).astype(float).astype(int).map(ACTION_EXPLAINERS).fillna("Monitoreo")
    out["plain_language_summary"] = out.apply(plain_language_risk, axis=1)
    out["screen_reader_label"] = out["plain_language_summary"]
    out["accessible_version"] = "0.8.0"
    return out


def focus_municipalities_table(df: pd.DataFrame) -> pd.DataFrame:
    out = add_accessibility_columns(df)
    if out.empty:
        return out
    focus = out[out["is_focus_municipality"]].copy()
    # Preserve user-specified order rather than risk-only order.
    order = {normalize_text(name): i for i, name in enumerate(FOCUS_MUNICIPALITIES)}
    focus["_focus_order"] = focus["municipality"].map(lambda x: order.get(normalize_text(x), 99))
    return focus.sort_values(["_focus_order"]).drop(columns=["_focus_order"], errors="ignore")


def build_accessible_summary(df: pd.DataFrame, *, generated_at_utc: str | None = None) -> dict[str, Any]:
    out = add_accessibility_columns(df)
    generated = generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if out.empty:
        return {
            "generated_at_utc": generated,
            "headline": "No hay datos disponibles.",
            "plain_language_summary": "Ejecuta la actualización operacional para generar datos claros.",
            "focus_municipalities": [],
            "wave_accessibility_notes": [],
            "model_version": "0.8.0",
        }
    ranked = out.sort_values(["is_focus_municipality", "action_priority", "operational_risk_score"], ascending=False)
    top = ranked.iloc[0]
    focus = focus_municipalities_table(out)
    focus_summaries = focus[[
        "municipality_display", "region", "corrected_precip_24h_in", "operational_risk_score",
        "impact_level", "action_explained", "focus_reason", "plain_language_summary",
    ]].to_dict(orient="records")
    high = int((out.get("operational_risk_score", pd.Series(dtype=float)) >= 55).sum())
    max_precip = float(out.get("corrected_precip_24h_in", pd.Series([0])).max())
    headline = f"Lectura rápida: {focus_display_name(top.get('municipality'))} requiere la primera revisión del panel."
    summary = (
        f"Hay {len(out)} municipios visibles. La lluvia máxima corregida es {max_precip:.2f} pulgadas en 24 horas. "
        f"{high} municipios tienen riesgo 55 o mayor. Los pueblos destacados son Juana Díaz, Ponce, San Juan y San Germán. "
        "Use esta vista como apoyo educativo y operacional; verifique siempre NWS San Juan, USGS, Red Sísmica de Puerto Rico y autoridades oficiales."
    )
    return {
        "generated_at_utc": generated,
        "headline": headline,
        "plain_language_summary": summary,
        "focus_municipalities": focus_summaries,
        "wave_accessibility_notes": [
            "Se usa texto visible junto a color; el color no es la única señal de riesgo.",
            "Las tablas tienen columnas con nombres claros y descargables en CSV.",
            "Los controles tienen etiquetas descriptivas y lenguaje llano.",
            "La vista ofrece modo de lectura rápida para reducir carga cognitiva.",
            "Se evita depender exclusivamente de mapas o gráficas 3D para comunicar riesgo.",
        ],
        "model_version": "0.8.0",
    }


def write_accessible_artifacts(predictions: pd.DataFrame, root: Path, *, generated_at_utc: str | None = None) -> dict[str, str]:
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    annotated = add_accessibility_columns(predictions)
    focus = focus_municipalities_table(annotated)
    summary = build_accessible_summary(annotated, generated_at_utc=generated_at_utc)

    pred_path = processed / "live_predictions_v8.csv"
    focus_path = processed / "focus_municipalities_v8.csv"
    summary_path = processed / "accessible_summary_v8.json"
    annotated.to_csv(pred_path, index=False)
    focus.to_csv(focus_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "predictions_v8": str(pred_path),
        "focus_municipalities_v8": str(focus_path),
        "accessible_summary_v8": str(summary_path),
    }
