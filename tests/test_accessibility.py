import pandas as pd

from prwx.accessibility import add_accessibility_columns, focus_municipalities_table, build_accessible_summary


def _df():
    return pd.DataFrame([
        {"municipality": "Juana Diaz", "region": "south_coast", "lat": 18.053, "lon": -66.506, "corrected_precip_24h_in": 1.2, "operational_risk_score": 42, "impact_level": "moderado", "action_priority": 3},
        {"municipality": "Ponce", "region": "south_coast", "lat": 18.011, "lon": -66.614, "corrected_precip_24h_in": 2.1, "operational_risk_score": 62, "impact_level": "alto", "action_priority": 4},
        {"municipality": "San Juan", "region": "north_coast", "lat": 18.465, "lon": -66.105, "corrected_precip_24h_in": .8, "operational_risk_score": 25, "impact_level": "vigilancia", "action_priority": 2},
        {"municipality": "San German", "region": "west", "lat": 18.082, "lon": -67.044, "corrected_precip_24h_in": 1.0, "operational_risk_score": 33, "impact_level": "moderado", "action_priority": 3},
        {"municipality": "Mayaguez", "region": "west", "lat": 18.201, "lon": -67.139, "corrected_precip_24h_in": .4, "operational_risk_score": 12, "impact_level": "bajo", "action_priority": 1},
    ])


def test_accessibility_columns_include_plain_language():
    out = add_accessibility_columns(_df())
    assert "plain_language_summary" in out.columns
    assert "screen_reader_label" in out.columns
    assert out["plain_language_summary"].str.contains("riesgo", case=False).all()


def test_focus_municipalities_are_prioritized():
    focus = focus_municipalities_table(_df())
    assert list(focus["municipality_display"]) == ["Juana Díaz", "Ponce", "San Juan", "San Germán"]
    assert focus["is_focus_municipality"].all()


def test_accessible_summary_mentions_focus_towns():
    summary = build_accessible_summary(_df(), generated_at_utc="2026-07-01T00:00:00+00:00")
    assert summary["model_version"] == "0.8.0"
    assert len(summary["focus_municipalities"]) == 4
    assert "Juana Díaz" in summary["plain_language_summary"]
