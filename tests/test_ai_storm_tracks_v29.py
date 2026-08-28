from fastapi.testclient import TestClient

from api.desktop_app import app
from prwx.ai_storm_tracks_v29 import STORM_AI_VERSION, analyze_events, storm_geojson, training_plan, training_status


def test_storm_ai_version():
    assert STORM_AI_VERSION == "2.9.0"


def test_training_plan_has_official_sources():
    plan = training_plan()
    assert "NHC advisories and GIS" in plan["official_sources"]
    assert "HAFS" in plan["official_sources"]


def test_storm_analysis_payload():
    payload = analyze_events()
    assert payload["version"] == "2.9.0"
    assert "events" in payload
    assert "training_status" in payload


def test_storm_geojson_payload():
    payload = storm_geojson()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 3


def test_storm_router_endpoints():
    client = TestClient(app)
    for path in [
        "/ai/storm-tracks/status",
        "/ai/storm-tracks/analysis",
        "/ai/storm-tracks/map.geojson",
        "/ai/storm-tracks/training/status",
        "/ai/storm-tracks/training/plan",
    ]:
        response = client.get(path)
        assert response.status_code == 200
