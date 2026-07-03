from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class LifeSafetyResult:
    status: str
    generated_at_utc: str
    actions_path: str
    municipal_path: str
    summary_path: str
    message: str


FOCUS_TOWNS = ["Juana Díaz", "Ponce", "San Juan", "San Germán"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def build_life_safety_actions(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    rows = [
        ("inundacion", "alto", "Activar monitoreo de ríos, quebradas, carreteras bajas y zonas con historial de inundación.", "NWS + municipio + manejo de emergencias", "Evitar cruzar carreteras inundadas; mover actividades críticas a zonas seguras."),
        ("calor", "moderado", "Revisar sensación térmica, personas vulnerables, hidratación y áreas con poca sombra.", "NWS HeatRisk/forecast + municipio", "Habilitar espacios frescos y pausas; verificar adultos mayores y personas con condiciones de salud."),
        ("huracan", "alto", "Validar trayectoria y cono oficial; preparar comunicación por fases 72h/48h/24h.", "National Hurricane Center", "Asegurar operaciones, listas de contacto, combustible, agua y continuidad de servicios."),
        ("terremoto", "alto", "Usar alerta temprana solo si el evento ya comenzó; validar con USGS y Red Sísmica.", "USGS + Red Sísmica", "Protegerse, evaluar daños estructurales visibles y evitar entrar a edificios afectados."),
        ("tsunami", "crítico", "Validar mensaje oficial NOAA/NTWC/PTWC antes de activar protocolos públicos.", "NOAA Tsunami Warning Centers", "Moverse a terreno alto o zona segura solo según instrucciones oficiales; no esperar confirmación visual del mar."),
        ("comunicaciones", "alto", "Preparar canal redundante: web, SMS, radio, lista de llamadas y cartel físico.", "Municipio + institución", "Si falla internet, mantener instrucciones breves, impresas y por radio local."),
        ("energia", "moderado", "Verificar respaldo eléctrico para router, radio, teléfonos, neveras médicas y equipos críticos.", "Plan interno", "Priorizar equipos esenciales y carga de baterías antes del evento."),
        ("accesibilidad", "alto", "Asegurar mensajes claros, alto contraste, lectura de pantalla y lenguaje sencillo.", "WAVE/WebAIM + práctica local", "Toda alerta debe tener texto, no solo color o sonido."),
    ]
    return pd.DataFrame([{
        "generated_at_utc": generated_at_utc,
        "hazard": h,
        "priority": p,
        "recommended_action": a,
        "validation_source": s,
        "life_safety_reason": r,
        "screen_reader_label": f"{h}: prioridad {p}. Acción: {a}",
    } for h, p, a, s, r in rows])


def build_municipal_life_safety(root: Path, generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    predictions = _safe_csv(processed / "live_predictions_v10.csv")
    active_alerts = _safe_csv(processed / "active_alerts_v17.csv")
    rows = []
    for town in FOCUS_TOWNS:
        pred = pd.DataFrame()
        if not predictions.empty:
            names = predictions.get("municipality_display", predictions.get("municipality", pd.Series(dtype=str))).astype(str)
            pred = predictions[names.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("ascii").str.lower() == town.encode("ascii", errors="ignore").decode("ascii").lower()]
        risk = 0.0
        heat = None
        rain = None
        if not pred.empty:
            r = pred.iloc[0]
            risk = float(pd.to_numeric(pd.Series([r.get("operational_risk_score", 0)]), errors="coerce").fillna(0).iloc[0])
            heat = r.get("feels_like_f", None)
            rain = r.get("corrected_precip_24h_in", None)
        alerts_count = 0
        if not active_alerts.empty:
            alerts_count = int(active_alerts.get("area", pd.Series(dtype=str)).astype(str).str.contains(town, case=False, na=False).sum())
        status = "normal"
        if risk >= 70 or alerts_count > 0:
            status = "acción inmediata"
        elif risk >= 45:
            status = "vigilancia"
        rows.append({
            "generated_at_utc": generated_at_utc,
            "municipality": town,
            "status": status,
            "operational_risk_score": round(risk, 1),
            "feels_like_f": heat,
            "rain_24h_in": rain,
            "active_alerts_for_area": alerts_count,
            "priority_action": "Verificar fuentes oficiales, rutas críticas, población vulnerable y comunicación municipal.",
            "screen_reader_label": f"{town}: estado {status}, riesgo {risk:.0f} de 100, alertas activas {alerts_count}.",
        })
    return pd.DataFrame(rows)


def build_life_safety_summary(actions: pd.DataFrame, municipal: pd.DataFrame, generated_at_utc: str) -> dict[str, Any]:
    immediate = municipal[municipal["status"].astype(str).str.contains("acción", case=False, na=False)].to_dict(orient="records") if not municipal.empty else []
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.8.0",
        "headline": "Life Safety Board activo: convierte clima, sismos, tsunami y huracanes en acciones claras.",
        "immediate_municipal_actions": immediate,
        "recommended_next_integrations": [
            "IPAWS/FEMA public alerts feed for all-hazards alerts.",
            "NOAA Tsunami CAP/RSS bulletin monitoring.",
            "USGS PAGER-style impact severity for significant earthquakes.",
            "Shelter status and capacity from municipalities.",
            "Crowdsourced damage reports with validation and privacy controls.",
            "Offline PWA cache and SMS gateway for communication outages.",
            "IoT rain gauges and river sensors near flood-prone roads.",
            "School/campus emergency mode with one-screen instructions.",
        ],
        "safety_limitation": "This dashboard supports decisions but does not replace official emergency management orders.",
    }


def write_life_safety_artifacts(root: Path, *, generated_at_utc: str | None = None) -> LifeSafetyResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    actions = build_life_safety_actions(generated_at_utc)
    municipal = build_municipal_life_safety(root, generated_at_utc)
    summary = build_life_safety_summary(actions, municipal, generated_at_utc)
    actions_path = processed / "life_safety_actions_v18.csv"
    municipal_path = processed / "municipal_life_safety_v18.csv"
    summary_path = processed / "life_safety_summary_v18.json"
    actions.to_csv(actions_path, index=False)
    municipal.to_csv(municipal_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return LifeSafetyResult("ok", generated_at_utc, str(actions_path), str(municipal_path), str(summary_path), "v1.8 life safety artifacts generated.")
