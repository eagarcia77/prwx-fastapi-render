from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from prwx.training_data_v21 import (
    Location,
    build_grib_object,
    download_grib_subset,
    extract_grib_points,
    locations_from_observations,
    utc_now_iso,
    write_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "pr_caribe_models"
TRAIN_ROOT = ROOT / "data" / "training"
MANIFEST_ROOT = TRAIN_ROOT / "manifests"


def parse_hours(text: str) -> list[int]:
    values: list[int] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            values.extend(range(start, end + 1))
        else:
            values.append(int(token))
    return sorted(set(values))


def read_locations(path: Path) -> list[Location]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    if "station_id" in frame.columns and "valid_time_utc" in frame.columns:
        return locations_from_observations(frame)

    location_id_col = "location_id" if "location_id" in frame.columns else "station_id"
    required = {location_id_col, "lat", "lon"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Location file requires columns: {sorted(required)}")
    locations: list[Location] = []
    for _, row in frame.drop_duplicates(location_id_col).iterrows():
        locations.append(
            Location(
                location_id=str(row[location_id_col]),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                name=str(row.get("station_name") or row.get("name") or ""),
                island=str(row.get("island") or "Puerto Rico"),
                elevation_m=float(row["elevation_m"]) if pd.notna(row.get("elevation_m")) else None,
            )
        )
    return locations


def save_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download indexed NOAA GRIB2 messages and extract Puerto Rico station points for PR-CARIBE WX."
    )
    parser.add_argument("--source", choices=["gfs", "gefs_mean", "gefs_spread", "gefs_member", "nam_pr"], required=True)
    parser.add_argument("--date", required=True, help="Model initialization date YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--cycle", type=int, choices=[0, 6, 12, 18], default=0)
    parser.add_argument("--forecast-hours", default="0,3,6,9,12,18,24", help="Example: 0,3,6 or 0-24")
    parser.add_argument("--member", default=None, help="GEFS member c00 or p01-p30")
    parser.add_argument("--locations", type=Path, default=TRAIN_ROOT / "observations_ncei_pr.parquet")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--keep-grib", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    date_text = args.date.replace("-", "")
    run_time = datetime.strptime(f"{date_text}{args.cycle:02d}", "%Y%m%d%H").replace(tzinfo=timezone.utc)
    hours = parse_hours(args.forecast_hours)
    locations = read_locations(args.locations)
    if not locations:
        raise SystemExit("No extraction locations were found. Collect NCEI observations first or provide --locations.")

    output = args.output or TRAIN_ROOT / f"{args.source}_{date_text}_{args.cycle:02d}.parquet"
    frames: list[pd.DataFrame] = []
    downloads: list[dict] = []
    failures: list[dict] = []

    for index, forecast_hour in enumerate(hours, start=1):
        grib = build_grib_object(args.source, date_text, args.cycle, forecast_hour, member=args.member)
        target = RAW_ROOT / args.source / date_text / f"{args.cycle:02d}" / f"f{forecast_hour:03d}.subset.grib2"
        print(f"[{index}/{len(hours)}] {args.source} {date_text} {args.cycle:02d}Z f{forecast_hour:03d}")
        try:
            download_info = download_grib_subset(grib, target)
            downloads.append(download_info)
            frame = extract_grib_points(
                target,
                locations,
                source=args.source,
                run_time_utc=run_time,
                forecast_hour=forecast_hour,
            )
            if not frame.empty:
                frames.append(frame)
                print(f"  extracted rows: {len(frame):,}; subset bytes: {download_info['bytes_written']:,}")
            if not args.keep_grib:
                target.unlink(missing_ok=True)
        except Exception as exc:
            failures.append({"forecast_hour": forecast_hour, "error": str(exc), "object_url": grib.url})
            print(f"  ERROR: {exc}")
            if not args.continue_on_error:
                raise

    if not frames:
        raise SystemExit("No model predictor rows were extracted.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["location_id", "valid_time_utc"], kind="stable")
    save_frame(combined, output)

    manifest_path = MANIFEST_ROOT / f"{args.source}_{date_text}_{args.cycle:02d}.json"
    manifest = {
        "source": args.source,
        "date": date_text,
        "cycle": args.cycle,
        "run_time_utc": run_time.isoformat(),
        "forecast_hours": hours,
        "member": args.member,
        "collected_at_utc": utc_now_iso(),
        "locations": len(locations),
        "rows": int(len(combined)),
        "output": str(output),
        "downloads": downloads,
        "bytes_written": int(sum(int(item.get("bytes_written", 0)) for item in downloads)),
        "failures": failures,
    }
    write_manifest(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
