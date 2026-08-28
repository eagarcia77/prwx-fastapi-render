from __future__ import annotations

import json
from pathlib import Path

from prwx.meteorological_report_v26 import build_report_payload, model_feature_matrix


def main() -> None:
    processed = Path("data/processed")
    processed.mkdir(parents=True, exist_ok=True)

    payload = build_report_payload({}, {})
    (processed / "caribbean_atlantic_meteorological_report_v26.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (processed / "caribbean_atlantic_meteorological_report_v26.md").write_text(
        payload["report_markdown"],
        encoding="utf-8",
    )
    (processed / "caribbean_atlantic_feature_matrix_v26.json").write_text(
        json.dumps({"version": "2.6.0", "matrix": model_feature_matrix()}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps({"status": "report_generated", "version": "2.6.0"}, indent=2))


if __name__ == "__main__":
    main()
