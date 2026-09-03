from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

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

VERSION = "5.6.0"
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
    return urllib.request.Request(url, headers={"User-Agent": "PR-WX/5.6 no-blank-satellite-image"})


def _read_index(folder: str) -> str:
    with urllib.request.urlopen(_request(f"{STAR_BASE}/{folder}/"), timeout=8) as response:  # nosec - public NOAA URL
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
    rows: list[tuple[str, int]] = []
    for match in pattern.finditer(html):
        href, stamp, size, _ext = match.groups()
        score = 3 if size == "1200x1200" else 2 if size == "600x600" else 1
        url = href if href.startswith("http") else f"{STAR_BASE}/{folder}/{href}"
        rows.append((url, int(stamp) * 10 + score))
    if not rows:
        return fallback
    rows.sort(key=lambda row: row[1], reverse=True)
    urls: list[str] = []
    for url, _score in rows[:12]:
        if url not in urls:
            urls.append(url)
    return urls[:8] + fallback


def _product_page(band: str) -> str:
    return f"{STAR_PAGE_BASE}?band={band}&length=12&sat=G19&sector=pr"


def _svg_fallback(product: str, message: str) -> bytes:
    safe_product = product.replace("<", "").replace(">", "")
    safe_message = message.replace("<", "").replace(">", "")[:180]
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='900' viewBox='0 0 1200 900'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#0f2f4f'/><stop offset='1' stop-color='#020617'/></linearGradient></defs>
<rect width='1200' height='900' fill='url(#g)'/>
<circle cx='360' cy='320' r='130' fill='#94a3b8' opacity='.35'/><circle cx='500' cy='280' r='170' fill='#cbd5e1' opacity='.28'/><circle cx='690' cy='345' r='150' fill='#64748b' opacity='.32'/><circle cx='835' cy='295' r='115' fill='#e2e8f0' opacity='.23'/>
<rect x='135' y='455' width='930' height='210' rx='26' fill='rgba(2,6,23,.78)' stroke='#fed141' stroke-width='5'/>
<text x='600' y='535' text-anchor='middle' font-family='Arial' font-size='42' fill='#fed141' font-weight='700'>PR-WX Satellite Diagnostic</text>
<text x='600' y='595' text-anchor='middle' font-family='Arial' font-size='30' fill='#ffffff'>Producto: {safe_product}</text>
<text x='600' y='640' text-anchor='middle' font-family='Arial' font-size='24' fill='#cbd5e1'>{safe_message}</text>
<text x='600' y='742' text-anchor='middle' font-family='Arial' font-size='24' fill='#86efac'>Abra /rain/live/satellite/self-test para diagnóstico.</text>
</svg>"""
    return svg.encode("utf-8")


def _download_first_image(product: str) -> tuple[bytes, str, str, bool, str]:
    info = PRODUCTS[product]
    urls = _latest_urls(info["folder"], info["band"])
    last_error = "unknown"
    for url in urls:
        try:
            with urllib.request.urlopen(_request(url), timeout=10) as response:  # nosec - public NOAA URL
                content_type = response.headers.get("Content-Type", "image/jpeg")
                data = response.read()
                looks_like_html = data[:40].lower().lstrip().startswith((b"<html", b"<!doctype"))
                if data and len(data) > 5000 and content_type.startswith("image/") and not looks_like_html:
                    return data, content_type, url, True, "ok"
                last_error = f"invalid response: {content_type}, {len(data)} bytes from {url}"
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = str(exc)
    return _svg_fallback(product, last_error), "image/svg+xml", "generated-fallback", False, last_error


def _satellite_response(product: str) -> Response:
    if product not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Unknown satellite product")
    data, content_type, source_url, ok, message = _download_first_image(product)
    headers = {
        "Cache-Control": "no-cache, max-age=60",
        "Content-Disposition": f"inline; filename=prwx-{product}.jpg",
        "X-PRWX-Version": VERSION,
        "X-PRWX-Source-URL": source_url,
        "X-PRWX-Proxy-OK": "true" if ok else "false",
        "X-PRWX-Proxy-Message": message[:150],
    }
    return Response(content=data, media_type=content_type, headers=headers)


def _test_product(key: str) -> dict[str, Any]:
    data, content_type, source_url, ok, message = _download_first_image(key)
    return {
        "product": key,
        "label": PRODUCTS[key]["label"],
        "ok": ok,
        "content_type": content_type,
        "bytes": len(data),
        "source_url": source_url,
        "proxy": f"/rain/live/satellite/proxy/{key}",
        "image": f"/rain/live/satellite/image/{key}.jpg",
        "message": message,
    }


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
        resolved[key] = {
            "label": info["label"],
            "kind": info["kind"],
            "note": info["note"],
            "page": _product_page(info["band"]),
            "proxy": f"/rain/live/satellite/proxy/{key}",
            "image": f"/rain/live/satellite/image/{key}.jpg",
            "urls": _latest_urls(info["folder"], info["band"]),
        }
    return {
        "version": VERSION,
        "model": "AURORA RainCast PR No-Blank Satellite Image Console",
        "generated_utc": _utc_now(),
        "source": "NOAA/NESDIS/STAR GOES-19 Puerto Rico sector resolver + same-origin image endpoint",
        "official_sector_page": "https://goes.noaa.gov/sector.php?sat=G19&sector=pr&src=nav",
        "self_test": "/rain/live/satellite/self-test",
        "products": resolved,
        "note": "Experimental helper endpoint. Official interpretation must come from NOAA/NWS/NHC and emergency-management agencies.",
    }


@router.get("/rain/live/satellite/self-test")
def rain_live_satellite_self_test() -> dict[str, Any]:
    return {"version": VERSION, "generated_utc": _utc_now(), "products": {key: _test_product(key) for key in PRODUCTS}}


@router.get("/rain/live/satellite/proxy/{product}")
def rain_live_satellite_proxy(product: str):
    return _satellite_response(product)


@router.get("/rain/live/satellite/image/{product}.jpg")
def rain_live_satellite_image(product: str):
    return _satellite_response(product)
