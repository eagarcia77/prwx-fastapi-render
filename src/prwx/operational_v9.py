from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v8 import run_operational_update_v8
from .realtime_v9 import write_realtime_v9_artifacts, utc_now_iso


def run_operational_update_v9(
    *,
    root: Path | None = None,
    limit: int | None = None,
    user_agent: str | None = None,
    include_mrms: bool = True,
    include_usgs: bool = True,
    include_alerts: bool = True,
    include_seismic: bool = True,
    append_to_history: bool = True,
    force_retrain: bool = False,
) -> OperationalResult:
    """Run v0.8 and generate v0.9 one-minute/animated safety artifacts."""
    root = root or project_root()
    result = run_operational_update_v8(
        root=root,
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        include_seismic=include_seismic,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
    )
    processed = root / "data" / "processed"
    meta_path = processed / "latest_run.json"
    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except Exception:
        meta = {}
    generated = str(meta.get("generated_at_utc") or result.generated_at_utc or utc_now_iso())
    artifacts = write_realtime_v9_artifacts(root, generated_at_utc=generated)
    rows_predicted = 0
    try:
        import pandas as pd
        rows_predicted = int(len(pd.read_csv(artifacts["predictions_v9"])))
    except Exception:
        rows_predicted = int(result.rows_predicted or 0)
    meta.update({
        "status": "ok",
        "model_version": "0.9.0",
        "realtime_mode": True,
        "update_interval_seconds": 60,
        "animated_rain_wind_map": True,
        "earthquake_tsunami_safety_panel": True,
        "android_sensor_bridge_mode": "experimental_aggregated_signals_only",
        "v9_artifacts": artifacts,
        "message": "Operational v0.9 realtime + animated rain/wind + safety alerts update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=rows_predicted,
        predictions_path=artifacts["predictions_v9"],
        metadata_path=str(meta_path),
        message="Operational v0.9 realtime + animated rain/wind + safety alerts update completed.",
    )
