from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .advanced_model import load_advanced_model, predict_advanced_corrected, save_advanced_model, train_advanced_bias_model
from .features import prepare_features
from .municipalities import load_municipalities
from .qc import add_quality_flags, summarize_quality
from .risk import add_risk_columns
from .sources.mrms_live import download_mrms_for_locations
from .sources.nws_alerts import download_pr_alerts
from .sources.nws_live import download_nws_for_locations
from .sources.usgs_live import attach_nearest_gage, download_usgs_pr_gages


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()




def build_offline_fallback_forecast(locations: pd.DataFrame, generated_at: str) -> pd.DataFrame:
    """Create a deterministic fallback when internet/API calls are unavailable.

    This keeps the dashboard and tests functional offline. Rows are clearly marked
    as offline fallback and must not be interpreted as real weather.
    """
    rows = []
    for _, loc in locations.iterrows():
        region = loc.get("region")
        elevation = float(loc.get("elevation_m", 0) or 0)
        coastal = float(loc.get("coastal", 0) or 0)
        regional_base = {
            "central_mountains": 0.70,
            "east": 0.65,
            "west": 0.45,
            "north_coast": 0.35,
            "south_coast": 0.20,
        }.get(region, 0.30)
        orographic = min(0.45, elevation / 1600.0)
        coast_adj = -0.05 if coastal else 0.08
        base_precip = max(0.0, regional_base + orographic + coast_adj)
        row = loc.to_dict()
        row.update({
            "source_status": "offline_demo_fallback",
            "base_precip_24h_in": round(base_precip, 3),
            "precip_probability_avg": min(95, round(25 + base_precip * 30, 1)),
            "precip_probability_max": min(100, round(45 + base_precip * 35, 1)),
            "base_temp_f": 82.0 if region == "central_mountains" else 87.0,
            "relative_humidity": 82.0 if region in {"central_mountains", "east"} else 75.0,
            "wind_speed_mph": 10.0,
            "wind_dir_deg": 95.0,
            "periods_used": 0,
        })
        rows.append(row)
    return pd.DataFrame(rows)


def ensure_dirs(root: Path) -> None:
    for folder in ["data/processed", "data/processed/history", "models", "data/raw"]:
        (root / folder).mkdir(parents=True, exist_ok=True)


@dataclass
class OperationalResult:
    status: str
    generated_at_utc: str
    rows_predicted: int
    predictions_path: str
    metadata_path: str
    message: str


def ensure_advanced_model(root: Path | None = None, force_retrain: bool = False) -> dict[str, Any]:
    root = root or project_root()
    ensure_dirs(root)
    model_path = root / "models" / "prwx_advanced_bias_model.joblib"
    sample_path = root / "data" / "sample" / "training_sample.csv"
    if model_path.exists() and not force_retrain:
        return {"trained": False, "model_path": str(model_path), "message": "Existing v0.5 model found."}
    if not sample_path.exists():
        raise FileNotFoundError(f"Missing sample training file: {sample_path}")
    df = pd.read_csv(sample_path)
    trained, metrics = train_advanced_bias_model(df)
    save_advanced_model(trained, model_path)
    return {"trained": True, "model_path": str(model_path), "metrics": metrics}


