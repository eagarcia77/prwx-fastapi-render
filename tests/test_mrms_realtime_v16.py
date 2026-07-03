from prwx.mrms_realtime_v16 import build_export_image_url, build_mrms_image_table

def test_mrms_export_url_contains_export_image():
    url = build_export_image_url("QPE 1h")
    assert "exportImage" in url
    assert "renderingRule" in url

def test_mrms_image_table_layers():
    df = build_mrms_image_table("2026-07-01T00:00:00+00:00")
    assert len(df) >= 7
    assert "QPE 24h" in set(df["layer"])
