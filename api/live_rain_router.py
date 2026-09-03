from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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
STAR_LEGACY_BASE = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr"
STAR_PAGE_BASE = "https://www.star.nesdis.noaa.gov/goes/sector_band.php"

PRODUCTS: dict[str, dict[str, str]] = {
    "band13": {"folder": "13", "label": "Banda 13 IR", "kind": "ir", "band": "13", "note": "Infrarrojo térmico. Recomendado para ver nubes de día y de noche."},
    "geocolor": {"folder": "GEOCOLOR", "label": "GeoColor", "kind": "geocolor", "band": "GEOCOLOR", "note": "Vista natural de día y multispectral IR de noche."},
    "band14": {"folder": "14", "label": "Banda 14 IR", "kind": "ir", "band": "14", "note": "Otra vista infrarroja para nubosidad alta."},
    "visible": {"folder": "02", "label": "Banda 2 Visible", "kind": "visible", "band": "02", "note": "Visible de alta resolución. Funciona mejor de día."},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": "PR-WX/5.4 satellite-proxy"})


def _read_index(folder: str) -> str:
    url = f"{STAR_BASE}/{folder}/"
    with urllib.request.urlopen(_request(url), timeout=8) as response:  # nosec - public NOAA URL
        return response.read().decode("utf-8", errors="ignore")


def _latest_urls(folder: str, product: str) -> list[str]:
    fallback = [
        f"{STAR_BASE}/{folder}/1200x1200.jpg",
        f"{STAR_BASE}/{folder}/600x600.jpg",
        f"{STAR_LEGACY_BASE}/{folder}/600x600.jpg",
    ]
    try:
        html = _read_index(folder)
    except Exception:
        return fallback

    pattern = re.compile(
        r'href="([^"<>]*(\d{11})_GOES19-ABI-pr-' + re.escape(product) + r'-(1200x1200|600x600|2400x2400)\.(jpg|gif))"',
        re.IGNORECASE,
    )
    rows: list[tuple[str, int, str]] = []
    for match in pattern.finditer(html):
        href, stamp, size, _ext = match.groups()
        score = 3 if size == "1200x1200" else 2 if size == "600x600" else 1
        rows.append((href, int(stamp) * 10 + score, size))

    if not rows:
        return fallback

    rows.sort(key=lambda row: row[1], reverse=True)
    urls: list[str] = []
    for href, _score, _size in rows[:12]:
        url = href if href.startswith("http") else f"{STAR_BASE}/{folder}/{href}"
        if url not in urls:
            urls.append(url)
    return urls[:8] + fallback


def _product_page(band: str) -> str:
    return f"{STAR_PAGE_BASE}?band={band}&length=12&sat=G19&sector=pr"


def _download_first_image(urls: list[str]) -> tuple[bytes, str, str]:
    last_error = "unknown"
    for url in urls:
        try:
            with urllib.request.urlopen(_request(url), timeout=10) as response:  # nosec - public NOAA URL
                content_type = response.headers.get("Content-Type", "image/jpeg")
                data = response.read()
                if data:
                    return data, content_type, url
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = str(exc)
    raise HTTPException(status_code=502, detail=f"No NOAA STAR image could be fetched: {last_error}")


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
            "proxy": f"/rain/live/satellite/proxy/{key}",
            "urls": _latest_urls(folder, band),
        }
    return {
        "version": "5.4.0",
        "model": "AURORA RainCast PR Backend Image Proxy",
        "generated_utc": _utc_now(),
        "source": "NOAA/NESDIS/STAR GOES-19 Puerto Rico sector resolver + same-origin image proxy",
        "official_sector_page": "https://goes.noaa.gov/sector.php?sat=G19&sector=pr&src=nav",
        "products": resolved,
        "note": "Experimental helper endpoint. Official interpretation must come from NOAA/NWS/NHC and emergency-management agencies.",
    }


@router.get("/rain/live/satellite/proxy/{product}")
def rain_live_satellite_proxy(product: str):
    if product not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Unknown satellite product")
    info = PRODUCTS[product]
    data, content_type, source_url = _download_first_image(_latest_urls(info["folder"], info["band"]))
    headers = {
        "Cache-Control": "public, max-age=60",
        "X-PRWX-Version": "5.4.0",
        "X-PRWX-Source-URL": source_url,
    }
    return StreamingResponse(iter([data]), media_type=content_type, headers=headers)
