from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ActiveAlertsResult:
    status: str
    generated_at_utc: str
    active_alerts_path: str
    notification_state_path: str
    hardening_report_path: str
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns or [])
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=columns or [])


def _safe_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_active_alerts(root: Path, *, generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"

    safety = _safe_csv(processed / "safety_alerts_v9.csv")
    global_tsunami = _safe_csv(processed / "global_tsunami_watch_v13.csv")
    global_eq = _safe_csv(processed / "global_earthquakes_v13.csv")
    hurricane_risk = _safe_csv(processed / "hurricane_pr_risk_v14.csv")
    predictions = _safe_csv(processed / "live_predictions_v10.csv")

    rows: list[dict[str, Any]] = []

    if not safety.empty:
        for _, r in safety.head(25).iterrows():
            severity = str(r.get("severity", "vigilancia") or "vigilancia")
            rows.append({
                "generated_at_utc": generated_at_utc,
                "alert_type": r.get("hazard_type", "clima"),
                "severity": severity,
                "source": r.get("source", "PR-WX"),
                "headline": r.get("headline", "Señal meteorológica relevante"),
                "area": r.get("municipality", "Puerto Rico"),
                "recommended_action": r.get("recommended_action", "Verificar fuentes oficiales."),
                "sound_enabled": True,
                "browser_notification_enabled": True,
                "sticky_until_cleared": True,
                "official_validation_required": True,
                "screen_reader_label": f"Alerta {severity}: {r.get('headline', 'Señal relevante')}. Acción: {r.get('recommended_action', 'Verificar fuentes oficiales.')}",
            })

    if not global_tsunami.empty:
        for _, r in global_tsunami.head(20).iterrows():
            rows.append({
                "generated_at_utc": generated_at_utc,
                "alert_type": "tsunami",
                "severity": "alto",
                "source": r.get("source", "USGS/NOAA validation required"),
                "headline": f"Evento con bandera de tsunami: {r.get('place', 'lugar no disponible')}",
                "area": r.get("place", "global"),
                "recommended_action": "Verificar NOAA Tsunami Warning Center, Red Sísmica y autoridades oficiales.",
                "sound_enabled": True,
                "browser_notification_enabled": True,
                "sticky_until_cleared": True,
                "official_validation_required": True,
                "screen_reader_label": f"Tsunami: evento cerca de {r.get('place', 'lugar no disponible')}. Verificar fuentes oficiales.",
            })

    if not global_eq.empty:
        eq = global_eq.copy()
        eq["magnitude"] = pd.to_numeric(eq.get("magnitude", 0), errors="coerce").fillna(0)
        strong = eq[eq["magnitude"] >= 5.5].head(20)
        for _, r in strong.iterrows():
            mag = float(r.get("magnitude", 0) or 0)
            rows.append({
                "generated_at_utc": generated_at_utc,
                "alert_type": "terremoto",
                "severity": "alto" if mag >= 6.5 else "moderado",
                "source": r.get("source", "USGS"),
                "headline": f"Sismo M{mag:.1f}: {r.get('place', 'lugar no disponible')}",
                "area": r.get("place", "global"),
                "recommended_action": "Revisar mapa mundial, posible impacto regional y fuentes oficiales.",
                "sound_enabled": True,
                "browser_notification_enabled": True,
                "sticky_until_cleared": True,
                "official_validation_required": True,
                "screen_reader_label": f"Sismo magnitud {mag:.1f} cerca de {r.get('place', 'lugar no disponible')}.",
            })

    if not hurricane_risk.empty:
        risky = hurricane_risk[hurricane_risk.get("pr_watch_level", pd.Series(dtype=str)).astype(str).str.contains("vigilancia", case=False, na=False)].head(20)
        for _, r in risky.iterrows():
            rows.append({
                "generated_at_utc": generated_at_utc,
                "alert_type": "huracan",
                "severity": "alto" if "alta" in str(r.get("pr_watch_level", "")).lower() else "moderado",
                "source": "PR-WX/NHC validation required",
                "headline": f"Vigilancia tropical: {r.get('storm_name', 'sistema tropical')}",
                "area": "Puerto Rico",
                "recommended_action": "Verificar trayectoria oficial del National Hurricane Center.",
                "sound_enabled": True,
                "browser_notification_enabled": True,
                "sticky_until_cleared": True,
                "official_validation_required": True,
                "screen_reader_label": f"Vigilancia tropical para Puerto Rico por {r.get('storm_name', 'sistema tropical')}.",
            })

    if not predictions.empty:
        p = predictions.copy()
        p["operational_risk_score"] = pd.to_numeric(p.get("operational_risk_score", 0), errors="coerce").fillna(0)
        high = p[p["operational_risk_score"] >= 70].head(20)
        for _, r in high.iterrows():
            rows.append({
                "generated_at_utc": generated_at_utc,
                "alert_type": "clima",
                "severity": "alto",
                "source": "PR-WX",
                "headline": f"Riesgo operacional alto en {r.get('municipality_display') or r.get('municipality', 'municipio')}",
                "area": r.get("municipality_display") or r.get("municipality", "Puerto Rico"),
                "recommended_action": r.get("action_explained", "Monitoreo intensivo y verificación de fuentes oficiales."),
                "sound_enabled": True,
                "browser_notification_enabled": True,
                "sticky_until_cleared": True,
                "official_validation_required": True,
                "screen_reader_label": f"Riesgo alto en {r.get('municipality_display') or r.get('municipality', 'municipio')}.",
            })

    columns = [
        "generated_at_utc", "alert_type", "severity", "source", "headline", "area",
        "recommended_action", "sound_enabled", "browser_notification_enabled",
        "sticky_until_cleared", "official_validation_required", "screen_reader_label"
    ]
    if not rows:
        rows.append({
            "generated_at_utc": generated_at_utc,
            "alert_type": "sistema",
            "severity": "informativo",
            "source": "PR-WX",
            "headline": "Sistema activo sin alertas críticas.",
            "area": "Puerto Rico",
            "recommended_action": "Mantener actualización automática activa.",
            "sound_enabled": True,
            "browser_notification_enabled": True,
            "sticky_until_cleared": False,
            "official_validation_required": False,
            "screen_reader_label": "Sistema activo sin alertas críticas.",
        })
    return pd.DataFrame(rows, columns=columns)


def build_notification_state(active_alerts: pd.DataFrame, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now_iso()
    high_levels = {"alto", "crítico", "critico", "severe", "critical"}
    severity_series = active_alerts.get("severity", pd.Series(dtype=str)).astype(str).str.lower()
    critical_count = int(severity_series.isin(high_levels).sum())
    alert_count = int(len(active_alerts))
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.7.0",
        "notifications_default_active": True,
        "sound_default_active": True,
        "sticky_alerts_default_active": True,
        "browser_permission_required": True,
        "alert_count": alert_count,
        "critical_count": critical_count,
        "notification_title": "PR-WX Alertas activas",
        "notification_body": f"{critical_count} alerta(s) críticas/altas de {alert_count} señal(es) activas. Verifique el panel y fuentes oficiales.",
        "recommended_user_action": "Mantener la página abierta, conceder permiso de notificaciones y mantener Docker updater activo cada minuto.",
    }


def build_hardening_report(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    checks = []
    expected = {
        "active_alerts_v17.csv": "alertas activas consolidadas",
        "notification_state_v17.json": "estado de notificaciones",
        "mrms_real_image_urls_v16.csv": "MRMS real",
        "system_health_v15.json": "salud del sistema",
        "latest_run.json": "metadata operacional",
    }
    for file, description in expected.items():
        path = processed / file
        checks.append({
            "file": file,
            "description": description,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "status": "ok" if path.exists() and path.stat().st_size > 0 else "pendiente",
        })
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.7.0",
        "hardened_mode": True,
        "docker_update_interval_seconds": 60,
        "auto_refresh_seconds": 60,
        "fail_safe_design": "El dashboard debe mostrar tablas, mensajes de estado y fallback cuando una fuente externa no responda.",
        "checks": checks,
    }


def write_active_alert_artifacts(root: Path, *, generated_at_utc: str | None = None) -> ActiveAlertsResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    active_alerts = build_active_alerts(root, generated_at_utc=generated_at_utc)
    state = build_notification_state(active_alerts, generated_at_utc=generated_at_utc)

    alerts_path = processed / "active_alerts_v17.csv"
    state_path = processed / "notification_state_v17.json"
    report_path = processed / "hardening_report_v17.json"

    active_alerts.to_csv(alerts_path, index=False)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    report = build_hardening_report(root, generated_at_utc=generated_at_utc)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return ActiveAlertsResult("ok", generated_at_utc, str(alerts_path), str(state_path), str(report_path), "v1.7 active alerts and hardening artifacts generated.")
