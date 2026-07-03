from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v6 import run_operational_update_v6
from .seismic import write_seismic_artifacts


def run_operational_update_v7(
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
    """Run v0.6 weather update plus v0.7 clarity/earthquake artifacts."""
    root = root or project_root()
    result = run_operational_update_v6(
        root=root,
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
    )
    processed = root / "data" / "processed"
    meta_path = processed / "latest_run.json"
    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except Exception:
        meta = {}

    seismic_payload: dict[str, Any] = {"enabled": False}
    if include_seismic:
        seismic = write_seismic_artifacts(root, use_live=True, generated_at_utc=str(meta.get("generated_at_utc") or result.generated_at_utc))
        seismic_payload = {
            "enabled": True,
            "status": seismic.status,
            "earthquakes_path": seismic.earthquakes_path,
            "warning_path": seismic.warning_path,
            "briefing_path": seismic.briefing_path,
        }

    meta.update({
        "status": "ok",
        "model_version": "0.7.0",
        "clear_ui_mode": True,
        "seismic_eew_mode": include_seismic,
        "seismic": seismic_payload,
        "message": "Operational v0.7 clarity + seismic EEW update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=str(meta.get("generated_at_utc", result.generated_at_utc)),
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v0.7 clarity + seismic EEW update completed.",
    )
