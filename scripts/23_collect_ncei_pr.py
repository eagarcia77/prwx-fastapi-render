from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from prwx.training_data_v21 import PR_BBOX, fetch_ncei_global_hourly, normalize_ncei_global_hourly, utc_now_iso, write_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "training" / "observations_ncei_pr.parquet"
DEFAULT_MANIFEST = ROOT / "data" / "training" / "manifests" / "ncei_pr.json"


def month_windows(start: date, end: date):
    current = date(start.year, start.month, 1)
    while current <= end:
        if current.month == 12:
            next_month = date(current.year + 1, 1, 1)
        else:
            next_month = date(current.year, current.month + 1, 1)
        window_start = max(start, current)
        window_end = min(end, next_month - pd.Timedelta(days=1))
        yield window_start, window_end
        current = next_month


def save_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect real NOAA/NCEI Global Hourly observations for Puerto Rico.")
    parser.add_argument("--start", default="2023-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--north", type=float, default=PR_BBOX[0])
    parser.add_argument("--west", type=float, default=PR_BBOX[1])
    parser.add_argument("--south", type=float, default=PR_BBOX[2])
    parser.add_argument("--east", type=float, default=PR_BBOX[3])
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()
    if end < start:
        raise SystemExit("--end must not be before --start")
    bbox = (args.north, args.west, args.south, args.east)

    frames: list[pd.DataFrame] = []
    failures: list[dict[str, str]] = []
    windows = list(month_windows(start, end))
    for index, (window_start, window_end) in enumerate(windows, start=1):
        print(f"[{index}/{len(windows)}] NCEI {window_start} -> {window_end}")
        try:
            raw = fetch_ncei_global_hourly(window_start.isoformat(), window_end.isoformat(), bbox=bbox)
            normalized = normalize_ncei_global_hourly(raw)
            if not normalized.empty:
                frames.append(normalized)
                print(f"  rows: {len(normalized):,}; stations: {normalized['station_id'].nunique():,}")
            else:
                print("  no rows")
        except Exception as exc:
            failures.append({"start": window_start.isoformat(), "end": window_end.isoformat(), "error": str(exc)})
            print(f"  ERROR: {exc}")
            if not args.continue_on_error:
                raise

    if not frames:
        raise SystemExit("No NCEI observations were collected.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["station_id", "valid_time_utc"], kind="stable")
    combined = combined.drop_duplicates(["station_id", "valid_time_utc"], keep="last")
    save_frame(combined, args.output)

    valid_times = pd.to_datetime(combined["valid_time_utc"], utc=True)
    manifest = {
        "source": "ncei_isd",
        "dataset": "NOAA/NCEI Global Hourly ISD",
        "collected_at_utc": utc_now_iso(),
        "requested_start": args.start,
        "requested_end": args.end,
        "actual_start_utc": valid_times.min().isoformat(),
        "actual_end_utc": valid_times.max().isoformat(),
        "bbox_nwse": list(bbox),
        "rows": int(len(combined)),
        "stations": int(combined["station_id"].nunique()),
        "output": str(args.output),
        "failures": failures,
    }
    write_manifest(args.manifest, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
