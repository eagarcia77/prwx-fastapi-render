from pathlib import Path

from prwx.active_alerts_v17 import build_active_alerts, build_notification_state, build_hardening_report

def test_active_alerts_fallback(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    df = build_active_alerts(tmp_path, generated_at_utc="2026-07-01T00:00:00+00:00")
    assert not df.empty
    assert "sound_enabled" in df.columns
    assert bool(df["sound_enabled"].iloc[0]) is True

def test_notification_state_defaults(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    df = build_active_alerts(tmp_path, generated_at_utc="2026-07-01T00:00:00+00:00")
    state = build_notification_state(df, generated_at_utc="2026-07-01T00:00:00+00:00")
    assert state["notifications_default_active"] is True
    assert state["sound_default_active"] is True

def test_hardening_report(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    report = build_hardening_report(tmp_path, generated_at_utc="2026-07-01T00:00:00+00:00")
    assert report["hardened_mode"] is True
