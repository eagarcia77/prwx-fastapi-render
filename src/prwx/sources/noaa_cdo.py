from __future__ import annotations

import os
from typing import Any
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"


def _token() -> str:
    token = os.getenv("NOAA_CDO_TOKEN")
    if not token:
        raise RuntimeError("Missing NOAA_CDO_TOKEN. Request a free token from NOAA CDO and place it in .env.")
    return token


def cdo_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    r = requests.get(url, headers={"token": _token()}, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_daily_summaries(station_id: str, start_date: str, end_date: str, datatype_ids: list[str] | None = None) -> pd.DataFrame:
    """Fetch daily summaries for a station from NOAA CDO.

    Dates use YYYY-MM-DD. Common datatypes: PRCP, TMAX, TMIN, AWND.
    """
    if datatype_ids is None:
        datatype_ids = ["PRCP", "TMAX", "TMIN"]
    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": start_date,
        "enddate": end_date,
        "datatypeid": datatype_ids,
        "units": "standard",
        "limit": 1000,
    }
    result = cdo_get("data", params)
    records = result.get("results", [])
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    return df
