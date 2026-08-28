from __future__ import annotations

import argparse
import json

from prwx.storm_historical_ingest_v30 import status, write_training_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Download NOAA/NHC HURDAT2 and build PR-WX storm trajectory AI training table.")
    parser.add_argument("--no-download", action="store_true", help="Use existing raw HURDAT2 file if present.")
    args = parser.parse_args()
    result = write_training_table(download=not args.no_download)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\nSTATUS:")
    print(json.dumps(status(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
