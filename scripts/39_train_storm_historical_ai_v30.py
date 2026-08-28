from __future__ import annotations

import argparse
import json

from prwx.storm_historical_ingest_v30 import status as historical_status, write_training_table
from prwx.storm_historical_train_v30 import model_status, train_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PR-WX experimental AI storm trajectory model from historical Atlantic best tracks.")
    parser.add_argument("--build", action="store_true", help="Build the training table from HURDAT2 before training.")
    parser.add_argument("--train", action="store_true", help="Train the model.")
    parser.add_argument("--force", action="store_true", help="Allow a small experimental training run even if readiness thresholds are not met.")
    args = parser.parse_args()
    if args.build:
        print(json.dumps(write_training_table(download=True), indent=2, ensure_ascii=False))
    if args.train:
        print(json.dumps(train_model(force=args.force), indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"historical": historical_status(), "model": model_status()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
