from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v14 import run_operational_update_v14
from .resilience_v15 import write_resilience_artifacts

def run_operational_update_v15(
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
) -> OperationalResult:
    root = root or project_root()
    result = run_operational_update_v14(
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
    )
    processed = root / "data" / "processed"
    meta_path = processed / "latest_run.json"
    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except Exception:
        meta = {}
    generated = str(meta.get("generated_at_utc") or result.generated_at_utc)
    resilience = write_resilience_artifacts(root, generated_at_utc=generated)
    meta.update({
        "status": "ok",
        "model_version": "1.5.0",
        "mrms_ready_manifest": True,
        "system_health_panel": True,
        "resilient_empty_csv_handling": True,
        "v15_artifacts": {
            "system_health": resilience.health_path,
            "mrms_manifest": resilience.mrms_manifest_path,
        },
        "message": "Operational v1.5 MRMS-ready resilience update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.5 MRMS-ready resilience update completed.",
    )
