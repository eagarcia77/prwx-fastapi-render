from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

NWS_BASE = "https://api.weather.gov"
DEFAULT_USER_AGENT = "PR-WX-Hybrid-Model/0.3 eduardo@example.com"

WIND_DIR_DEGREES = {
    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
    "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
    "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
    "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
}


@dataclass
class NwsForecastSummary:
    lat: float
    lon: float
    source_status: str
    base_precip_24h_in: float
    precip_probability_avg: float | None
    precip_probability_max: float | None
    base_temp_f: float | None
    relative_humidity: float | None
    wind_speed_mph: float | None
    wind_dir_deg: float | None
    periods_used: int


def _headers(user_agent: str | None = None) -> dict[str, str]:
    return {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "application/geo+json, application/json",
    }


def _get_json(url: str, user_agent: str | None = None, timeout: int = 20) -> dict[str, Any]:
    response = requests.get(url, headers=_headers(user_agent), timeout=timeout)
    response.raise_for_status()
    return response.json()


def _numeric_value(field: Any) -> float | None:
    if field is None:
        return None
    if isinstance(field, (int, float)) and not math.isnan(float(field)):
        return float(field)
    if isinstance(field, dict):
        value = field.get("value")
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _qpf_inches(field: Any) -> float | None:
    """Extract quantitative precipitation amount and convert mm to inches when needed."""
    if not isinstance(field, dict):
        return None
    value = field.get("value")
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    unit = str(field.get("unitCode", "")).lower()
    if "mm" in unit or "wmo" in unit:
        return value / 25.4
    if "inch" in unit or "in" in unit:
        return value
    return value / 25.4


def _wind_speed_to_mph(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower()
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _wind_dir_to_deg(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return WIND_DIR_DEGREES.get(str(value).upper().strip())


def get_point_metadata(lat: float, lon: float, user_agent: str | None = None) -> dict[str, Any]:
    return _get_json(f"{NWS_BASE}/points/{lat:.4f},{lon:.4f}", user_agent=user_agent)


def get_hourly_forecast(lat: float, lon: float, user_agent: str | None = None) -> list[dict[str, Any]]:
    meta = get_point_metadata(lat, lon, user_agent=user_agent)
    forecast_url = meta.get("properties", {}).get("forecastHourly")
    if not forecast_url:
        raise ValueError("NWS point metadata did not include forecastHourly URL.")
    hourly = _get_json(forecast_url, user_agent=user_agent)
    return hourly.get("properties", {}).get("periods", [])


def summarize_next_24h(lat: float, lon: float, user_agent: str | None = None) -> NwsForecastSummary:
    periods = get_hourly_forecast(lat, lon, user_agent=user_agent)[:24]
    if not periods:
        raise ValueError("NWS hourly forecast returned no periods.")

    qpf_values = [_qpf_inches(p.get("quantitativePrecipitation")) for p in periods]
    qpf_values = [v for v in qpf_values if v is not None]

    pops = [_numeric_value(p.get("probabilityOfPrecipitation")) for p in periods]
    pops = [p for p in pops if p is not None]

    temps = [_numeric_value(p.get("temperature")) for p in periods]
    temps = [t for t in temps if t is not None]

    rhs = [_numeric_value(p.get("relativeHumidity")) for p in periods]
    rhs = [rh for rh in rhs if rh is not None]

    wind_speeds = [_wind_speed_to_mph(p.get("windSpeed")) for p in periods]
    wind_speeds = [w for w in wind_speeds if w is not None]

    wind_dirs = [_wind_dir_to_deg(p.get("windDirection")) for p in periods]
    wind_dirs = [w for w in wind_dirs if w is not None]

    if qpf_values:
        base_precip = float(sum(qpf_values))
        status = "nws_qpf"
    else:
        # Fallback proxy: NWS hourly products sometimes include PoP but not QPF.
        # This is NOT a true rainfall amount. It lets the correction pipeline run
        # while clearly marking the source as a proxy estimate.
        pop_sum = sum(p / 100 for p in pops) if pops else 0.0
        base_precip = float(min(4.0, pop_sum * 0.04))
        status = "pop_proxy_no_qpf"

    return NwsForecastSummary(
        lat=float(lat),
        lon=float(lon),
        source_status=status,
        base_precip_24h_in=round(base_precip, 3),
        precip_probability_avg=round(sum(pops) / len(pops), 1) if pops else None,
        precip_probability_max=max(pops) if pops else None,
        base_temp_f=round(sum(temps) / len(temps), 1) if temps else None,
        relative_humidity=round(sum(rhs) / len(rhs), 1) if rhs else None,
        wind_speed_mph=round(sum(wind_speeds) / len(wind_speeds), 1) if wind_speeds else None,
        wind_dir_deg=round(sum(wind_dirs) / len(wind_dirs), 1) if wind_dirs else None,
        periods_used=len(periods),
    )


def download_nws_for_locations(
    locations: pd.DataFrame,
    user_agent: str | None = None,
    pause_seconds: float = 0.35,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, loc in locations.iterrows():
        try:
            summary = summarize_next_24h(float(loc["lat"]), float(loc["lon"]), user_agent=user_agent)
            row = loc.to_dict()
            row.update(summary.__dict__)
            rows.append(row)
        except Exception as exc:  # network APIs should fail gracefully in the CLI
            row = loc.to_dict()
            row.update({
                "source_status": f"error: {exc}",
                "base_precip_24h_in": None,
                "precip_probability_avg": None,
                "precip_probability_max": None,
                "base_temp_f": None,
                "relative_humidity": None,
                "wind_speed_mph": None,
                "wind_dir_deg": None,
                "periods_used": 0,
            })
            rows.append(row)
        time.sleep(pause_seconds)
    return pd.DataFrame(rows)
