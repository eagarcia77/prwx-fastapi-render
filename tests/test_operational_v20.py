from prwx.operational_v20 import run_operational_update_v20


def test_v20_wrapper_callable():
    assert callable(run_operational_update_v20)
