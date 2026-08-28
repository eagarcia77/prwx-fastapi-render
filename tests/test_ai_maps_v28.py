from __future__ import annotations

from fastapi.testclient import TestClient

from api.desktop_app import app
from prwx.ai_maps_v28 import PR_MUNICIPAL_CENTROIDS, municipality_analysis, pr_ai_map_payload


def test_ai_map_has_78_municipalities():
    payload = pr_ai_map_payload()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 78
    assert len(PR_MUNICIPAL_CENTROIDS) == 78


def test_ai_map_municipality_analysis():
    feature = municipality_analysis("San Juan")
    assert feature["properties"]["municipality"] == "San Juan"
    assert "ai_analysis" in feature["properties"]
    assert 0 <= feature["properties"]["risk_score"] <= 100


def test_ai_map_api_routes():
    client = TestClient(app)
    for path in [
        "/ai/maps/status",
        "/ai/maps/layers",
        "/ai/maps/summary",
        "/ai/maps/pr-municipalities",
        "/ai/maps/pr-municipalities.geojson",
        "/ai/maps/municipality/Ponce",
    ]:
        response = client.get(path)
        assert response.status_code == 200


def test_desktop_health_reports_ai_maps_router():
    client = TestClient(app)
    response = client.get("/desktop-health")
    assert response.status_code == 200
    data = response.json()
    assert data["ai_maps_router_installed"] is True
