from fastapi.testclient import TestClient

from api.desktop_app import app
from prwx.aurora_3d_scene_v36 import scene_payload, status


def test_aurora_3d_scene_payload_has_core_layers():
    payload = scene_payload()
    assert payload["model"]["model_code"] == "AURORA-3D"
    assert payload["municipal_nodes"]
    assert payload["dust_streams"]
    assert payload["tropical_streams"]


def test_aurora_3d_status():
    data = status()
    assert data["status"] == "ok"
    assert data["scene_endpoint"] == "/aurora-caribe/3d/scene"


def test_aurora_3d_api_routes():
    client = TestClient(app)
    for path in [
        "/aurora-caribe/3d/model",
        "/aurora-caribe/3d/status",
        "/aurora-caribe/3d/layers",
        "/aurora-caribe/3d/scene",
        "/aurora-caribe/3d/report",
    ]:
        response = client.get(path)
        assert response.status_code == 200


def test_desktop_health_reports_aurora_3d():
    client = TestClient(app)
    data = client.get("/desktop-health").json()
    assert data["version"] == "3.6.0"
    assert data["aurora_3d_router_installed"] is True
