from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .android_app_v20 import write_android_app_status
from .operational import OperationalResult, project_root, write_json
from .operational_v19 import run_operational_update_v19

def run_operational_update_v20(
    *,
    root: Path | None = None,
    limit: int | None = None,
    user_agent: str | None = None,
    include_mrms: bool = True,
    include_usgs: bool = True,
    include_alerts: bool = True,
    include_seismic: bool = True,
    include_hurricanes: bool = True,
    append_to_history: bool = True,
    force_retrain: bool = False,
    check_external_services: bool = True,
) -> OperationalResult:
    root = root or project_root()
    result = run_operational_update_v19(
        root=root,
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        include_seismic=include_seismic,
        include_hurricanes=include_hurricanes,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
        check_external_services=check_external_services,
    )
    processed = root / "data" / "processed"
    meta_path = processed / "latest_run.json"
    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except Exception:
        meta = {}
    generated = str(meta.get("generated_at_utc") or result.generated_at_utc)
    android = write_android_app_status(root, generated)
    meta.update({
        "status": "ok",
        "model_version": "2.0.0",
        "android_app_starter_included": True,
        "android_sensor_bridge_next_step": True,
        "v20_artifacts": {
            "android_app_status": android.app_status_path,
            "android_project_dir": "android_sensor_app",
        },
        "message": "Operational v2.0 Android app starter + bridge update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v2.0 Android app starter + bridge update completed.",
    )
