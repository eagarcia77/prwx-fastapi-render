from __future__ import annotations

from fastapi.testclient import TestClient

from api.desktop_app import app


client = TestClient(app)


def test_caribbean_routes_registered():
    paths = {getattr(route, "path", None) for route in app.router.routes}
    assert "/caribbean/model/status" in paths
    assert "/caribbean/model/sources" in paths
    assert "/caribbean/model/readiness" in paths
    assert "/caribbean/training/status" in paths
    assert "/weather/report/{municipality}" in paths


def test_caribbean_model_status_is_truthful_before_real_training():
    response = client.get("/caribbean/model/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "PR-CARIBE WX Hybrid"
    assert payload["version"] == "2.0.0"
    assert payload["production_validated"] is False


def test_caribbean_sources_include_pr_specific_nam_nest():
    response = client.get("/caribbean/model/sources")
    assert response.status_code == 200
    payload = response.json()
    ids = {source["id"] for source in payload["sources"]}
    assert "nam_pr_nest" in ids
    assert "nws_sju_grid" in ids
    assert "mrms_caribbean" in ids
    excluded = {item["id"] for item in payload["excluded_as_core"]}
    assert "hrrr_operational" in excluded


def test_training_status_exists_and_remains_unvalidated():
    response = client.get("/caribbean/training/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["pipeline"] == "PR-CARIBE historical training data v2.1"
    assert payload["production_validated"] is False
    assert "observations" in payload["commands"]
    assert "model_archive" in payload["commands"]


def test_desktop_health_reports_router():
    response = client.get("/desktop-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["caribbean_router_installed"] is True
    assert "/weather/report/{municipality}" in payload["caribbean_router_paths"]
    assert "/caribbean/training/status" in payload["caribbean_router_paths"]
