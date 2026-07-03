from prwx.features import heat_index_f


def test_heat_index_returns_temp_for_cool_conditions():
    assert heat_index_f(75, 50) == 75


def test_heat_index_warm_humid_is_above_temp():
    assert heat_index_f(90, 70) > 90
