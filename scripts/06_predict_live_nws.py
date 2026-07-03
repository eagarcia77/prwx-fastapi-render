"""Create corrected predictions from downloaded NWS live forecast data."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from prwx.features import prepare_features
from prwx.model import load_model, predict_corrected
from prwx.risk import add_risk_columns

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model_path = ROOT / "models" / "prwx_bias_model.joblib"
    live_path = ROOT / "data" / "processed" / "live_nws_forecast.csv"
    if not model_path.exists():
        raise FileNotFoundError("Run scripts/03_train_bias_model.py first.")
    if not live_path.exists():
        raise FileNotFoundError("Run scripts/05_download_nws_live.py first.")

    df = pd.read_csv(live_path)
    df = df.dropna(subset=["base_precip_24h_in"]).copy()
    if df.empty:
        raise RuntimeError("No valid NWS rows found. Check data/processed/live_nws_forecast.csv for API errors.")

    # The initial model expects several fields. If the live API does not provide them,
    # use safe defaults so the pipeline remains usable for prototyping.
    defaults = {
        "month": pd.Timestamp.now(tz="America/Puerto_Rico").month,
        "hour": pd.Timestamp.now(tz="America/Puerto_Rico").hour,
        "relative_humidity": 75.0,
        "wind_speed_mph": 8.0,
        "wind_dir_deg": 90.0,
        "pw_in": 1.8,
        "dust_index": 0.2,
        "base_temp_f": 84.0,
    }
    for col, value in defaults.items():
        if col not in df.columns:
            df[col] = value
        else:
            df[col] = df[col].fillna(value)

    trained = load_model(model_path)
    pred = predict_corrected(trained, df)
    pred = prepare_features(pred)
    pred = add_risk_columns(pred)

    out = ROOT / "data" / "processed" / "live_predictions.csv"
    pred.to_csv(out, index=False)
    print(f"Live predictions saved: {out}")
    print(pred[["municipality", "source_status", "base_precip_24h_in", "corrected_precip_24h_in", "rain_risk"]])


if __name__ == "__main__":
    main()
