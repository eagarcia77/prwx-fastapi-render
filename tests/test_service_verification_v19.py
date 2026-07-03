from pathlib import Path

from prwx.service_verification_v19 import verify_android_earthquake_bridge, build_verification_summary, check_local_artifacts

def test_android_bridge_verifies(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    status = verify_android_earthquake_bridge(tmp_path, generated_at_utc="2026-07-01T00:00:00+00:00")
    assert status["android_bridge_status"] == "ok"
    assert status["privacy_ok"] is True

def test_local_artifacts_shape(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    rows = check_local_artifacts(tmp_path)
    assert len(rows) >= 5

def test_verification_summary():
    summary = build_verification_summary(
        [{"ok": True}, {"ok": False}],
        [{"ok": True}, {"ok": True}, {"ok": True}, {"ok": True}, {"ok": True}],
        {"android_bridge_status": "ok"},
        "2026-07-01T00:00:00+00:00",
    )
    assert summary["overall_status"] == "ok"
