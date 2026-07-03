"""Train the Puerto Rico bias correction model."""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from prwx.model import train_bias_model, save_model

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / "data" / "processed" / "training_table.csv"
    if not path.exists():
        raise FileNotFoundError("Run scripts/02_build_training_table.py first.")

    df = pd.read_csv(path)
    trained, metrics = train_bias_model(df)

    model_path = ROOT / "models" / "prwx_bias_model.joblib"
    save_model(trained, model_path)

    metrics_path = ROOT / "reports" / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Model saved: {model_path}")
    print("Metrics:")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
