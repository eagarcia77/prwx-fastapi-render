from prwx.operational_v14 import run_operational_update_v14


def test_v14_wrapper_callable():
    assert callable(run_operational_update_v14)
