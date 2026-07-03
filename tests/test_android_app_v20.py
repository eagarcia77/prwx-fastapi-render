from pathlib import Path
from prwx.android_app_v20 import inspect_android_app

def test_android_app_starter_exists():
    root = Path(".")
    status = inspect_android_app(root, "2026-07-01T00:00:00+00:00")
    assert status["overall_status"] == "ok"
    assert status["privacy_ok"] is True
    assert status["endpoint_ok"] is True
    assert status["accelerometer_ok"] is True
