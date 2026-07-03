from __future__ import annotations

import os
import requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.weather.gov"


def _headers() -> dict[str, str]:
    return {
        "User-Agent": os.getenv("USER_AGENT", "PR-WX-Hybrid-Model/0.2 contact@example.com"),
        "Accept": "application/geo+json, application/json",
    }


def get_point_metadata(lat: float, lon: float) -> dict[str, Any]:
    """Return NWS point metadata for a lat/lon."""
    url = f"{BASE_URL}/points/{lat:.4f},{lon:.4f}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_forecast_grid(lat: float, lon: float) -> dict[str, Any]:
    """Fetch NWS grid forecast for a lat/lon via /points then forecastGridData."""
    meta = get_point_metadata(lat, lon)
    grid_url = meta["properties"]["forecastGridData"]
    r = requests.get(grid_url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_active_alerts(area: str = "PR") -> dict[str, Any]:
    """Fetch active NWS alerts for a state/territory area, e.g., PR or VI."""
    url = f"{BASE_URL}/alerts/active?area={area}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()
