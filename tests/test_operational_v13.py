from prwx.operational_v13 import run_operational_update_v13


def test_v13_wrapper_callable():
    assert callable(run_operational_update_v13)
