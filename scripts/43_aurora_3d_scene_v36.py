from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.aurora_3d_scene_v36 import report, scene_layers, scene_payload, status

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AURORA 3D command-center scene artifacts.")
    parser.add_argument("--pretty", action="store_true", help="Write indented JSON output.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    artifacts = {
        "aurora_3d_scene_v36.json": scene_payload(),
        "aurora_3d_layers_v36.json": scene_layers(),
        "aurora_3d_status_v36.json": status(),
        "aurora_3d_report_v36.json": report(),
    }
    for name, payload in artifacts.items():
        (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=indent), encoding="utf-8")
    print(json.dumps({"status": "ok", "generated": sorted(artifacts)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
