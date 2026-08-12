from prwx import __version__
from prwx.operational_v12 import run_operational_update_v12


def test_version_v12():
    # Operational v1.2 remains callable inside the current PR-WX application;
    # the package version tracks the deployed service, not the legacy wrapper name.
    assert __version__ == "2.5.0"


def test_v12_wrapper_callable():
    assert callable(run_operational_update_v12)
