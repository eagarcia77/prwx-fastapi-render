from __future__ import annotations

import argparse
import json
from pathlib import Path

from prwx.aurora_dust_v35 import generate_artifacts, health_guidance, source_catalog, training_plan, training_status

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "processed" / "aurora_sahara_dust_artifact_manifest_v35.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AURORA Sahara-Caribe dust/aerosol analysis artifacts.")
    parser.add_argument("--collect", action="store_true", help="Reserved for future live-data collection step.")
    parser.add_argument("--train", action="store_true", help="Generate training readiness report.")
    parser.add_argument("--force", action="store_true", help="Allow experimental artifact generation with small datasets.")
    args = parser.parse_args()

    generated = generate_artifacts()
    manifest = {
        "status": "ok",
        "collect_requested": args.collect,
        "train_requested": args.train,
        "force": args.force,
        "generated": generated,
        "training_status": training_status(),
        "training_plan": training_plan(),
        "sources": source_catalog(),
        "health_guidance": health_guidance(),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "manifest": str(MANIFEST), "generated_files": generated.get("files", [])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
