from pathlib import Path

from prwx.resilience_v15 import build_mrms_manifest, build_health_report

def test_mrms_manifest_has_layers():
    df = build_mrms_manifest("2026-07-01T00:00:00+00:00")
    assert {"QPE 1h", "QPE 3h", "QPE 6h", "QPE 24h"}.issubset(set(df["layer"]))

def test_health_report_shape(tmp_path: Path):
    root = tmp_path
    (root / "data" / "processed").mkdir(parents=True)
    report = build_health_report(root, "2026-07-01T00:00:00+00:00")
    assert report["model_version"] == "1.5.0"
    assert "file_status" in report
