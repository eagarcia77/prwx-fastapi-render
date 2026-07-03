from fastapi.testclient import TestClient

from api.app import app


def test_web_bridge_status():
    client = TestClient(app)
    response = client.get("/web-bridge/status")
    assert response.status_code == 200
    assert response.json()["trigger_endpoint"] == "/seismic/web-trigger"


def test_mobile_page_served():
    client = TestClient(app)
    response = client.get("/mobile/")
    assert response.status_code == 200
    assert "Web Sensor Bridge" in response.text


def test_web_trigger_endpoint():
    client = TestClient(app)
    payload = {
        "coarse_lat": 18.02,
        "coarse_lon": -66.61,
        "pga_g": 0.05,
        "confidence": 0.35,
        "source": "web_sensor_bridge_test"
    }
    response = client.post("/seismic/web-trigger", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "stored_experimental_web_trigger"
