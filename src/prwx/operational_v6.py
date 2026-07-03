from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .immersive import write_immersive_artifacts
from .operational import OperationalResult, project_root, run_operational_update_v5, write_json


def run_operational_update_v6(
    *,
    root: Path | None = None,
    limit: int | None = None,
    user_agent: str | None = None,
    include_mrms: bool = True,
    include_usgs: bool = True,
    include_alerts: bool = True,
    append_to_history: bool = True,
    force_retrain: bool = False,
) -> OperationalResult:
    """Run v0.5 operational update and generate v0.6 immersive artifacts."""
    root = root or project_root()
    result = run_operational_update_v5(
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
    pred_path = processed / "live_predictions_v5.csv"
    meta_path = processed / "latest_run.json"
    meta: dict[str, Any] = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    if pred_path.exists() and pred_path.stat().st_size > 0:
        predictions = pd.read_csv(pred_path)
    else:
        predictions = pd.DataFrame()
    artifacts = write_immersive_artifacts(predictions, root, meta=meta)
    meta.update({
        "status": "ok",
        "model_version": "0.6.0",
        "immersive_mode": True,
        "v6_artifacts": artifacts,
        "message": "Operational v0.6 immersive update completed.",
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status="ok",
        generated_at_utc=str(meta.get("generated_at_utc", result.generated_at_utc)),
        rows_predicted=int(len(predictions)),
        predictions_path=artifacts["predictions_v6"],
        metadata_path=str(meta_path),
        message="Operational v0.6 immersive update completed.",
    )
