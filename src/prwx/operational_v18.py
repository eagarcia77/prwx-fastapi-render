from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .life_safety_v18 import write_life_safety_artifacts
from .mrms_fixed_v18 import write_mrms_fixed_artifacts
from .operational import OperationalResult, project_root, write_json
from .operational_v17 import run_operational_update_v17


def run_operational_update_v18(
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
    result = run_operational_update_v17(
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
    mrms = write_mrms_fixed_artifacts(root, generated_at_utc=generated)
    safety = write_life_safety_artifacts(root, generated_at_utc=generated)
    meta.update({
        "status": "ok",
        "model_version": "1.8.0",
        "mrms_fixed_browser_arcgis": True,
        "life_safety_board": True,
        "lifesaving_recommendations_included": True,
        "v18_artifacts": {
            "mrms_fixed_urls": mrms.url_table_path,
            "mrms_fixed_summary": mrms.summary_path,
            "mrms_arcgis_html": mrms.html_path,
            "life_safety_actions": safety.actions_path,
            "municipal_life_safety": safety.municipal_path,
            "life_safety_summary": safety.summary_path,
        },
        "message": "Operational v1.8 MRMS fix + life safety board update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.8 MRMS fix + life safety board update completed.",
    )
