"""Validate that generated live files are usable."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def main() -> None:
    pred_path = PROCESSED / "live_predictions.csv"
    meta_path = PROCESSED / "latest_run.json"
    if not pred_path.exists():
        raise FileNotFoundError(pred_path)
    if not meta_path.exists():
        raise FileNotFoundError(meta_path)

    df = pd.read_csv(pred_path)
    required = {"municipality", "lat", "lon", "base_precip_24h_in", "corrected_precip_24h_in", "rain_risk"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in live_predictions.csv: {sorted(missing)}")
    if df.empty:
        raise ValueError("live_predictions.csv is empty")
    if df["corrected_precip_24h_in"].isna().any():
        raise ValueError("corrected_precip_24h_in contains missing values")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status") != "ok":
        raise ValueError(f"latest_run.json status is not ok: {meta.get('status')}")

    print("Generated outputs validated successfully.")
    print(f"Rows: {len(df)}")
    print(f"Latest run: {meta.get('generated_at_utc')}")


if __name__ == "__main__":
    main()
