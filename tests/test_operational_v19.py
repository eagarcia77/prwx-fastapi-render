from prwx.operational_v19 import run_operational_update_v19


def test_v19_wrapper_callable():
    assert callable(run_operational_update_v19)
