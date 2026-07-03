"""Download current NWS hourly forecast summaries for Puerto Rico locations.

This script requires internet access. It does not require a NOAA token.
By default it downloads a small subset to avoid unnecessary API calls.
Use --all to request all 78 municipalities.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from prwx.municipalities import load_municipalities
from prwx.sources.nws_live import download_nws_for_locations

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Download all 78 municipalities.")
    parser.add_argument("--limit", type=int, default=12, help="Number of municipalities to download when --all is not used.")
    parser.add_argument("--user-agent", default=None, help="Custom NWS User-Agent with contact email.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    locations = load_municipalities(ROOT / "data" / "sample" / "pr_municipalities.csv")
    if not args.all:
        # Balanced subset: metro/north, south, west, east and central mountains.
        preferred = [
            "San Juan", "Ponce", "Mayaguez", "Caguas", "Adjuntas", "Rio Grande",
            "Humacao", "Arecibo", "Guayama", "Yauco", "Fajardo", "Utuado",
        ]
        subset = locations[locations["municipality"].isin(preferred)].head(args.limit)
        if len(subset) < args.limit:
            subset = locations.head(args.limit)
        locations = subset

    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "live_nws_forecast.csv"

    print(f"Downloading NWS forecast summaries for {len(locations)} locations...")
    df = download_nws_for_locations(locations, user_agent=args.user_agent)
    df.to_csv(out, index=False)
    print(f"Saved: {out}")
    print(df[["municipality", "source_status", "base_precip_24h_in", "precip_probability_avg", "base_temp_f"]])


if __name__ == "__main__":
    main()
