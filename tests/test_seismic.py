from pathlib import Path

import pandas as pd

from prwx.seismic import (
    build_eew_matrix,
    build_sample_earthquakes,
    build_sample_android_triggers,
    estimate_warning_seconds,
    evaluate_android_trigger_cluster,
    haversine_km,
)


def test_haversine_distance_reasonable():
    d = haversine_km(18.4655, -66.1057, 18.0111, -66.6141)
    assert 70 <= d <= 80


def test_warning_seconds_non_negative():
    seconds = estimate_warning_seconds(17.94, -66.92, 18.4655, -66.1057, depth_km=10)
    assert seconds >= 0


def test_eew_matrix_has_rows():
    eq = build_sample_earthquakes("2026-01-01T00:00:00+00:00")
    muni = pd.DataFrame([
        {"municipality": "San Juan", "region": "north_coast", "lat": 18.4655, "lon": -66.1057},
        {"municipality": "Ponce", "region": "south_coast", "lat": 18.0111, "lon": -66.6141},
    ])
    out = build_eew_matrix(eq, muni, top_events=1)
    assert len(out) == 2
    assert "estimated_warning_seconds" in out.columns


def test_android_cluster_sample():
    triggers = build_sample_android_triggers("2026-01-01T00:00:00+00:00")
    cluster = evaluate_android_trigger_cluster(triggers)
    assert cluster["trigger_count"] >= 4
    assert "privacy_note" in cluster
