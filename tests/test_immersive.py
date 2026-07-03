from __future__ import annotations

import pandas as pd

from prwx.immersive import add_immersive_columns, build_briefing, compute_idw_grid, predictions_to_geojson, simulate_scenario


def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "municipality": ["San Juan", "Ponce", "Adjuntas"],
        "region": ["north_coast", "south_coast", "central_mountains"],
        "lat": [18.4655, 18.0111, 18.1627],
        "lon": [-66.1057, -66.6141, -66.7221],
        "base_precip_24h_in": [0.4, 0.6, 1.1],
        "corrected_precip_24h_in": [0.7, 1.2, 2.4],
        "precip_p10_in": [0.2, 0.5, 1.1],
        "precip_p90_in": [1.3, 2.0, 3.6],
        "prob_ge_2in": [0.0, 0.2, 0.8],
        "prob_ge_4in": [0.0, 0.0, 0.2],
        "mrms_qpe_24h_in": [0.0, 0.8, 1.4],
        "nearby_gage_stage_ft": [1.0, 2.0, 7.0],
        "base_heat_index_f": [96, 101, 88],
        "active_nws_alerts": [0, 0, 1],
        "ensemble_spread_in": [0.2, 0.4, 0.8],
    })


def test_add_immersive_columns():
    out = add_immersive_columns(sample_df())
    assert "immersive_tower_height" in out.columns
    assert "action_priority" in out.columns
    assert out["confidence_score"].between(0, 100).all()


def test_compute_idw_grid():
    out = add_immersive_columns(sample_df())
    grid = compute_idw_grid(out, resolution=0.2)
    assert not grid.empty
    assert "operational_risk_score" in grid.columns


def test_briefing_and_geojson():
    out = add_immersive_columns(sample_df())
    briefing = build_briefing(out)
    assert briefing["headline"]
    assert briefing["top_municipalities"]
    geo = predictions_to_geojson(out)
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) == len(out)


def test_scenario_increases_risk():
    out = add_immersive_columns(sample_df())
    sc = simulate_scenario(out, rain_multiplier=2.0, soil_saturation_boost=1.0, heat_boost_f=5.0, alert_override=1)
    assert sc["operational_risk_score"].max() >= out["operational_risk_score"].max()
