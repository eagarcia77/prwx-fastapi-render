from __future__ import annotations

import argparse
import os

from prwx.operational_v18 import run_operational_update_v18

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PR-WX v1.8 MRMS fix + life safety board update.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-mrms", action="store_true")
    parser.add_argument("--no-usgs", action="store_true")
    parser.add_argument("--no-alerts", action="store_true")
    parser.add_argument("--no-seismic", action="store_true")
    parser.add_argument("--no-hurricanes", action="store_true")
    parser.add_argument("--no-history", action="store_true")
    parser.add_argument("--force-retrain", action="store_true")
    parser.add_argument("--user-agent", default=os.getenv("PRWX_NWS_USER_AGENT") or os.getenv("USER_AGENT"))
    args = parser.parse_args()

    result = run_operational_update_v18(
        limit=args.limit,
        user_agent=args.user_agent,
        include_mrms=not args.no_mrms,
        include_usgs=not args.no_usgs,
        include_alerts=not args.no_alerts,
        include_seismic=not args.no_seismic,
        include_hurricanes=not args.no_hurricanes,
        append_to_history=not args.no_history,
        force_retrain=args.force_retrain,
    )
    print(result)
    if result.status != "ok":
        raise SystemExit(1)
