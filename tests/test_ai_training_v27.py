from fastapi.testclient import TestClient
import pandas as pd

from api.desktop_app import app
from prwx.ai_training_engine_v27 import analyze_training_dataset, ai_training_plan, feature_matrix_catalog


def test_ai_readiness_empty_dataset():
    readiness = analyze_training_dataset(pd.DataFrame())
    assert readiness.rows == 0
    assert readiness.research_ready is False
    assert readiness.operational_candidate is False


def test_ai_feature_matrix_has_categories():
    matrix = feature_matrix_catalog()
    assert len(matrix) >= 4
    assert any("gfs_" in item["prefixes"] for item in matrix)


def test_ai_training_plan_payload():
    readiness = analyze_training_dataset(pd.DataFrame())
    plan = ai_training_plan(readiness)
    assert plan["version"] == "2.7.0"
    assert "steps" in plan
    assert "official_sources" in plan


def test_ai_api_status_endpoint():
    client = TestClient(app)
    response = client.get("/ai/model/status")
    assert response.status_code == 200
    assert response.json()["version"] == "2.7.0"


def test_ai_api_training_plan_markdown():
    client = TestClient(app)
    response = client.get("/ai/model/training-plan.md")
    assert response.status_code == 200
    assert "Inteligencia Artificial" in response.text
