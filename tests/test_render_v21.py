from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app
from scripts.render_bootstrap_v21 import main as render_bootstrap_main


def test_render_bootstrap_creates_status():
    render_bootstrap_main()
    assert Path("data/processed/render_status_v21.json").exists()


def test_healthz_endpoint():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_render_status_endpoint():
    render_bootstrap_main()
    client = TestClient(app)
    response = client.get("/render/status")
    assert response.status_code == 200
    assert response.json()["platform"] == "Render"
