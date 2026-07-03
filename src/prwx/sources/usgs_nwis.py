from __future__ import annotations

import requests
import pandas as pd

BASE_IV = "https://waterservices.usgs.gov/nwis/iv/"


def fetch_instantaneous_values(sites: list[str], parameter_cd: str = "00060", period: str = "P7D") -> pd.DataFrame:
    """Fetch USGS instantaneous values.

    parameter_cd examples:
    - 00060 discharge/streamflow
    - 00065 gage height
    - 00045 precipitation
    """
    params = {
        "format": "json",
        "sites": ",".join(sites),
        "parameterCd": parameter_cd,
        "period": period,
        "siteStatus": "all",
    }
    r = requests.get(BASE_IV, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    rows = []
    for series in js.get("value", {}).get("timeSeries", []):
        site = series["sourceInfo"]["siteCode"][0]["value"]
        name = series["sourceInfo"].get("siteName", "")
        var = series["variable"]["variableCode"][0]["value"]
        for v in series.get("values", [{}])[0].get("value", []):
            rows.append({
                "site": site,
                "site_name": name,
                "parameter_cd": var,
                "datetime": v.get("dateTime"),
                "value": float(v.get("value")) if v.get("value") not in [None, ""] else None,
            })
    return pd.DataFrame(rows)
