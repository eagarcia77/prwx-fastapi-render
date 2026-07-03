from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v15 import run_operational_update_v15
from .mrms_realtime_v16 import write_mrms_realtime_artifacts


def run_operational_update_v16(
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
    result = run_operational_update_v15(
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
    mrms = write_mrms_realtime_artifacts(root, generated_at_utc=generated)
    meta.update({
        "status": "ok",
        "model_version": "1.6.0",
        "mrms_real_image_server": True,
        "mrms_export_image_urls": True,
        "v16_artifacts": {
            "mrms_real_image_urls": mrms.image_urls_path,
            "mrms_real_summary": mrms.summary_path,
        },
        "message": "Operational v1.6 real MRMS radar display update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.6 real MRMS radar display update completed.",
    )
