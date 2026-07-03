"""Download a small NWS sample for selected Puerto Rico locations.

This script requires internet access. It saves the raw JSON responses in data/raw/nws/.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from prwx.sources.nws_api import get_forecast_grid, get_active_alerts

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = ROOT / "data" / "sample" / "pr_locations.csv"
OUT = ROOT / "data" / "raw" / "nws"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    locations = pd.read_csv(LOCATIONS)
    for _, row in locations.iterrows():
        print(f"Downloading NWS grid for {row['municipality']}...")
        js = get_forecast_grid(float(row["lat"]), float(row["lon"]))
        out_file = OUT / f"{row['location_id']}_forecast_grid.json"
        out_file.write_text(json.dumps(js, indent=2), encoding="utf-8")

    alerts = get_active_alerts("PR")
    (OUT / "active_alerts_PR.json").write_text(json.dumps(alerts, indent=2), encoding="utf-8")
    print(f"Saved files to {OUT}")


if __name__ == "__main__":
    main()
