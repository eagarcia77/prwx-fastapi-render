import pandas as pd

from prwx.radar_cone_v14 import build_radar_layers, build_hurricane_cone, build_hurricane_pr_risk
from prwx.hurricanes_v13 import build_sample_hurricane_tracks


def test_radar_layers_from_predictions():
    df = pd.DataFrame([{"municipality":"Ponce","municipality_display":"Ponce","lat":18.0,"lon":-66.6,"corrected_precip_24h_in":2.0,"operational_risk_score":55}])
    radar = build_radar_layers(df, generated_at_utc="2026-07-01T00:00:00+00:00")
    assert set(radar["layer"]) == {"Radar 1h", "Radar 3h", "Radar 6h", "Radar 24h"}


def test_hurricane_cone_and_pr_risk():
    tracks = build_sample_hurricane_tracks("2026-07-01T00:00:00+00:00")
    cone = build_hurricane_cone(tracks)
    risk = build_hurricane_pr_risk(tracks)
    assert not cone.empty
    assert not risk.empty
