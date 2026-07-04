from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from api.app import app



def main() -> None:
    required = [
        ROOT / "mobile" / "index.html",
        ROOT / "mobile" / "app.js",
        ROOT / "mobile" / "api-config.js",
        ROOT / "mobile" / "styles.css",
        ROOT / "mobile" / "manifest.webmanifest",
        ROOT / "mobile" / "service-worker.js",
        ROOT / "index.html",
        ROOT / ".nojekyll",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists() or p.stat().st_size == 0 and p.name != ".nojekyll"]
    if missing:
        raise SystemExit(f"Missing required web files: {missing}")

    client = TestClient(app)
    checks = {
        "/healthz": client.get("/healthz"),
        "/web-bridge/status": client.get("/web-bridge/status"),
        "/mobile/": client.get("/mobile/"),
        "/mobile/config.json": client.get("/mobile/config.json"),
    }
    failures = {path: resp.status_code for path, resp in checks.items() if resp.status_code >= 400}
    if failures:
        raise SystemExit(f"Endpoint failures: {failures}")
    status = checks["/web-bridge/status"].json()
    out = {
        "status": "ok",
        "version": status.get("version"),
        "mobile_folder_exists": status.get("mobile_folder_exists"),
        "mobile_index_exists": status.get("mobile_index_exists"),
        "checked_files": [str(p.relative_to(ROOT)) for p in required],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
