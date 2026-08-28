from prwx.storm_historical_ingest_v30 import sample_schema, source_catalog, training_readiness
from prwx.storm_historical_train_v30 import model_status


def test_historical_source_catalog_has_official_sources():
    sources = source_catalog()
    ids = {item["id"] for item in sources}
    assert "hurdat2_atlantic" in ids
    assert "ibtracs_na" in ids
    assert "aewc" in ids


def test_schema_has_pr_approach_targets():
    schema = sample_schema()
    assert "target_approach_500km_72h" in schema["required_targets"]
    assert "distance_to_pr_km" in schema["core_features"]


def test_empty_readiness_is_safe():
    readiness = training_readiness()
    assert "research_ready" in readiness
    assert readiness["production_validated"] is False


def test_model_status_safe_without_model():
    status = model_status()
    assert status["version"] == "3.0.0"
    assert "model_file_exists" in status
