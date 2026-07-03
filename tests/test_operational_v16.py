from prwx.operational_v16 import run_operational_update_v16


def test_v16_wrapper_callable():
    assert callable(run_operational_update_v16)
