from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.ai_storm_tracks_v29 import analyze_events, generate_artifacts, status, train_if_possible, training_plan, training_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and optionally train PR-WX AI storm trajectory map v2.9.")
    parser.add_argument("--train", action="store_true", help="Attempt experimental AI training if historical data exists.")
    parser.add_argument("--force", action="store_true", help="Allow small experimental training below research threshold.")
    args = parser.parse_args()

    result = {
        "status": status(),
        "training_status": training_status(),
        "training_plan": training_plan(),
        "analysis": analyze_events(),
        "artifacts": generate_artifacts(),
    }
    if args.train:
        result["training_result"] = train_if_possible(force=args.force)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
