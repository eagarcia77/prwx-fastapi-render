from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import pandas as pd

from prwx.caribbean_model_v20 import training_readiness
from prwx.training_data_v21 import merge_training_sources, utc_now_iso, write_manifest

ROOT = Path(__file__).resolve().parents[1]
TRAIN_ROOT = ROOT / "data" / "training"
DEFAULT_OBSERVATIONS = TRAIN_ROOT / "observations_ncei_pr.parquet"
DEFAULT_OUTPUT = TRAIN_ROOT / "pr_caribbean_training.parquet"
DEFAULT_MANIFEST = TRAIN_ROOT / "manifests" / "training_table.json"


def read_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def save_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)


def discover_model_files(patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        for name in glob.glob(pattern):
            path = Path(name)
            if path.is_file() and path.name not in {"observations_ncei_pr.parquet", "pr_caribbean_training.parquet"}:
                found.append(path)
    return sorted(set(found))


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge real observations and NOAA model predictors into PR-CARIBE WX training data.")
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--model-files", nargs="*", default=[])
    parser.add_argument("--model-glob", action="append", default=[str(TRAIN_ROOT / "gfs_*.parquet"), str(TRAIN_ROOT / "gefs_*.parquet"), str(TRAIN_ROOT / "nam_pr_*.parquet")])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    if not args.observations.exists():
        raise SystemExit(f"Observation file not found: {args.observations}")
    observations = read_frame(args.observations)

    explicit = [Path(value) for value in args.model_files]
    discovered = discover_model_files(args.model_glob)
    model_paths = sorted(set(explicit + discovered))
    model_frames: list[pd.DataFrame] = []
    used_files: list[str] = []
    for path in model_paths:
        if not path.exists():
            continue
        frame = read_frame(path)
        if frame.empty:
            continue
        model_frames.append(frame)
        used_files.append(str(path))

    combined = merge_training_sources(observations, model_frames)
    save_frame(combined, args.output)
    readiness = training_readiness(combined)

    source_prefixes = sorted(
        {
            column.split("_", 1)[0]
            for column in combined.columns
            if column.startswith(("gfs_", "gefs_", "nam_pr_", "mrms_", "goes_", "nws_", "ndbc_"))
        }
    )
    manifest = {
        "source": "training_table",
        "built_at_utc": utc_now_iso(),
        "observations": str(args.observations),
        "model_files": used_files,
        "rows": int(len(combined)),
        "stations": int(combined["station_id"].nunique()) if "station_id" in combined.columns else 0,
        "sources_detected": source_prefixes,
        "output": str(args.output),
        "readiness": readiness,
        "production_validated": False,
    }
    write_manifest(args.manifest, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
