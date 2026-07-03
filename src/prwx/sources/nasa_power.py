from __future__ import annotations

import requests
import pandas as pd

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_daily_power(lat: float, lon: float, start: str, end: str, parameters: list[str] | None = None) -> pd.DataFrame:
    """Fetch daily NASA POWER data for a point.

    Dates must use YYYYMMDD format. Example parameters: T2M, PRECTOTCORR, RH2M, WS2M.
    """
    if parameters is None:
        parameters = ["T2M", "PRECTOTCORR", "RH2M", "WS2M"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "community": "AG",
        "parameters": ",".join(parameters),
        "format": "JSON",
    }
    r = requests.get(BASE_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()["properties"]["parameter"]
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"
    return df.reset_index()
