from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_ANDROID_FILES = [
    "android_sensor_app/settings.gradle.kts",
    "android_sensor_app/build.gradle.kts",
    "android_sensor_app/app/build.gradle.kts",
    "android_sensor_app/app/src/main/AndroidManifest.xml",
    "android_sensor_app/app/src/main/java/edu/prwx/quakebridge/MainActivity.kt",
]

@dataclass
class AndroidAppBridgeResult:
    status: str
    generated_at_utc: str
    app_status_path: str
    message: str

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def inspect_android_app(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now_iso()
    file_status = []
    for rel in REQUIRED_ANDROID_FILES:
        path = root / rel
        file_status.append({
            "file": rel,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "status": "ok" if path.exists() and path.stat().st_size > 0 else "missing",
        })
    main_path = root / "android_sensor_app/app/src/main/java/edu/prwx/quakebridge/MainActivity.kt"
    main_text = main_path.read_text(encoding="utf-8") if main_path.exists() else ""
    privacy_ok = all(term not in main_text.lower() for term in ["device_id", "imei", "phone_number"])
    endpoint_ok = "/seismic/android-trigger" in main_text
    consent_ok = "consent" in main_text.lower()
    accelerometer_ok = "TYPE_ACCELEROMETER" in main_text
    overall_ok = all(f["status"] == "ok" for f in file_status) and privacy_ok and endpoint_ok and consent_ok and accelerometer_ok
    return {
        "generated_at_utc": generated_at_utc,
        "model_version": "2.0.0",
        "android_app_starter": True,
        "overall_status": "ok" if overall_ok else "degraded",
        "file_status": file_status,
        "privacy_ok": privacy_ok,
        "endpoint_ok": endpoint_ok,
        "consent_ok": consent_ok,
        "accelerometer_ok": accelerometer_ok,
        "default_emulator_api_url": "http://10.0.2.2:8000",
        "real_phone_api_url_note": "Use la IP LAN de la computadora, por ejemplo http://192.168.1.25:8000.",
        "limitations": [
            "Starter Android app; no es sistema público de alertas.",
            "No predice terremotos.",
            "No conecta directamente con la red privada de Google Android Earthquake Alerts.",
        ],
    }

def write_android_app_status(root: Path, generated_at_utc: str | None = None) -> AndroidAppBridgeResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    status = inspect_android_app(root, generated_at_utc)
    path = processed / "android_app_bridge_status_v20.json"
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return AndroidAppBridgeResult("ok", generated_at_utc, str(path), "v2.0 Android app starter status generated.")
