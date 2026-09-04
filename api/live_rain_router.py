from __future__ import annotations

import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

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

VERSION = "6.0.0"
STAR_BASE = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr"
STAR_LEGACY_BASE = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr"
STAR_PAGE_BASE = "https://www.star.nesdis.noaa.gov/goes/sector_band.php"
GOES_PAGE_BASE = "https://www.goes.noaa.gov/sector_band.php"
WFO_PAGE = "https://www.goes.noaa.gov/wfo.php?wfo=sju"
WFO_REFRESH_PAGE = "https://www.goes.noaa.gov/wfo.php?refresh=true&wfo=sju"
OFFICIAL_SECTOR_PAGE = "https://www.star.nesdis.noaa.gov/goes/sector.php?sat=G19&sector=pr&src=nav"

PRODUCTS: dict[str, dict[str, str]] = {
    "band13": {"folder": "13", "label": "Banda 13 IR", "kind": "ir", "band": "13", "note": "Infrarrojo térmico. Recomendado para ver nubes de día y de noche."},
    "geocolor": {"folder": "GEOCOLOR", "label": "GeoColor", "kind": "geocolor", "band": "GEOCOLOR", "note": "Vista natural de día y multispectral IR de noche."},
    "band14": {"folder": "14", "label": "Banda 14 IR", "kind": "ir", "band": "14", "note": "Otra vista infrarroja para nubosidad alta."},
    "visible": {"folder": "02", "label": "Banda 2 Visible", "kind": "visible", "band": "02", "note": "Visible de alta resolución. Funciona mejor de día."},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": "PR-WX/6.0 animated-cloud-loop"})


def _read_text(url: str, timeout: int = 8) -> str:
    with urllib.request.urlopen(_request(url), timeout=timeout) as response:  # nosec - public NOAA URL
        return response.read().decode("utf-8", errors="ignore")


def _product_page(band: str) -> str:
    return f"{STAR_PAGE_BASE}?band={urllib.parse.quote(band)}&length=12&sat=G19&sector=pr&src=nav"


def _goes_product_page(band: str) -> str:
    return f"{GOES_PAGE_BASE}?band={urllib.parse.quote(band)}&length=12&sat=G19&sector=pr&src=nav"


def _absolute_url(href: str, folder: str) -> str:
    href = href.strip().replace("&amp;", "&")
    if href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        host = "https://cdn.star.nesdis.noaa.gov" if "/GOES" in href else "https://www.star.nesdis.noaa.gov"
        return host + href
    if href.startswith("GOES19") or href.startswith("20"):
        return f"{STAR_BASE}/{folder}/{href}"
    return urllib.parse.urljoin(f"{STAR_BASE}/{folder}/", href)


def _collect_image_urls(html: str, folder: str, band: str) -> list[str]:
    urls: list[str] = []
    patterns = [
        r'https://cdn\.star\.nesdis\.noaa\.gov/[^"\'<>\s]+\.(?:jpg|jpeg|png)',
        r'(?:src|href)=["\']([^"\']+\.(?:jpg|jpeg|png))(?:\?[^"\']*)?["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            url = _absolute_url(match.group(1) if match.groups() else match.group(0), folder)
            low = url.lower()
            want = f"/pr/{folder.lower()}/" in low or f"-pr-{band.lower()}-" in low
            if want and "600x60" not in low and url not in urls:
                urls.append(url)
    return urls


def _collect_loop_urls(html: str, folder: str, band: str) -> list[str]:
    urls: list[str] = []
    patterns = [
        r'https://cdn\.star\.nesdis\.noaa\.gov/[^"\'<>\s]+\.gif',
        r'(?:src|href)=["\']([^"\']+\.gif)(?:\?[^"\']*)?["\']',
        r'href=["\']([^"\']*GOES19-ABI-PR-' + re.escape(band) + r'-600x600\.gif)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            url = _absolute_url(match.group(1) if match.groups() else match.group(0), folder)
            low = url.lower()
            want = f"/pr/{folder.lower()}/" in low or f"-pr-{band.lower()}-" in low or f"/pr/{folder.lower()}/" in urllib.parse.unquote(low)
            if want and "600x60" in low and url not in urls:
                urls.append(url)
            elif want and url.endswith(".gif") and url not in urls:
                urls.append(url)
    return urls


def _page_candidates(folder: str, band: str) -> list[str]:
    urls: list[str] = []
    for page in (_product_page(band), _goes_product_page(band)):
        try:
            html = _read_text(page)
        except Exception:
            continue
        for url in _collect_image_urls(html, folder, band):
            if url not in urls:
                urls.append(url)
    return urls


def _wfo_candidates(folder: str, band: str) -> list[str]:
    urls: list[str] = []
    for page in (WFO_REFRESH_PAGE, WFO_PAGE):
        try:
            html = _read_text(page)
        except Exception:
            continue
        for url in _collect_image_urls(html, folder, band):
            if url not in urls:
                urls.append(url)
    return urls


def _index_candidates(folder: str, band: str) -> list[str]:
    try:
        html = _read_text(f"{STAR_BASE}/{folder}/")
    except Exception:
        return []
    rows: list[tuple[str, int]] = []
    pattern = re.compile(
        r'href="([^"<>]*(\d{11})_GOES19-ABI-pr-' + re.escape(band) + r'-(1200x1200|600x600|2400x2400|300x300)\.(jpg|jpeg|png))"',
        re.IGNORECASE,
    )
    for match in pattern.finditer(html):
        href, stamp, size, _ext = match.groups()
        score = {"2400x2400": 4, "1200x1200": 3, "600x600": 2, "300x300": 1}.get(size, 0)
        rows.append((_absolute_url(href, folder), int(stamp) * 10 + score))
    rows.sort(key=lambda row: row[1], reverse=True)
    return [url for url, _score in rows[:14]]


def _loop_candidates(folder: str, band: str) -> list[str]:
    urls: list[str] = []
    for page in (f"{STAR_BASE}/{folder}/", _product_page(band), _goes_product_page(band), WFO_REFRESH_PAGE, WFO_PAGE):
        try:
            html = _read_text(page)
        except Exception:
            continue
        for url in _collect_loop_urls(html, folder, band):
            if url not in urls:
                urls.append(url)
    rows: list[tuple[str, int]] = []
    for url in urls:
        stamps = re.findall(r'(\d{11})', url)
        score = max([int(s) for s in stamps], default=0)
        rows.append((url, score))
    rows.sort(key=lambda row: row[1], reverse=True)
    return [url for url, _score in rows[:10]]


def _latest_urls(folder: str, band: str, wfo_first: bool = False) -> list[str]:
    fallback = [
        f"{STAR_BASE}/{folder}/1200x1200.jpg",
        f"{STAR_BASE}/{folder}/600x600.jpg",
        f"{STAR_BASE}/{folder}/300x300.jpg",
        f"{STAR_LEGACY_BASE}/{folder}/1200x1200.jpg",
        f"{STAR_LEGACY_BASE}/{folder}/600x600.jpg",
    ]
    groups = (_wfo_candidates(folder, band), _page_candidates(folder, band), _index_candidates(folder, band), fallback) if wfo_first else (_index_candidates(folder, band), _page_candidates(folder, band), _wfo_candidates(folder, band), fallback)
    urls: list[str] = []
    for group in groups:
        for url in group:
            if url not in urls:
                urls.append(url)
    return urls


def _svg_fallback(product: str, message: str) -> bytes:
    safe_product = product.replace("<", "").replace(">", "")
    safe_message = message.replace("<", "").replace(">", "")[:180]
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='900' viewBox='0 0 1200 900'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#0f2f4f'/><stop offset='1' stop-color='#020617'/></linearGradient></defs>
<rect width='1200' height='900' fill='url(#g)'/>
<circle cx='360' cy='320' r='130' fill='#94a3b8' opacity='.35'/><circle cx='500' cy='280' r='170' fill='#cbd5e1' opacity='.28'/><circle cx='690' cy='345' r='150' fill='#64748b' opacity='.32'/><circle cx='835' cy='295' r='115' fill='#e2e8f0' opacity='.23'/>
<rect x='120' y='445' width='960' height='230' rx='26' fill='rgba(2,6,23,.78)' stroke='#fed141' stroke-width='5'/>
<text x='600' y='530' text-anchor='middle' font-family='Arial' font-size='42' fill='#fed141' font-weight='700'>PR-WX Satellite Diagnostic</text>
<text x='600' y='592' text-anchor='middle' font-family='Arial' font-size='30' fill='#ffffff'>Producto: {safe_product}</text>
<text x='600' y='640' text-anchor='middle' font-family='Arial' font-size='24' fill='#cbd5e1'>{safe_message}</text>
<text x='600' y='742' text-anchor='middle' font-family='Arial' font-size='24' fill='#86efac'>Abra /rain/live/satellite/self-test para diagnostico.</text>
</svg>"""
    return svg.encode("utf-8")


def _download_first(urls: list[str], fallback_label: str) -> tuple[bytes, str, str, bool, str]:
    last_error = "unknown"
    for url in urls:
        try:
            with urllib.request.urlopen(_request(url), timeout=10) as response:  # nosec - public NOAA URL
                content_type = response.headers.get("Content-Type", "application/octet-stream")
                data = response.read()
                looks_like_html = data[:40].lower().lstrip().startswith((b"<html", b"<!doctype"))
                if data and len(data) > 5000 and content_type.startswith("image/") and not looks_like_html:
                    return data, content_type, url, True, "ok"
                last_error = f"invalid response: {content_type}, {len(data)} bytes from {url}"
        except Exception as exc:
            last_error = str(exc)
    return _svg_fallback(fallback_label, last_error), "image/svg+xml", "generated-fallback", False, last_error


def _satellite_response(product: str, wfo_first: bool = False) -> Response:
    if product not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Unknown satellite product")
    info = PRODUCTS[product]
    data, content_type, source_url, ok, message = _download_first(_latest_urls(info["folder"], info["band"], wfo_first=wfo_first), product)
    return Response(content=data, media_type=content_type, headers={
        "Cache-Control": "no-cache, max-age=60",
        "Content-Disposition": f"inline; filename=prwx-{product}.jpg",
        "X-PRWX-Version": VERSION,
        "X-PRWX-Source-URL": source_url,
        "X-PRWX-Proxy-OK": "true" if ok else "false",
        "X-PRWX-Proxy-Message": message[:150],
    })


def _loop_response(product: str) -> Response:
    if product not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Unknown satellite product")
    info = PRODUCTS[product]
    loops = _loop_candidates(info["folder"], info["band"])
    fallback_images = _latest_urls(info["folder"], info["band"], wfo_first=False)
    data, content_type, source_url, ok, message = _download_first(loops + fallback_images, product + " loop")
    return Response(content=data, media_type=content_type, headers={
        "Cache-Control": "no-cache, max-age=60",
        "Content-Disposition": f"inline; filename=prwx-{product}-loop.gif",
        "X-PRWX-Version": VERSION,
        "X-PRWX-Source-URL": source_url,
        "X-PRWX-Loop-OK": "true" if ok and source_url.endswith(".gif") else "false",
        "X-PRWX-Proxy-Message": message[:150],
    })


def _test_product(key: str) -> dict[str, Any]:
    info = PRODUCTS[key]
    img_data, img_type, img_url, img_ok, img_msg = _download_first(_latest_urls(info["folder"], info["band"], wfo_first=True), key)
    loop_data, loop_type, loop_url, loop_ok, loop_msg = _download_first(_loop_candidates(info["folder"], info["band"]), key + " loop")
    return {
        "product": key,
        "label": info["label"],
        "ok": img_ok,
        "loop_ok": loop_ok and loop_url.endswith(".gif"),
        "content_type": img_type,
        "loop_content_type": loop_type,
        "bytes": len(img_data),
        "loop_bytes": len(loop_data),
        "source_url": img_url,
        "loop_source_url": loop_url,
        "image": f"/rain/live/satellite/image/{key}.jpg",
        "loop": f"/rain/live/satellite/loop/{key}.gif",
        "wfo_image": f"/rain/live/satellite/wfo/{key}.jpg",
        "message": img_msg,
        "loop_message": loop_msg,
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
def rain_live_summary_route():
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
            "wfo_image": f"/rain/live/satellite/wfo/{key}.jpg",
            "loop": f"/rain/live/satellite/loop/{key}.gif",
            "urls": _latest_urls(info["folder"], info["band"], wfo_first=False)[:14],
            "loops": _loop_candidates(info["folder"], info["band"])[:8],
        }
    return {
        "version": VERSION,
        "model": "AURORA RainCast PR Animated Cloud Loop",
        "generated_utc": _utc_now(),
        "source": "NOAA/NESDIS/STAR GOES Puerto Rico CDN + animated GIF loop + WFO San Juan + PR-WX endpoints",
        "official_sector_page": OFFICIAL_SECTOR_PAGE,
        "wfo_sju_page": WFO_PAGE,
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


@router.get("/rain/live/satellite/wfo/{product}.jpg")
def rain_live_satellite_wfo_image(product: str):
    return _satellite_response(product, wfo_first=True)


@router.get("/rain/live/satellite/loop/{product}.gif")
def rain_live_satellite_loop(product: str):
    return _loop_response(product)


@router.get("/rain/live/satellite/debug/{product}.html")
def rain_live_satellite_debug(product: str):
    if product not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Unknown satellite product")
    info = PRODUCTS[product]
    urls = _latest_urls(info["folder"], info["band"], wfo_first=True)[:16]
    loops = _loop_candidates(info["folder"], info["band"])[:10]
    rows = "".join(f"<li><a href='{url}' target='_blank' rel='noopener'>{url}</a></li>" for url in urls)
    loop_rows = "".join(f"<li><a href='{url}' target='_blank' rel='noopener'>{url}</a></li>" for url in loops)
    html = f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><title>PR-WX Debug {product}</title><style>body{{font-family:Arial;background:#06111d;color:#fff;padding:24px}}a{{color:#fed141}}img{{max-width:100%;background:#000;border:1px solid #334155;border-radius:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}</style></head><body><h1>PR-WX v{VERSION} Debug {info['label']}</h1><p>Fuente CDN directa + WFO San Juan + page resolver + loop GIF.</p><p><a href='/rain/live/satellite/loop/{product}.gif'>Abrir loop GIF</a> · <a href='/rain/live/satellite/image/{product}.jpg'>Abrir image endpoint</a> · <a href='/rain/live/satellite/self-test'>Self-test JSON</a></p><div class='grid'><section><h2>Loop animado</h2><img src='/rain/live/satellite/loop/{product}.gif?debug=1'></section><section><h2>Imagen fija</h2><img src='/rain/live/satellite/image/{product}.jpg?debug=1'></section></div><h2>Candidatos de loop</h2><ol>{loop_rows}</ol><h2>Candidatos de imagen</h2><ol>{rows}</ol></body></html>"""
    return HTMLResponse(html)
