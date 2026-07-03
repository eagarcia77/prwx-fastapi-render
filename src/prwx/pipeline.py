from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from prwx.features import prepare_features
from prwx.model import load_model, predict_corrected, save_model, train_bias_model
from prwx.municipalities import load_municipalities
from prwx.risk import add_risk_columns
from prwx.sources.nws_live import download_nws_for_locations

DEFAULT_TZ = "America/Puerto_Rico"


@dataclass
class PipelineResult:
    status: str
    generated_at_utc: str
    rows_downloaded: int
    rows_predicted: int
    forecast_path: str
    predictions_path: str
    metadata_path: str
    history_path: str | None = None
    message: str = ""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_dirs(root: Path) -> None:
    for folder in ["data/processed", "data/processed/history", "models"]:
        (root / folder).mkdir(parents=True, exist_ok=True)


def ensure_demo_model(root: Path | None = None, force_retrain: bool = False) -> dict[str, Any]:
    """Train the starter bias model when the artifact is missing.

    The included demo model is intentionally small. Production accuracy requires
    multi-year observations and forecast archives.
    """
    root = root or project_root()
    _ensure_dirs(root)
    model_path = root / "models" / "prwx_bias_model.joblib"
    table_path = root / "data" / "processed" / "training_table.csv"
    sample_path = root / "data" / "sample" / "training_sample.csv"

    if model_path.exists() and not force_retrain:
        return {"trained": False, "model_path": str(model_path), "message": "Existing model found."}

    if not sample_path.exists():
        raise FileNotFoundError(f"Missing sample training file: {sample_path}")

    df = pd.read_csv(sample_path)
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(table_path, index=False)
    trained, metrics = train_bias_model(df)
    save_model(trained, model_path)
    return {"trained": True, "model_path": str(model_path), "metrics": metrics}


def select_locations(root: Path, all_municipalities: bool = True, limit: int | None = None) -> pd.DataFrame:
    locations = load_municipalities(root / "data" / "sample" / "pr_municipalities.csv")
    if all_municipalities:
        return locations

    preferred = [
        "San Juan", "Ponce", "Mayaguez", "Caguas", "Adjuntas", "Rio Grande",
        "Humacao", "Arecibo", "Guayama", "Yauco", "Fajardo", "Utuado",
    ]
    subset = locations[locations["municipality"].isin(preferred)].copy()
    if limit is not None:
        subset = subset.head(limit)
    return subset if not subset.empty else locations.head(limit or 12)


