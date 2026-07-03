from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

import pandas as pd
import requests

USGS_IV = "https://waterservices.usgs.gov/nwis/iv/"

USGS_COLUMNS = [
    "site_no", "site_name", "lat", "lon", "variable_code", "variable_name",
    "value", "value_time", "usgs_status", "error"
]


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))


def download_usgs_pr_gages(period: str = "PT6H", timeout: int = 30) -> pd.DataFrame:
    """Download near-real-time USGS stream gage values for Puerto Rico."""
    params = {
        "format": "json",
        "stateCd": "PR",
        "parameterCd": "00060,00065",
        "siteStatus": "active",
        "period": period,
    }
    try:
        r = requests.get(USGS_IV, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return pd.DataFrame([{"usgs_status": f"usgs_error:{type(exc).__name__}", "error": str(exc)}], columns=USGS_COLUMNS)

    rows = []
    for ts in data.get("value", {}).get("timeSeries", []):
        source = ts.get("sourceInfo", {})
        site = source.get("siteName")
        code = source.get("siteCode", [{}])[0].get("value")
        geo = source.get("geoLocation", {}).get("geogLocation", {})
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        variable = ts.get("variable", {})
        variable_code = variable.get("variableCode", [{}])[0].get("value")
        variable_name = variable.get("variableName")
        values = ts.get("values", [{}])[0].get("value", [])
        latest = values[-1] if values else {}
        try:
            val = float(latest.get("value"))
        except Exception:
            val = None
        rows.append({
            "site_no": code,
            "site_name": site,
            "lat": lat,
            "lon": lon,
            "variable_code": variable_code,
            "variable_name": variable_name,
            "value": val,
            "value_time": latest.get("dateTime"),
            "usgs_status": "ok",
        })
    return pd.DataFrame(rows, columns=USGS_COLUMNS)


def attach_nearest_gage(locations: pd.DataFrame, gages: pd.DataFrame) -> pd.DataFrame:
    """Attach nearest USGS stage/flow values to each municipality point."""
    out = locations.copy()
    if gages.empty or "usgs_status" in gages.columns and gages["usgs_status"].astype(str).str.contains("error").all():
        out["nearby_gage_stage_ft"] = None
        out["nearby_gage_flow_cfs"] = None
        out["nearest_gage_miles"] = None
        return out

    stage = gages[gages["variable_code"] == "00065"].dropna(subset=["lat", "lon", "value"])
    flow = gages[gages["variable_code"] == "00060"].dropna(subset=["lat", "lon", "value"])

    stages, flows, dist = [], [], []
    for _, loc in out.iterrows():
        loclat, loclon = float(loc["lat"]), float(loc["lon"])
        best_dist = None
        best_stage = None
        if not stage.empty:
            d = stage.apply(lambda r: _haversine_miles(loclat, loclon, float(r["lat"]), float(r["lon"])), axis=1)
            idx = d.idxmin()
            best_dist = float(d.loc[idx])
            best_stage = float(stage.loc[idx, "value"])
        best_flow = None
        if not flow.empty:
            d2 = flow.apply(lambda r: _haversine_miles(loclat, loclon, float(r["lat"]), float(r["lon"])), axis=1)
            idx2 = d2.idxmin()
            best_flow = float(flow.loc[idx2, "value"])
            if best_dist is None:
                best_dist = float(d2.loc[idx2])
        stages.append(best_stage)
        flows.append(best_flow)
        dist.append(best_dist)
    out["nearby_gage_stage_ft"] = stages
    out["nearby_gage_flow_cfs"] = flows
    out["nearest_gage_miles"] = dist
    return out
