from __future__ import annotations

import pandas as pd

from prwx.realtime_v9 import add_realtime_columns, build_weather_animation, build_safety_alerts


def _pred():
    return pd.DataFrame([
        {"municipality":"Juana Diaz", "region":"south_coast", "lat":18.053, "lon":-66.506, "corrected_precip_24h_in":2.0, "operational_risk_score":70, "impact_level":"alto", "action_priority":4},
        {"municipality":"San Juan", "region":"north_coast", "lat":18.465, "lon":-66.105, "corrected_precip_24h_in":0.7, "operational_risk_score":25, "impact_level":"vigilancia", "action_priority":2},
    ])


def test_realtime_columns_add_wind_and_text():
    out = add_realtime_columns(_pred(), generated_at_utc="2026-07-01T00:00:00+00:00")
    assert "wind_speed_mph" in out.columns
    assert "wind_arrow" in out.columns
    assert out["weather_plain_text"].str.contains("viento", case=False).all()
    assert out.loc[0, "realtime_version"] == "0.9.0"


def test_weather_animation_has_frames():
    out = build_weather_animation(_pred(), generated_at_utc="2026-07-01T00:00:00+00:00", minutes=20, step_minutes=5)
    assert not out.empty
    assert out["forecast_minute"].nunique() == 5
    assert {"rain_frame_in_hr", "wind_speed_mph", "wind_arrow"}.issubset(out.columns)


def test_safety_alerts_include_weather_and_quake():
    pred = add_realtime_columns(_pred())
    eq = pd.DataFrame([{ "magnitude":5.2, "place":"southwest Puerto Rico", "lat":17.9, "lon":-66.9, "depth_km":10, "source":"USGS", "status":"reviewed", "tsunami":0 }])
    alerts = build_safety_alerts(pred, eq, pd.DataFrame(), pd.DataFrame(), generated_at_utc="2026-07-01T00:00:00+00:00")
    assert not alerts.empty
    assert "terremoto" in set(alerts["hazard_type"])
    assert "lluvia/viento" in set(alerts["hazard_type"])
