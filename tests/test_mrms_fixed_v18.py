from prwx.mrms_fixed_v18 import build_export_image_url, build_url_table, build_arcgis_js_html

def test_mrms_fixed_url():
    url = build_export_image_url("QPE 1h")
    assert "exportImage" in url
    assert "renderingRule" in url
    assert "bboxSR" in url

def test_url_table_and_html():
    df = build_url_table("2026-07-01T00:00:00+00:00")
    assert len(df) >= 7
    html = build_arcgis_js_html("QPE 1h")
    assert "ImageryLayer" in html
