"""Create sample predictions using the trained model."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from prwx.model import load_model, predict_corrected
from prwx.features import prepare_features
from prwx.risk import add_risk_columns

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model_path = ROOT / "models" / "prwx_bias_model.joblib"
    forecast_path = ROOT / "data" / "sample" / "forecast_sample.csv"
    if not model_path.exists():
        raise FileNotFoundError("Run scripts/03_train_bias_model.py first.")

    trained = load_model(model_path)
    df = pd.read_csv(forecast_path)
    pred = predict_corrected(trained, df)
    pred = prepare_features(pred)
    pred = add_risk_columns(pred)

    out = ROOT / "data" / "processed" / "sample_predictions.csv"
    pred.to_csv(out, index=False)
    print(f"Predictions saved: {out}")
    print(pred[["municipality", "base_precip_24h_in", "corrected_precip_24h_in", "rain_risk"]])


if __name__ == "__main__":
    main()
