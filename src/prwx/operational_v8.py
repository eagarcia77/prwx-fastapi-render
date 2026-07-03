from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .accessibility import write_accessible_artifacts
from .operational import OperationalResult, project_root, write_json
from .operational_v7 import run_operational_update_v7


def run_operational_update_v8(
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
    """Run v0.7 and generate v0.8 accessible, plain-language artifacts."""
    root = root or project_root()
    result = run_operational_update_v7(
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

    pred_candidates = [
        processed / "live_predictions_v6.csv",
        processed / "live_predictions_v5.csv",
        processed / "live_predictions.csv",
    ]
    predictions = pd.DataFrame()
    for path in pred_candidates:
        try:
            if path.exists() and path.stat().st_size > 0:
                predictions = pd.read_csv(path)
                if not predictions.empty:
                    break
        except Exception:
            continue

    artifacts = write_accessible_artifacts(predictions, root, generated_at_utc=str(meta.get("generated_at_utc") or result.generated_at_utc))
    meta.update({
        "status": "ok",
        "model_version": "0.8.0",
        "accessible_ui_mode": True,
        "wave_ready_design": True,
        "focus_municipalities": ["Juana Díaz", "Ponce", "San Juan", "San Germán"],
        "v8_artifacts": artifacts,
        "message": "Operational v0.8 accessibility + priority municipalities update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=str(meta.get("generated_at_utc", result.generated_at_utc)),
        rows_predicted=int(len(predictions)),
        predictions_path=artifacts["predictions_v8"],
        metadata_path=str(meta_path),
        message="Operational v0.8 accessibility + priority municipalities update completed.",
    )
