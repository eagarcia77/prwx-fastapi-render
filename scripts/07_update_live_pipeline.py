"""Run the full PR-WX live update pipeline.

This is the main automation entry point for local Task Scheduler, GitHub Actions,
or manual PowerShell runs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from prwx.pipeline import copy_latest_for_release, update_live_forecast

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Use all 78 Puerto Rico municipalities.")
    parser.add_argument("--limit", type=int, default=12, help="Number of municipalities when --all is not used.")
    parser.add_argument("--user-agent", default=None, help="Custom NWS User-Agent with contact email.")
    parser.add_argument("--append-history", action="store_true", help="Append latest rows into history CSV.")
    parser.add_argument("--force-retrain", action="store_true", help="Retrain the demo model before predicting.")
    parser.add_argument("--pause-seconds", type=float, default=0.35, help="Delay between NWS API calls.")
    parser.add_argument("--fail-on-empty", action="store_true", help="Exit with error when no rows are predicted.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = update_live_forecast(
        root=ROOT,
        all_municipalities=args.all,
        limit=args.limit,
        user_agent=args.user_agent,
        append_to_history=args.append_history,
        force_retrain=args.force_retrain,
        pause_seconds=args.pause_seconds,
    )
    copy_latest_for_release(ROOT)
    print(f"Status: {result.status}")
    print(f"Generated at UTC: {result.generated_at_utc}")
    print(f"Rows downloaded: {result.rows_downloaded}")
    print(f"Rows predicted: {result.rows_predicted}")
    print(f"Forecast file: {result.forecast_path}")
    print(f"Predictions file: {result.predictions_path}")
    print(f"Metadata file: {result.metadata_path}")
    if result.history_path:
        print(f"History file: {result.history_path}")
    if result.message:
        print(result.message)
    if args.fail_on_empty and result.rows_predicted == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
