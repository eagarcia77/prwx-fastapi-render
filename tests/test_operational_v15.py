from prwx.operational_v15 import run_operational_update_v15


def test_v15_wrapper_callable():
    assert callable(run_operational_update_v15)
