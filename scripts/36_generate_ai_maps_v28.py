from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.ai_maps_v28 import map_layers, pr_ai_map_payload, status

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PR-WX AI interactive municipal map artifacts.")
    parser.add_argument("--pretty", action="store_true", help="Write formatted JSON.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    payload = pr_ai_map_payload()
    (OUT / "ai_pr_municipal_map_v28.geojson").write_text(json.dumps(payload, ensure_ascii=False, indent=indent), encoding="utf-8")
    (OUT / "ai_pr_municipal_map_status_v28.json").write_text(json.dumps(status(), ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "ai_pr_municipal_map_layers_v28.json").write_text(json.dumps({"layers": map_layers()}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
