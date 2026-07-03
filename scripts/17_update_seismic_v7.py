from __future__ import annotations

import argparse

from prwx.operational import project_root
from prwx.seismic import write_seismic_artifacts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PR-WX v0.7 seismic/Android EEW artifacts.")
    parser.add_argument("--offline", action="store_true", help="Use educational sample instead of USGS live feed.")
    args = parser.parse_args()
    result = write_seismic_artifacts(project_root(), use_live=not args.offline)
    print(result)
