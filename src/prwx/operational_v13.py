from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hurricanes_v13 import write_hurricane_artifacts
from .global_seismic_v13 import write_global_seismic_artifacts
from .operational import OperationalResult, project_root, write_json
from .operational_v12 import run_operational_update_v12


def run_operational_update_v13(
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
    result = run_operational_update_v12(
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        include_seismic=include_seismic,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
    )
    processed = root / 'data' / 'processed'
    meta_path = processed / 'latest_run.json'
    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    except Exception:
        meta = {}
    generated = str(meta.get('generated_at_utc') or result.generated_at_utc)
    hurricane = write_hurricane_artifacts(root, use_live=include_hurricanes, generated_at_utc=generated)
    global_seismic = write_global_seismic_artifacts(root, use_live=include_seismic, generated_at_utc=generated)
    meta.update({
        'status': 'ok',
        'model_version': '1.3.0',
        'atlantic_hurricane_animation': True,
        'global_earthquake_map': True,
        'expanded_earthquake_tsunami_information': True,
        'v13_artifacts': {
            'atlantic_hurricane_tracks': hurricane.tracks_path,
            'atlantic_hurricane_summary': hurricane.summary_path,
            'global_earthquakes': global_seismic.quakes_path,
            'global_tsunami_watch': global_seismic.tsunami_path,
            'global_seismic_summary': global_seismic.summary_path,
        },
        'message': 'Operational v1.3 hurricane + global seismic update completed.',
    })
    write_json(meta_path, meta)
    return OperationalResult(
        status='ok',
        generated_at_utc=generated,
        rows_predicted=result.rows_predicted,
        predictions_path=result.predictions_path,
        metadata_path=str(meta_path),
        message='Operational v1.3 hurricane + global seismic update completed.',
    )
