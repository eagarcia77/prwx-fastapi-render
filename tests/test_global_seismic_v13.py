from prwx.global_seismic_v13 import build_sample_global_earthquakes, build_global_seismic_summary


def test_sample_global_quakes():
    df = build_sample_global_earthquakes('2026-07-01T00:00:00+00:00')
    assert not df.empty
    assert {'place','magnitude','lat','lon'}.issubset(df.columns)


def test_global_summary():
    df = build_sample_global_earthquakes('2026-07-01T00:00:00+00:00')
    s = build_global_seismic_summary(df, '2026-07-01T00:00:00+00:00')
    assert s['earthquake_count'] >= 1
