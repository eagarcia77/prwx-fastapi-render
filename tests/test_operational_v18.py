from prwx.operational_v18 import run_operational_update_v18


def test_v18_wrapper_callable():
    assert callable(run_operational_update_v18)
