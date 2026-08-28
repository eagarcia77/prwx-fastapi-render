from __future__ import annotations

from prwx.meteorological_report_v26 import (
    build_report_markdown,
    build_report_payload,
    model_feature_matrix,
    readiness_label,
    training_plan_payload,
)


def test_feature_matrix_includes_tropical_and_reanalysis_sources():
    matrix = model_feature_matrix()
    flat_sources = {source for item in matrix for source in item["sources"]}
    assert "gfs" in flat_sources
    assert "gefs" in flat_sources
    assert "nhc" in flat_sources
    assert "hafs" in flat_sources
    assert "era5_reanalysis" in flat_sources
    assert "oisst" in flat_sources


def test_training_plan_recommends_new_caribbean_atlantic_model():
    plan = training_plan_payload({"status": "training_required"}, {})
    assert plan["training_decision"]["recommendation"] == "train_new_caribbean_atlantic_model"
    assert plan["minimum_real_training_dataset"]["rows_operational_candidate"] >= 50000


def test_report_payload_and_markdown_have_required_sections():
    payload = build_report_payload({"status": "training_required"}, {})
    markdown = build_report_markdown({"status": "training_required"}, {})
    assert payload["report_version"] == "2.6.0"
    assert "Informe meteorológico Caribe-Atlántico" in markdown
    assert "Ruta de entrenamiento" in markdown
    assert readiness_label({}) == "entrenamiento histórico requerido"
