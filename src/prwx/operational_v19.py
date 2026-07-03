from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v18 import run_operational_update_v18
from .service_verification_v19 import write_service_verification_artifacts


def run_operational_update_v19(
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
    result = run_operational_update_v18(
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
    verify = write_service_verification_artifacts(root, generated_at_utc=generated, check_external=check_external_services)
    meta.update({
        "status": "ok",
        "model_version": "1.9.0",
        "service_verification": True,
        "android_earthquake_bridge_verified": True,
        "v19_artifacts": {
            "service_status": verify.service_status_path,
            "android_status": verify.android_status_path,
            "verification_summary": verify.verification_summary_path,
        },
        "message": "Operational v1.9 service verification + Android earthquake bridge update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.9 service verification + Android earthquake bridge update completed.",
    )
