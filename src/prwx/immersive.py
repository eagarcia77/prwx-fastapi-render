from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .risk import add_risk_columns


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    return str(value)


def add_immersive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add operational-digital-twin fields for PR-WX v0.6.

    These columns do not claim new physical observations; they transform the
    model output into impact-oriented indicators for visualization, scenarios,
    briefing and API use.
    """
    out = df.copy()
    if "operational_risk_score" not in out.columns or "impact_level" not in out.columns:
        out = add_risk_columns(out)

    if "corrected_precip_24h_in" not in out.columns and "base_precip_24h_in" in out.columns:
        out["corrected_precip_24h_in"] = out["base_precip_24h_in"]

    precip = out.get("corrected_precip_24h_in", pd.Series([0] * len(out))).fillna(0).astype(float)
    risk = out.get("operational_risk_score", pd.Series([0] * len(out))).fillna(0).astype(float)
    spread = out.get("ensemble_spread_in", pd.Series([0] * len(out))).fillna(0).astype(float)
    p90 = out.get("precip_p90_in", precip).fillna(precip).astype(float)
    p10 = out.get("precip_p10_in", precip).fillna(precip).astype(float)

    # Visualization height for 3D towers: scaled enough to look immersive, not
    # a physical altitude. Label explicitly in dashboard.
    out["immersive_tower_height"] = (precip * 130 + risk * 4 + spread * 90).clip(lower=15, upper=1200).round(1)
    out["uncertainty_band_in"] = (p90 - p10).clip(lower=0).round(2)
    out["confidence_score"] = (100 - (spread * 18 + out["uncertainty_band_in"] * 9)).clip(lower=35, upper=98).round(0)

    def priority(row: pd.Series) -> int:
        score = _num(row.get("operational_risk_score"))
        alerts = _num(row.get("active_nws_alerts"))
        qpe = _num(row.get("mrms_qpe_24h_in"))
        if score >= 75 or _text(row.get("impact_level")) == "crítico":
            return 5
        if score >= 55 or alerts > 0:
            return 4
        if score >= 35 or qpe >= 2:
            return 3
        if score >= 18:
            return 2
        return 1

    out["action_priority"] = out.apply(priority, axis=1)
    out["school_ops_signal"] = out["action_priority"].map({
        5: "revisar operación presencial",
        4: "monitoreo intensivo",
        3: "preparar comunicación preventiva",
        2: "vigilancia normal",
        1: "operación normal",
    })
    out["road_flood_signal"] = np.where((precip >= 2.0) | (risk >= 45), "vigilar carreteras inundables", "sin señal crítica")
    out["river_signal"] = np.where((_num_series(out, "nearby_gage_stage_ft") >= 8) | (risk >= 55), "vigilar ríos/quebradas", "sin señal crítica")
    out["heat_signal"] = np.where(_num_series(out, "base_heat_index_f") >= 102, "calor peligroso", np.where(_num_series(out, "base_heat_index_f") >= 95, "calor moderado", "sin señal crítica"))
    out["ai_zone_label"] = out.apply(lambda r: f"{_text(r.get('region'), 'PR')} / prioridad {int(_num(r.get('action_priority'), 1))}", axis=1)
    out["immersive_version"] = "0.6.0"
    return out


def _num_series(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def compute_idw_grid(
    df: pd.DataFrame,
    *,
    value_col: str = "operational_risk_score",
    resolution: float = 0.055,
    power: float = 2.0,
    bounds: tuple[float, float, float, float] = (17.84, 18.55, -67.32, -65.18),
) -> pd.DataFrame:
    """Create a lightweight interpolated PR grid using inverse distance weighting.

    The grid is intended for immersive visualization only. It should not be used
    as a replacement for radar grids, hydrologic models or official warnings.
    """
    if df.empty or value_col not in df.columns:
        return pd.DataFrame(columns=["lat", "lon", value_col, "grid_kind"])
    points = df[["lat", "lon", value_col]].dropna().copy()
    if points.empty:
        return pd.DataFrame(columns=["lat", "lon", value_col, "grid_kind"])

    lat_min, lat_max, lon_min, lon_max = bounds
    lats = np.arange(lat_min, lat_max + resolution, resolution)
    lons = np.arange(lon_min, lon_max + resolution, resolution)
    plat = points["lat"].to_numpy(dtype=float)
    plon = points["lon"].to_numpy(dtype=float)
    pval = points[value_col].to_numpy(dtype=float)

    rows: list[dict[str, float | str]] = []
    for lat in lats:
        for lon in lons:
            # Rough mask around the Puerto Rico main island and near islands.
            # It trims far ocean points while keeping a clean broad digital twin.
            island_core = ((lat - 18.20) / 0.42) ** 2 + ((lon + 66.25) / 1.15) ** 2 <= 1.15
            west_core = ((lat - 18.12) / 0.25) ** 2 + ((lon + 67.05) / 0.30) ** 2 <= 1.0
            east_core = ((lat - 18.15) / 0.25) ** 2 + ((lon + 65.45) / 0.35) ** 2 <= 1.0
            if not (island_core or west_core or east_core):
                continue
            d2 = (plat - lat) ** 2 + (plon - lon) ** 2
            weights = 1.0 / np.power(d2 + 1e-7, power / 2)
            val = float(np.sum(weights * pval) / np.sum(weights))
            rows.append({"lat": round(float(lat), 5), "lon": round(float(lon), 5), value_col: round(val, 3), "grid_kind": "idw_visual"})
    return pd.DataFrame(rows)


def predictions_to_geojson(df: pd.DataFrame) -> dict[str, Any]:
    features = []
    for _, row in df.iterrows():
        try:
            lat = float(row.get("lat"))
            lon = float(row.get("lon"))
        except Exception:
            continue
        props = {}
        for col in df.columns:
            if col in {"lat", "lon"}:
                continue
            value = row.get(col)
            if isinstance(value, (np.integer, np.floating)):
                value = float(value)
            elif pd.isna(value):
                value = None
            props[col] = value
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def build_briefing(df: pd.DataFrame, meta: dict[str, Any] | None = None, *, top_n: int = 8) -> dict[str, Any]:
    out = add_immersive_columns(df)
    meta = meta or {}
    generated = meta.get("generated_at_utc") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if out.empty:
        return {
            "generated_at_utc": generated,
            "headline": "Sin predicciones disponibles.",
            "executive_summary": "Ejecuta el flujo operacional para generar el briefing.",
            "top_municipalities": [],
            "regional_summary": [],
            "recommended_actions": [],
            "model_version": "0.6.0",
        }

    ranked = out.sort_values(["action_priority", "operational_risk_score", "corrected_precip_24h_in"], ascending=False).head(top_n)
    max_risk = float(out["operational_risk_score"].max())
    max_row = ranked.iloc[0]
    max_muni = _text(max_row.get("municipality"), "Puerto Rico")
    max_precip = _num(max_row.get("corrected_precip_24h_in"))
    impact = _text(max_row.get("impact_level"), "N/D")

    if max_risk >= 75:
        headline = f"Riesgo crítico localizado: {max_muni} encabeza el escenario operacional."
    elif max_risk >= 55:
        headline = f"Riesgo alto localizado: vigilancia reforzada para {max_muni}."
    elif max_risk >= 35:
        headline = f"Riesgo moderado: lluvias relevantes posibles en {max_muni} y zonas cercanas."
    elif max_risk >= 18:
        headline = "Vigilancia preventiva: condiciones variables por región."
    else:
        headline = "Escenario general bajo, con monitoreo rutinario recomendado."

    executive_summary = (
        f"El sistema v0.6 estima una lluvia máxima corregida de {max_precip:.2f} pulgadas en 24 horas, "
        f"con nivel de impacto '{impact}' para {max_muni}. La lectura combina pronóstico base, corrección local, "
        "incertidumbre, señales hidrológicas, MRMS/USGS cuando están disponibles y alertas NWS activas. "
        "Este resumen es experimental y debe contrastarse con fuentes oficiales."
    )

    top = []
    for _, r in ranked.iterrows():
        top.append({
            "municipality": _text(r.get("municipality")),
            "region": _text(r.get("region")),
            "corrected_precip_24h_in": round(_num(r.get("corrected_precip_24h_in")), 2),
            "operational_risk_score": round(_num(r.get("operational_risk_score")), 1),
            "impact_level": _text(r.get("impact_level")),
            "action_priority": int(_num(r.get("action_priority"), 1)),
            "school_ops_signal": _text(r.get("school_ops_signal")),
            "road_flood_signal": _text(r.get("road_flood_signal")),
            "confidence_score": round(_num(r.get("confidence_score")), 0),
        })

    regional = []
    if "region" in out.columns:
        grouped = out.groupby("region", dropna=False).agg(
            municipalities=("municipality", "count"),
            max_risk=("operational_risk_score", "max"),
            avg_risk=("operational_risk_score", "mean"),
            max_precip=("corrected_precip_24h_in", "max"),
            priority_max=("action_priority", "max"),
        ).reset_index().sort_values("max_risk", ascending=False)
        regional = grouped.round(2).to_dict(orient="records")

    actions = [
        "Comparar este panel con avisos oficiales de NWS San Juan antes de tomar decisiones.",
        "Vigilar municipios con prioridad 4 o 5, especialmente si hay quebradas, ríos urbanos o carreteras inundables.",
        "Actualizar el flujo cada 30 minutos durante eventos convectivos, ondas tropicales o lluvias orográficas.",
        "Usar el simulador de escenarios para evaluar sensibilidad ante más lluvia, mayor saturación del suelo o calor extremo.",
    ]

    return {
        "generated_at_utc": generated,
        "headline": headline,
        "executive_summary": executive_summary,
        "top_municipalities": top,
        "regional_summary": regional,
        "recommended_actions": actions,
        "model_version": "0.6.0",
    }


def simulate_scenario(
    df: pd.DataFrame,
    *,
    rain_multiplier: float = 1.0,
    soil_saturation_boost: float = 0.0,
    heat_boost_f: float = 0.0,
    alert_override: int | None = None,
) -> pd.DataFrame:
    """Run a simple what-if scenario over current predictions.

    The scenario is a decision-support visualization. It does not retrain the ML
    model; it perturbs the operational variables and recalculates risk.
    """
    out = df.copy()
    if "corrected_precip_24h_in" not in out.columns:
        out["corrected_precip_24h_in"] = _num_series(out, "base_precip_24h_in")
    out["corrected_precip_24h_in"] = (_num_series(out, "corrected_precip_24h_in") * float(rain_multiplier)).clip(lower=0)
    if "precip_p90_in" in out.columns:
        out["precip_p90_in"] = (_num_series(out, "precip_p90_in") * float(rain_multiplier)).clip(lower=0)
    if "mrms_qpe_24h_in" in out.columns:
        out["mrms_qpe_24h_in"] = (_num_series(out, "mrms_qpe_24h_in") + float(soil_saturation_boost)).clip(lower=0)
    else:
        out["mrms_qpe_24h_in"] = float(soil_saturation_boost)
    if "base_heat_index_f" in out.columns:
        out["base_heat_index_f"] = _num_series(out, "base_heat_index_f") + float(heat_boost_f)
    else:
        out["base_heat_index_f"] = 90 + float(heat_boost_f)
    if alert_override is not None:
        out["active_nws_alerts"] = int(alert_override)
    out = add_risk_columns(out)
    out = add_immersive_columns(out)
    return out


def write_immersive_artifacts(df: pd.DataFrame, root: Path, meta: dict[str, Any] | None = None) -> dict[str, str]:
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    enriched = add_immersive_columns(df)
    v6_path = processed / "live_predictions_v6.csv"
    grid_path = processed / "immersive_grid_v6.csv"
    briefing_path = processed / "prwx_briefing_v6.json"
    geojson_path = processed / "live_predictions_v6.geojson"

    enriched.to_csv(v6_path, index=False)
    compute_idw_grid(enriched, value_col="operational_risk_score").to_csv(grid_path, index=False)
    briefing = build_briefing(enriched, meta=meta)
    briefing_path.write_text(json.dumps(briefing, ensure_ascii=False, indent=2), encoding="utf-8")
    geojson_path.write_text(json.dumps(predictions_to_geojson(enriched), ensure_ascii=False), encoding="utf-8")
    return {
        "predictions_v6": str(v6_path),
        "immersive_grid_v6": str(grid_path),
        "briefing_v6": str(briefing_path),
        "geojson_v6": str(geojson_path),
    }
