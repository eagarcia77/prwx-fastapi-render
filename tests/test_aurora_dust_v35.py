from fastapi.testclient import TestClient

from api.desktop_app import app
from prwx.aurora_dust_v35 import dust_analysis, dust_geojson, source_catalog, training_plan


def test_aurora_dust_analysis_payload():
    payload = dust_analysis()
    assert payload["model"]["model_code"] == "AURORA-SAHARA"
    assert payload["towns"]
    assert payload["highest_risk_municipality"]


def test_aurora_dust_geojson_features():
    geo = dust_geojson()
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) >= 4


def test_aurora_dust_sources_and_training_plan():
    sources = source_catalog()
    plan = training_plan()
    assert any("NASA" in item["name"] for item in sources["official_and_scientific_sources"])
    assert "dust_risk_score_0_100" in plan["target_variables"]


def test_aurora_dust_api_routes():
    client = TestClient(app)
    for path in [
        "/aurora-caribe/dust/status",
        "/aurora-caribe/dust/analysis",
        "/aurora-caribe/dust/map.geojson",
        "/aurora-caribe/dust/training/status",
        "/aurora-caribe/dust/health-guidance",
    ]:
        response = client.get(path)
        assert response.status_code == 200