def _fill_operational_defaults(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    now = pd.Timestamp.now(tz="America/Puerto_Rico")
    defaults = {
        "month": int(now.month),
        "hour": int(now.hour),
        "relative_humidity": 78.0,
        "wind_speed_mph": 9.0,
        "wind_dir_deg": 95.0,
        "pw_in": 1.9,
        "dust_index": 0.2,
        "base_temp_f": 84.0,
        "mrms_qpe_1h_in": 0.0,
        "mrms_qpe_3h_in": 0.0,
        "mrms_qpe_6h_in": 0.0,
        "mrms_qpe_24h_in": 0.0,
        "nearby_gage_stage_ft": 0.0,
        "nearby_gage_flow_cfs": 0.0,
        "soil_proxy_7d_in": 0.0,
        "active_nws_alerts": 0,
    }
    for col, value in defaults.items():
        if col not in out.columns:
            out[col] = value
        else:
            out[col] = out[col].fillna(value)
    return out


def append_history(predictions: pd.DataFrame, path: Path, generated_at_utc: str, max_rows: int = 25000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hist = predictions.copy()
    hist.insert(0, "run_generated_at_utc", generated_at_utc)
    if path.exists() and path.stat().st_size > 0:
        try:
            old = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            old = pd.DataFrame()
        if not old.empty:
            hist = pd.concat([old, hist], ignore_index=True)
        if len(hist) > max_rows:
            hist = hist.tail(max_rows).copy()
    hist.to_csv(path, index=False)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_operational_update_v5(
    *,
    root: Path | None = None,
    limit: int | None = None,
    user_agent: str | None = None,
    include_mrms: bool = True,
    include_usgs: bool = True,
    include_alerts: bool = True,
    append_to_history: bool = True,
    force_retrain: bool = False,
) -> OperationalResult:
    root = root or project_root()
    ensure_dirs(root)
    generated_at = utc_now_iso()

    model_info = ensure_advanced_model(root, force_retrain=force_retrain)
    locations = load_municipalities(root / "data" / "sample" / "pr_municipalities.csv")
    if limit:
        # v0.8: quick runs still include the user-priority municipalities so
        # Juana Diaz, Ponce, San Juan and San German are never hidden by a
        # simple head(limit) sample. The row count may be slightly above the
        # requested limit by design.
        focus_names = {"juana diaz", "ponce", "san juan", "san german"}
        muni_lower = locations["municipality"].astype(str).str.lower()
        focus_rows = locations[muni_lower.isin(focus_names)].copy()
        head_rows = locations.head(limit).copy()
        locations = pd.concat([focus_rows, head_rows], ignore_index=True).drop_duplicates("municipality", keep="first")

    raw_dir = root / "data" / "raw"
    processed = root / "data" / "processed"
    forecast_path = processed / "live_nws_forecast.csv"
    mrms_path = processed / "live_mrms_qpe.csv"
    usgs_path = processed / "live_usgs_gages.csv"
    alerts_path = processed / "live_nws_alerts.csv"
    predictions_path = processed / "live_predictions_v5.csv"
    latest_alias_path = processed / "live_predictions.csv"
    metadata_path = processed / "latest_run.json"
    history_path = processed / "history" / "live_predictions_history_v5.csv"

    forecast = download_nws_for_locations(locations, user_agent=user_agent)
    forecast.insert(0, "generated_at_utc", generated_at)
    forecast.to_csv(forecast_path, index=False)
    base = forecast.dropna(subset=["base_precip_24h_in"]).copy()
    used_offline_fallback = False

    if base.empty:
        base = build_offline_fallback_forecast(locations, generated_at)
        used_offline_fallback = True

    if include_mrms:
        mrms = download_mrms_for_locations(locations, limit=limit)
        mrms.to_csv(mrms_path, index=False)
        base = base.merge(mrms[["municipality", "mrms_qpe_24h_in", "mrms_status"]], on="municipality", how="left")
    else:
        base["mrms_qpe_24h_in"] = None
        base["mrms_status"] = "disabled"

    if include_usgs:
        gages = download_usgs_pr_gages()
        gages.to_csv(usgs_path, index=False)
        base = attach_nearest_gage(base, gages)
    else:
        base["nearby_gage_stage_ft"] = None
        base["nearby_gage_flow_cfs"] = None
        base["nearest_gage_miles"] = None

    if include_alerts:
        alerts = download_pr_alerts(user_agent=user_agent)
        alerts.to_csv(alerts_path, index=False)
        alert_count = int(len(alerts[alerts.get("alert_status", pd.Series(dtype=str)) == "ok"])) if not alerts.empty else 0
        base["active_nws_alerts"] = alert_count
    else:
        base["active_nws_alerts"] = 0

    base = _fill_operational_defaults(base)
    trained = load_advanced_model(root / "models" / "prwx_advanced_bias_model.joblib")
    predictions = predict_advanced_corrected(trained, base)
    predictions = prepare_features(predictions)
    predictions = add_risk_columns(predictions)
    predictions = add_quality_flags(predictions)
    # The NWS live forecast already carries generated_at_utc. Re-running the
    # operational pipeline from the dashboard/Docker can therefore leave this
    # column in the dataframe before prediction. Avoid a pandas duplicate-column
    # error and make the timestamp authoritative for the current run.
    predictions["generated_at_utc"] = generated_at
    first_cols = ["generated_at_utc"] + [c for c in predictions.columns if c != "generated_at_utc"]
    predictions = predictions[first_cols]
    predictions.to_csv(predictions_path, index=False)
    predictions.to_csv(latest_alias_path, index=False)

    if append_to_history:
        append_history(predictions, history_path, generated_at)

    payload = {
        "status": "ok",
        "generated_at_utc": generated_at,
        "model_version": "0.5.2",
        "rows_predicted": int(len(predictions)),
        "used_offline_fallback": bool(used_offline_fallback),
        "max_corrected_precip_24h_in": float(predictions["corrected_precip_24h_in"].max()),
        "max_operational_risk_score": float(predictions["operational_risk_score"].max()),
        "critical_count": int((predictions["impact_level"] == "crítico").sum()),
        "high_count": int((predictions["impact_level"] == "alto").sum()),
        "source_files": {
            "nws": str(forecast_path),
            "mrms": str(mrms_path),
            "usgs": str(usgs_path),
            "alerts": str(alerts_path),
            "predictions": str(predictions_path),
            "history": str(history_path),
        },
        "quality": summarize_quality(predictions),
        "model": model_info,
    }
    write_json(metadata_path, payload)
    return OperationalResult("ok", generated_at, int(len(predictions)), str(predictions_path), str(metadata_path), "Operational v0.5 update completed.")
