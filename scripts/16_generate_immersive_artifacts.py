from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from prwx.immersive import write_immersive_artifacts
from prwx.operational import project_root

if __name__ == "__main__":
    root = project_root()
    processed = root / "data" / "processed"
    for name in ["live_predictions_v5.csv", "live_predictions.csv", "sample_predictions.csv"]:
        path = processed / name
        if path.exists() and path.stat().st_size > 0:
            df = pd.read_csv(path)
            break
    else:
        raise SystemExit("No predictions file found. Run scripts/15_operational_update_v6.py first.")
    meta_path = processed / "latest_run.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    print(write_immersive_artifacts(df, root, meta=meta))
