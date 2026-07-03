from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v9 import run_operational_update_v9
from .temperature_v10 import write_realtime_v10_artifacts, utc_now_iso


def run_operational_update_v10(
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
    """Run v0.9 and generate v1.0 temperature-first accessible artifacts."""
    root = root or project_root()
    result = run_operational_update_v9(
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
    artifacts = write_realtime_v10_artifacts(root, generated_at_utc=generated)

    rows_predicted = int(result.rows_predicted or 0)
    try:
        import pandas as pd
        rows_predicted = int(len(pd.read_csv(artifacts["predictions_v10"])))
    except Exception:
        pass

    meta.update({
        "status": "ok",
        "model_version": "1.0.0",
        "temperature_visible_by_municipality": True,
        "focus_municipalities": ["Juana Díaz", "Ponce", "San Juan", "San Germán"],
        "update_interval_seconds": 60,
        "animated_rain_wind_temperature_map": True,
        "v10_artifacts": artifacts,
        "message": "Operational v1.0 temperature + clear realtime command center update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=rows_predicted,
        predictions_path=artifacts["predictions_v10"],
        metadata_path=str(meta_path),
        message="Operational v1.0 temperature + clear realtime command center update completed.",
    )
