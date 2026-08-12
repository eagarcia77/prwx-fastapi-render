from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from prwx.caribbean_model_v20 import (
    MODEL_NAME,
    MODEL_VERSION,
    bundle_summary,
    save_caribbean_model,
    train_caribbean_model,
    training_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "training" / "pr_caribbean_training.csv"
DEFAULT_PARQUET = ROOT / "data" / "training" / "pr_caribbean_training.parquet"
MODEL_PATH = ROOT / "models" / "pr_caribe_wx_v20.joblib"
META_PATH = ROOT / "data" / "processed" / "pr_caribe_wx_v20_training.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_training(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def choose_default() -> Path:
    if DEFAULT_PARQUET.exists():
        return DEFAULT_PARQUET
    return DEFAULT_CSV


def main() -> int:
    parser = argparse.ArgumentParser(description="Train PR-CARIBE WX Hybrid v2.0 from real archived forecasts and observations.")
    parser.add_argument("--input", type=Path, default=None, help="CSV or Parquet training table.")
    parser.add_argument("--model-output", type=Path, default=MODEL_PATH)
    parser.add_argument("--metadata-output", type=Path, default=META_PATH)
    parser.add_argument("--allow-research-only", action="store_true", help="Allow training before operational-candidate thresholds are met.")
    args = parser.parse_args()

    input_path = args.input or choose_default()
    frame = load_training(input_path)
    readiness = training_readiness(frame)

    if not readiness["research_ready"] and not args.allow_research_only:
        raise SystemExit(
            "Training dataset is not research-ready. Add real archived PR/Caribbean observations and model predictors, "
            "or use --allow-research-only only for pipeline testing."
        )

    bundle, report = train_caribbean_model(frame)
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    save_caribbean_model(bundle, args.model_output)

    metadata = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "trained_at_utc": utc_now(),
        "training_dataset": str(input_path),
        "readiness": readiness,
        "production_validated": False,
        "report": report,
        "bundle": bundle_summary(bundle),
        "warning": "A successful training run is not production validation. Independent event/station backtesting is still required.",
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
