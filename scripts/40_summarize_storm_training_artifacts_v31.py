from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prwx.storm_historical_ingest_v30 import status as historical_status
from prwx.storm_historical_train_v30 import model_status

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TRAINING = ROOT / "data" / "training"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
MANIFEST_PATH = REPORTS / "storm_training_artifact_manifest_v31.json"

ARTIFACT_CANDIDATES = [
    TRAINING / "storm_tracks_atlantic_training.csv",
    TRAINING / "raw" / "hurdat2_atlantic_latest.txt",
    TRAINING / "raw" / "hurdat2_atlantic_latest.url.txt",
    PROCESSED / "storm_historical_training_v30.json",
    PROCESSED / "storm_historical_sources_v30.json",
    PROCESSED / "storm_pr_trajectory_ai_v30.json",
    MODELS / "storm_pr_trajectory_ai_v30.joblib",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)) if path.exists() else str(path.relative_to(ROOT)),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def build_manifest() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "3.1.0",
        "generated_at_utc": utc_now_iso(),
        "purpose": "Manifest for GitHub Actions storm trajectory AI training artifacts.",
        "historical_status": historical_status(),
        "model_status": model_status(),
        "artifacts": [file_info(path) for path in ARTIFACT_CANDIDATES],
        "safety_note": "Experimental AI product. Official tropical cyclone warnings and forecast decisions must follow NHC, NWS and emergency-management agencies.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    print(json.dumps(build_manifest(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
