from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

NASA_POWER_HOURLY = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def download_power_recent_point(lat: float, lon: float, days: int = 2, timeout: int = 30) -> dict:
    """Download recent NASA POWER hourly point data as supplemental context."""
    end = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = end - timedelta(days=max(days - 1, 0))
    params = {
        "parameters": "T2M,RH2M,PRECTOTCORR,WS10M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    try:
        r = requests.get(NASA_POWER_HOURLY, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        params_data = data.get("properties", {}).get("parameter", {})
        precip = params_data.get("PRECTOTCORR", {})
        vals = [v for v in precip.values() if isinstance(v, (int, float)) and v > -900]
        return {
            "nasa_status": "ok",
            "nasa_recent_precip_mm": float(sum(vals)) if vals else None,
            "nasa_hours": len(vals),
        }
    except Exception as exc:
        return {"nasa_status": f"nasa_error:{type(exc).__name__}", "nasa_recent_precip_mm": None, "nasa_hours": 0}
