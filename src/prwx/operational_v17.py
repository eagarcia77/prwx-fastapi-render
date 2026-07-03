from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .active_alerts_v17 import write_active_alert_artifacts
from .operational import OperationalResult, project_root, write_json
from .operational_v16 import run_operational_update_v16


def run_operational_update_v17(
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
    result = run_operational_update_v16(
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
    active = write_active_alert_artifacts(root, generated_at_utc=generated)
    meta.update({
        "status": "ok",
        "model_version": "1.7.0",
        "alerts_always_active": True,
        "notifications_default_active": True,
        "sound_default_active": True,
        "sticky_alerts": True,
        "hardened_fail_safe_dashboard": True,
        "v17_artifacts": {
            "active_alerts": active.active_alerts_path,
            "notification_state": active.notification_state_path,
            "hardening_report": active.hardening_report_path,
        },
        "message": "Operational v1.7 active alerts + hardened dashboard update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.7 active alerts + hardened dashboard update completed.",
    )
