from fastapi.testclient import TestClient

from api.desktop_app import app
from prwx.aurora_caribe_ai_v34 import MODEL_NAME, data_readiness, model_identity, prediction_layers, training_cadence


def test_aurora_caribe_identity():
    identity = model_identity()
    assert identity["model_name"] == MODEL_NAME
    assert identity["model_code"] == "AURORA-CARIBE"
    assert identity["version"] == "3.4.0"


def test_aurora_training_cadence_is_scheduled():
    cadence = training_cadence()
    assert cadence["mode"] == "continuous_scheduled_training"
    assert "*/6" in cadence["cron_utc"]


def test_aurora_prediction_layers_include_maps():
    layers = prediction_layers()["layers"]
    ids = {layer["id"] for layer in layers}
    assert "municipal_ai_risk_heat" in ids
    assert "storm_trajectory_cinematic" in ids
    assert "aurora_prediction_fusion" in ids


def test_aurora_readiness_shape():
    readiness = data_readiness()
    assert "readiness_score" in readiness
    assert "available_inputs" in readiness


def test_aurora_api_endpoints():
    client = TestClient(app)
    response = client.get("/aurora-caribe/status")
    assert response.status_code == 200
    assert response.json()["model"]["model_code"] == "AURORA-CARIBE"
    predictions = client.get("/aurora-caribe/predictions/summary")
    assert predictions.status_code == 200
    assert "prediction_confidence" in predictions.json()
