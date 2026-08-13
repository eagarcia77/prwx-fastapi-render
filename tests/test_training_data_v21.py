from __future__ import annotations

import pandas as pd

from prwx.training_data_v21 import (
    PR_BBOX,
    bbox_param,
    build_grib_object,
    merge_training_sources,
    normalize_ncei_global_hourly,
    parse_idx,
    select_idx_ranges,
)


def test_bbox_and_official_key_templates():
    assert bbox_param(PR_BBOX).startswith("18.65,-67.35")
    gfs = build_grib_object("gfs", "20260812", 12, 6)
    assert gfs.key == "gfs.20260812/12/atmos/gfs.t12z.pgrb2.0p25.f006"
    nam = build_grib_object("nam_pr", "2026-08-12", 0, 6)
    assert nam.key == "nam.20260812/nam.t00z.priconest.hiresf06.tm00.grib2"
    gefs = build_grib_object("gefs_mean", "20260812", 0, 3)
    assert gefs.key.endswith("/geavg.t00z.pgrb2s.0p25.f003")


def test_idx_range_selection_uses_only_requested_messages():
    text = "\n".join(
        [
            "1:0:d=2026081200:TMP:2 m above ground:anl:",
            "2:100:d=2026081200:UGRD:10 m above ground:anl:",
            "3:200:d=2026081200:VGRD:10 m above ground:anl:",
            "4:300:d=2026081200:HGT:500 mb:anl:",
        ]
    )
    entries = parse_idx(text)
    ranges = select_idx_ranges(entries, patterns=[r":TMP:2 m above ground:", r":VGRD:10 m above ground:"], content_length=400)
    assert ranges[0][0:2] == (0, 99)
    assert ranges[1][0:2] == (200, 299)
    assert len(ranges) == 2


def test_ncei_normalization_decodes_temperature_wind_pressure_and_precip():
    raw = pd.DataFrame(
        [
            {
                "STATION": "78526311641",
                "DATE": "2026-08-12T12:00:00",
                "LATITUDE": 18.44,
                "LONGITUDE": -66.00,
                "ELEVATION": 3.0,
                "NAME": "TEST PR",
                "TMP": "+0300,1",
                "DEW": "+0240,1",
                "SLP": "10130,1",
                "WND": "090,1,N,0050,1",
                "AA1": "01,0254,9,1",
            }
        ]
    )
    out = normalize_ncei_global_hourly(raw)
    assert len(out) == 1
    row = out.iloc[0]
    assert round(float(row["observed_temp_f"]), 1) == 86.0
    assert round(float(row["observed_pressure_hpa"]), 1) == 1013.0
    assert round(float(row["observed_wind_speed_mph"]), 2) == 11.18
    assert round(float(row["observed_precip_1h_in"]), 3) == 1.0
    assert 60 < float(row["observed_relative_humidity"]) < 80


def test_merge_prefers_shortest_lead_for_same_valid_time():
    observations = pd.DataFrame(
        [
            {
                "station_id": "S1",
                "location_id": "S1",
                "valid_time_utc": "2026-08-12T12:00:00Z",
                "lat": 18.0,
                "lon": -66.0,
                "observed_temp_f": 84.0,
            }
        ]
    )
    model = pd.DataFrame(
        [
            {"location_id": "S1", "valid_time_utc": "2026-08-12T12:00:00Z", "gfs_temp_f": 82.0, "gfs_lead_hours": 12},
            {"location_id": "S1", "valid_time_utc": "2026-08-12T12:00:00Z", "gfs_temp_f": 83.5, "gfs_lead_hours": 6},
        ]
    )
    merged = merge_training_sources(observations, [model])
    assert len(merged) == 1
    assert float(merged.iloc[0]["gfs_temp_f"]) == 83.5
    assert int(merged.iloc[0]["gfs_lead_hours"]) == 6
