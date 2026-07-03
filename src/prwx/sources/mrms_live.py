from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import requests

MRMS_IMAGESERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"


@dataclass
class MrmsSampleResult:
    status: str
    value_in: float | None
    raw: dict


def sample_mrms_qpe_point(lat: float, lon: float, timeout: int = 20) -> MrmsSampleResult:
    """Sample MRMS QPE ImageServer at one point.

    The NOAA ArcGIS ImageServer can return different internal structures over
    time. This client is defensive: it stores the raw JSON and extracts the first
    numeric pixel/value it can find. If extraction fails, the pipeline continues
    with missing MRMS values rather than crashing.
    """
    geom = {"x": float(lon), "y": float(lat), "spatialReference": {"wkid": 4326}}
    params = {
        "f": "json",
        "geometry": json.dumps(geom),
        "geometryType": "esriGeometryPoint",
        "returnGeometry": "false",
    }
    try:
        r = requests.get(f"{MRMS_IMAGESERVER}/identify", params=params, timeout=timeout)
        r.raise_for_status()
        raw = r.json()
    except Exception as exc:
        return MrmsSampleResult(status=f"mrms_error:{type(exc).__name__}", value_in=None, raw={"error": str(exc)})

    value = _extract_numeric(raw)
    return MrmsSampleResult(status="ok" if value is not None else "mrms_no_value", value_in=value, raw=raw)


def _extract_numeric(obj) -> float | None:
    if obj is None:
        return None
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        # Ignore likely NoData sentinel values.
        val = float(obj)
        if -0.001 <= val <= 200:
            return val
        return None
    if isinstance(obj, str):
        try:
            return _extract_numeric(float(obj))
        except Exception:
            return None
    if isinstance(obj, dict):
        preferred = ["value", "pixelValue", "Raster.ItemPixelValue", "attributes"]
        for key in preferred:
            if key in obj:
                val = _extract_numeric(obj[key])
                if val is not None:
                    return val
        for val in obj.values():
            found = _extract_numeric(val)
            if found is not None:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = _extract_numeric(item)
            if found is not None:
                return found
    return None


MRMS_COLUMNS = ["municipality", "lat", "lon", "region", "mrms_qpe_24h_in", "mrms_status"]


def download_mrms_for_locations(locations: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
    rows = []
    df = locations.head(limit).copy() if limit else locations.copy()
    for _, loc in df.iterrows():
        result = sample_mrms_qpe_point(float(loc["lat"]), float(loc["lon"]))
        rows.append({
            "municipality": loc.get("municipality"),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
            "region": loc.get("region"),
            "mrms_qpe_24h_in": result.value_in,
            "mrms_status": result.status,
        })
    return pd.DataFrame(rows, columns=MRMS_COLUMNS)
