from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .operational import OperationalResult, project_root, write_json
from .operational_v13 import run_operational_update_v13
from .radar_cone_v14 import write_v14_artifacts


def run_operational_update_v14(
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
    result = run_operational_update_v13(
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
    v14 = write_v14_artifacts(root, use_live_hurricanes=include_hurricanes, generated_at_utc=generated)
    meta.update({
        "status": "ok",
        "model_version": "1.4.0",
        "radar_layers": True,
        "hurricane_uncertainty_cone": True,
        "global_seismic_filters": True,
        "stronger_tsunami_earthquake_alerts": True,
        "v14_artifacts": {
            "radar_layers": v14.radar_layers_path,
            "hurricane_cone": v14.hurricane_cone_path,
            "hurricane_pr_risk": v14.hurricane_risk_path,
            "v14_summary": v14.summary_path,
        },
        "message": "Operational v1.4 radar + cone + enhanced seismic display update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message="Operational v1.4 radar + cone + enhanced seismic display update completed.",
    )
