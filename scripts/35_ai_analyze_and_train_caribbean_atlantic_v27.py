from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.ai_training_engine_v27 import (
    AI_ANALYSIS_PATH,
    AI_TRAINING_PLAN_PATH,
    AI_TRAINING_REPORT_PATH,
    save_ai_analysis_assets,
    train_ai_model_if_ready,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="PR-WX AI training engine for Caribbean and Atlantic weather model")
    parser.add_argument("--dataset", type=str, default=None, help="Optional CSV/Parquet training dataset path")
    parser.add_argument("--train", action="store_true", help="Train model if minimum research criteria are met")
    parser.add_argument("--force", action="store_true", help="Force training even if readiness thresholds are not met")
    args = parser.parse_args()

    analysis = save_ai_analysis_assets(args.dataset)
    print(json.dumps({
        "status": "analysis_saved",
        "analysis_path": str(AI_ANALYSIS_PATH),
        "training_plan_path": str(AI_TRAINING_PLAN_PATH),
        "readiness": analysis.get("readiness", {}),
    }, ensure_ascii=False, indent=2))

    if args.train:
        training = train_ai_model_if_ready(args.dataset, force=args.force)
        print(json.dumps({
            "status": "training_attempt_completed",
            "training_report_path": str(AI_TRAINING_REPORT_PATH),
            "training": training,
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
