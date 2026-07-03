from prwx.hurricanes_v13 import build_sample_hurricane_tracks, build_hurricane_summary


def test_sample_hurricane_tracks():
    df = build_sample_hurricane_tracks('2026-07-01T00:00:00+00:00')
    assert not df.empty
    assert {'storm_name','forecast_hour','lat','lon'}.issubset(df.columns)


def test_hurricane_summary():
    df = build_sample_hurricane_tracks('2026-07-01T00:00:00+00:00')
    s = build_hurricane_summary(df, '2026-07-01T00:00:00+00:00')
    assert 'active_storms' in s
