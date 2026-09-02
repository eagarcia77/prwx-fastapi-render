from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from prwx.live_rain_v37 import (
    active_pr_alerts,
    live_rain_summary,
    map_layers,
    model_identity,
    municipal_risk,
    source_catalog,
    status,
)

router = APIRouter(tags=["AURORA RainCast PR"])

STAR_BASE = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr"
STAR_PAGE_BASE = "https://www.star.nesdis.noaa.gov/goes/sector_band.php"

PRODUCTS: dict[str, dict[str, str]] = {
    "band13": {"folder": "13", "label": "Banda 13 IR", "kind": "ir", "band": "13", "note": "Infrarrojo térmico. Recomendado para ver nubes de día y de noche."},
    "geocolor": {"folder": "GEOCOLOR", "label": "GeoColor", "kind": "geocolor", "band": "GEOCOLOR", "note": "Vista natural de día y multispectral IR de noche."},
    "band14": {"folder": "14", "label": "Banda 14 IR", "kind": "ir", "band": "14", "note": "Otra vista infrarroja para nubosidad alta."},
    "visible": {"folder": "02", "label": "Banda 2 Visible", "kind": "visible", "band": "02", "note": "Visible de alta resolución. Funciona mejor de día."},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_index(folder: str) -> str:
    url = f"{STAR_BASE}/{folder}/"
    req = urllib.request.Request(url, headers={"User-Agent": "PR-WX/5.3 satellite-resolver"})
    with urllib.request.urlopen(req, timeout=8) as response:  # nosec - public NOAA URL
        return response.read().decode("utf-8", errors="ignore")


def _latest_urls(folder: str, product: str) -> list[str]:
    try:
        html = _read_index(folder)
    except Exception:
        return [
            f"{STAR_BASE}/{folder}/1200x1200.jpg",
            f"{STAR_BASE}/{folder}/600x600.jpg",
            f"https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr/{folder}/600x600.jpg",
        ]
    pattern = re.compile(r'href="([^"<>]+GOES19-ABI-pr-' + re.escape(product) + r'-(?:1200x1200|600x600|2400x2400)\.(?:jpg|gif))"', re.IGNORECASE)
    matches = [m.group(1) for m in pattern.finditer(html)]
    matches = [m for m in matches if "600x60" not in m]
    if not matches:
        return [f"{STAR_BASE}/{folder}/1200x1200.jpg", f"{STAR_BASE}/{folder}/600x600.jpg"]
    priority = sorted(matches, key=lambda name: ("1200x1200" not in name, "600x600" not in name, name))
    latest = priority[-8:]
    latest = list(reversed(latest))
    urls = []
    for item in latest:
        if item.startswith("http"):
            urls.append(item)
        else:
            urls.append(f"{STAR_BASE}/{folder}/{item}")
    return urls[:6]


def _product_page(band: str) -> str:
    return f"{STAR_PAGE_BASE}?band={band}&length=12&sat=G19&sector=pr"


@router.get("/rain/live/model")
def rain_live_model():
    return model_identity()


@router.get("/rain/live/status")
def rain_live_status():
    return status()


@router.get("/rain/live/sources")
def rain_live_sources():
    return source_catalog()


@router.get("/rain/live/layers")
def rain_live_layers():
    return map_layers()


@router.get("/rain/live/alerts")
def rain_live_alerts():
    return active_pr_alerts()


@router.get("/rain/live/summary")
def rain_live_summary():
    return live_rain_summary()


@router.get("/rain/live/municipal-risk")
def rain_live_municipal_risk():
    return municipal_risk()


@router.get("/rain/live/satellite/latest")
def rain_live_satellite_latest() -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, info in PRODUCTS.items():
        folder = info["folder"]
        band = info["band"]
        resolved[key] = {
            "label": info["label"],
            "kind": info["kind"],
            "note": info["note"],
            "page": _product_page(band),
            "urls": _latest_urls(folder, band),
        }
    return {
        "version": "5.3.0",
        "model": "AURORA RainCast PR Backend Latest Satellite Resolver",
        "generated_utc": _utc_now(),
        "source": "NOAA/NESDIS/STAR GOES-19 Puerto Rico sector directory resolver",
        "official_sector_page": "https://goes.noaa.gov/sector.php?sat=G19&sector=pr&src=nav",
        "products": resolved,
        "note": "Experimental helper endpoint. Official interpretation must come from NOAA/NWS/NHC and emergency-management agencies.",
    }
