from prwx import __version__
from prwx.operational_v12 import run_operational_update_v12


def test_version_v12():
    assert __version__ == "2.1.0"


def test_v12_wrapper_callable():
    assert callable(run_operational_update_v12)
