from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.aurora_caribe_ai_v34 import MODEL_NAME, model_status, prediction_summary, run_training_iteration, training_plan, training_status

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PROCESSED = ROOT / "data" / "processed"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AURORA Caribe-Atlántico continuous training summary.")
    parser.add_argument("--force", action="store_true", help="Force an experimental training manifest even if readiness is low.")
    args = parser.parse_args()

    iteration = run_training_iteration(force=args.force)
    status = model_status()
    predictions = prediction_summary()
    training = training_status()
    plan = training_plan()
    manifest = {
        "model": MODEL_NAME,
        "iteration": iteration,
        "status": status,
        "predictions": predictions,
        "training": training,
        "plan": plan,
    }
    write(PROCESSED / "aurora_caribe_continuous_training_v34.json", manifest)
    write(REPORTS / "aurora_caribe_training_manifest_v34.json", manifest)
    print(json.dumps({"status": "ok", "model": MODEL_NAME, "artifact": "aurora-caribe-ai-training-v34"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
