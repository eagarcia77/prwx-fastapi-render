"""Build a training table.

For this starter, it copies the included sample data to data/processed.
In production, replace this step with joins between observations, base forecasts,
MRMS QPE, USGS hydrology and terrain features.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sample = ROOT / "data" / "sample" / "training_sample.csv"
    out = ROOT / "data" / "processed" / "training_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(sample)
    df.to_csv(out, index=False)
    print(f"Training table created: {out}")
    print(df.head())


if __name__ == "__main__":
    main()
