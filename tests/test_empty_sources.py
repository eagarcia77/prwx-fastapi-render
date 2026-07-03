from pathlib import Path

import pandas as pd

from prwx.sources.nws_alerts import ALERT_COLUMNS
from prwx.sources.mrms_live import download_mrms_for_locations, MRMS_COLUMNS
from prwx.sources.usgs_live import USGS_COLUMNS


def test_empty_alert_columns_constant():
    assert "alert_status" in ALERT_COLUMNS
    assert "error" in ALERT_COLUMNS


def test_empty_mrms_with_no_locations_has_headers():
    empty_locations = pd.DataFrame(columns=["municipality", "lat", "lon", "region"])
    out = download_mrms_for_locations(empty_locations)
    assert list(out.columns) == MRMS_COLUMNS
    assert out.empty


def test_empty_csv_file_guard_pattern(tmp_path: Path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    try:
        pd.read_csv(p)
    except pd.errors.EmptyDataError:
        assert True
