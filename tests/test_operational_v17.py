from prwx.operational_v17 import run_operational_update_v17


def test_v17_wrapper_callable():
    assert callable(run_operational_update_v17)
