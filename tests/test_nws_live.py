from prwx.sources.nws_live import _qpf_inches, _wind_speed_to_mph, _wind_dir_to_deg


def test_qpf_mm_to_inches():
    assert round(_qpf_inches({"value": 25.4, "unitCode": "wmoUnit:mm"}), 2) == 1.00


def test_wind_speed_range_to_average():
    assert _wind_speed_to_mph("5 to 10 mph") == 7.5


def test_wind_direction_to_degrees():
    assert _wind_dir_to_deg("ESE") == 112.5