def _fill_live_defaults(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    now = pd.Timestamp.now(tz=DEFAULT_TZ)
    defaults = {
        "month": int(now.month),
        "hour": int(now.hour),
        "relative_humidity": 75.0,
        "wind_speed_mph": 8.0,
        "wind_dir_deg": 90.0,
        "pw_in": 1.8,
        "dust_index": 0.2,
        "base_temp_f": 84.0,
    }
    for col, value in defaults.items():
        if col not in out.columns:
            out[col] = value
        else:
            out[col] = out[col].fillna(value)
    return out


def append_history(predictions: pd.DataFrame, history_path: Path, generated_at_utc: str) -> Path:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    out = predictions.copy()
    out.insert(0, "run_generated_at_utc", generated_at_utc)
    if history_path.exists():
        prior = pd.read_csv(history_path)
        out = pd.concat([prior, out], ignore_index=True)
        # Keep the history compact for GitHub and Streamlit deployments.
        if len(out) > 5000:
            out = out.tail(5000).copy()
    out.to_csv(history_path, index=False)
    return history_path


def write_metadata(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def update_live_forecast(
    *,
    root: Path | None = None,
    all_municipalities: bool = True,
    limit: int | None = None,
    user_agent: str | None = None,
    append_to_history: bool = True,
    force_retrain: bool = False,
    pause_seconds: float = 0.35,
) -> PipelineResult:
    """Download NWS data, run local correction, save latest and optional history."""
    root = root or project_root()
    _ensure_dirs(root)
    generated_at = utc_now_iso()

    model_info = ensure_demo_model(root, force_retrain=force_retrain)
    locations = select_locations(root, all_municipalities=all_municipalities, limit=limit)

    forecast_path = root / "data" / "processed" / "live_nws_forecast.csv"
    predictions_path = root / "data" / "processed" / "live_predictions.csv"
    metadata_path = root / "data" / "processed" / "latest_run.json"
    history_path = root / "data" / "processed" / "history" / "live_predictions_history.csv"

    forecast = download_nws_for_locations(locations, user_agent=user_agent, pause_seconds=pause_seconds)
    forecast.insert(0, "generated_at_utc", generated_at)
    forecast.to_csv(forecast_path, index=False)

    valid = forecast.dropna(subset=["base_precip_24h_in"]).copy()
    if valid.empty:
        payload = {
            "status": "error",
            "generated_at_utc": generated_at,
            "rows_downloaded": int(len(forecast)),
            "rows_predicted": 0,
            "message": "NWS returned no usable rows. Check live_nws_forecast.csv for API errors.",
            "model": model_info,
        }
        write_metadata(metadata_path, payload)
        return PipelineResult(
            status="error",
            generated_at_utc=generated_at,
            rows_downloaded=int(len(forecast)),
            rows_predicted=0,
            forecast_path=str(forecast_path),
            predictions_path=str(predictions_path),
            metadata_path=str(metadata_path),
            history_path=str(history_path) if append_to_history else None,
            message=payload["message"],
        )

    trained = load_model(root / "models" / "prwx_bias_model.joblib")
    valid = _fill_live_defaults(valid)
    predictions = predict_corrected(trained, valid)
    predictions = prepare_features(predictions)
    predictions = add_risk_columns(predictions)
    # The forecast dataframe may already include generated_at_utc. Set/update it
    # instead of inserting a duplicate column, which breaks repeated live updates.
    predictions["generated_at_utc"] = generated_at
    first_cols = ["generated_at_utc"] + [c for c in predictions.columns if c != "generated_at_utc"]
    predictions = predictions[first_cols]
    predictions.to_csv(predictions_path, index=False)

    hist_path_str = None
    if append_to_history:
        append_history(predictions, history_path, generated_at)
        hist_path_str = str(history_path)

    payload = {
        "status": "ok",
        "generated_at_utc": generated_at,
        "rows_downloaded": int(len(forecast)),
        "rows_predicted": int(len(predictions)),
        "forecast_path": str(forecast_path),
        "predictions_path": str(predictions_path),
        "history_path": hist_path_str,
        "max_corrected_precip_24h_in": float(predictions["corrected_precip_24h_in"].max()),
        "high_risk_count": int((predictions["rain_risk"] == "alto").sum()),
        "source_status_counts": predictions["source_status"].value_counts(dropna=False).to_dict() if "source_status" in predictions else {},
        "model": model_info,
    }
    write_metadata(metadata_path, payload)
    return PipelineResult(
        status="ok",
        generated_at_utc=generated_at,
        rows_downloaded=int(len(forecast)),
        rows_predicted=int(len(predictions)),
        forecast_path=str(forecast_path),
        predictions_path=str(predictions_path),
        metadata_path=str(metadata_path),
        history_path=hist_path_str,
        message="Live forecast updated.",
    )


def copy_latest_for_release(root: Path | None = None) -> None:
    """Create stable filenames useful for releases or static downloads."""
    root = root or project_root()
    processed = root / "data" / "processed"
    targets = {
        "live_predictions.csv": "latest_live_predictions.csv",
        "live_nws_forecast.csv": "latest_live_nws_forecast.csv",
        "latest_run.json": "latest_run_snapshot.json",
    }
    for src_name, dst_name in targets.items():
        src = processed / src_name
        if src.exists():
            shutil.copy2(src, processed / dst_name)
