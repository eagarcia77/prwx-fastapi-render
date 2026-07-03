import pandas as pd

from prwx.temperature_v10 import add_temperature_columns, build_temperature_table, build_weather_animation_v10, heat_risk_level


def sample_df():
    return pd.DataFrame([
        {
            "municipality": "Juana Diaz", "lat": 18.05, "lon": -66.50, "region": "south_coast",
            "base_temp_f": 91, "base_heat_index_f": 103, "relative_humidity": 76,
            "corrected_precip_24h_in": 1.2, "operational_risk_score": 42, "impact_level": "moderado",
            "wind_speed_mph": 12, "wind_dir_deg": 110,
        },
        {
            "municipality": "San Juan", "lat": 18.46, "lon": -66.10, "region": "north_coast",
            "base_temp_f": 88, "base_heat_index_f": 96, "relative_humidity": 78,
            "corrected_precip_24h_in": 0.6, "operational_risk_score": 25, "impact_level": "vigilancia",
            "wind_speed_mph": 15, "wind_dir_deg": 80,
        },
    ])


def test_heat_risk_level_categories():
    assert heat_risk_level(88) == "bajo"
    assert heat_risk_level(91) == "vigilancia"
    assert heat_risk_level(99) == "moderado"
    assert heat_risk_level(104) == "alto"
    assert heat_risk_level(109) == "crítico"


def test_add_temperature_columns_visible_fields():
    out = add_temperature_columns(sample_df(), generated_at_utc="2026-07-01T12:00:00+00:00")
    assert "temperature_f" in out.columns
    assert "feels_like_f" in out.columns
    assert "heat_risk_level" in out.columns
    assert "temperature_plain_text" in out.columns
    assert out.loc[0, "municipality_display"] == "Juana Díaz"
    assert "temperatura" in out.loc[0, "weather_plain_text"]


def test_temperature_table_focus_first():
    table = build_temperature_table(sample_df())
    assert not table.empty
    assert table.iloc[0]["is_focus_municipality"]


def test_weather_animation_v10_has_temperature_frame():
    anim = build_weather_animation_v10(sample_df(), generated_at_utc="2026-07-01T12:00:00+00:00")
    assert not anim.empty
    assert "temperature_frame_f" in anim.columns
    assert "feels_like_f" in anim.columns
