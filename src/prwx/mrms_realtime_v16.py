from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

MRMS_IMAGE_SERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"
PR_BBOX = "-68.25,17.55,-64.25,19.25"
LAYER_TO_RASTER_FUNCTION = {
    "QPE 1h": "rft_1hr",
    "QPE 3h": "rft_3hr",
    "QPE 6h": "rft_6hr",
    "QPE 12h": "rft_12hr",
    "QPE 24h": "rft_24hr",
    "QPE 48h": "rft_48hr",
    "QPE 72h": "rft_72hr",
}


@dataclass
class MrmsRealtimeResult:
    status: str
    generated_at_utc: str
    image_urls_path: str
    summary_path: str
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_export_image_url(layer: str, *, bbox: str = PR_BBOX, width: int = 1200, height: int = 700) -> str:
    raster_function = LAYER_TO_RASTER_FUNCTION.get(layer, "rft_1hr")
    rendering_rule = json.dumps({"rasterFunction": raster_function}, separators=(",", ":"))
    params = {
        "bbox": bbox,
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width},{height}",
        "format": "png32",
        "transparent": "true",
        "renderingRule": rendering_rule,
        "f": "image",
    }
    return f"{MRMS_IMAGE_SERVER}/exportImage?{urllib.parse.urlencode(params)}"


def build_mrms_image_table(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    rows = []
    for layer, func in LAYER_TO_RASTER_FUNCTION.items():
        rows.append({
            "generated_at_utc": generated_at_utc,
            "layer": layer,
            "raster_function": func,
            "bbox": PR_BBOX,
            "image_url": build_export_image_url(layer),
            "source": "NOAA/NWS MRMS QPE ImageServer",
            "screen_reader_label": f"{layer}: imagen MRMS QPE para Puerto Rico usando función {func}.",
        })
    return pd.DataFrame(rows)


def check_mrms_service(timeout: int = 8) -> dict:
    try:
        r = requests.get(f"{MRMS_IMAGE_SERVER}?f=pjson", timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.6 educational"})
        return {"ok": bool(r.ok), "status_code": int(r.status_code), "url": MRMS_IMAGE_SERVER}
    except Exception as exc:
        return {"ok": False, "status_code": None, "url": MRMS_IMAGE_SERVER, "error": str(exc)[:200]}


def write_mrms_realtime_artifacts(root: Path, *, generated_at_utc: str | None = None) -> MrmsRealtimeResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    image_table = build_mrms_image_table(generated_at_utc)
    service_status = check_mrms_service()
    summary = {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.6.0",
        "headline": "MRMS real ImageServer preparado para mostrar radar QPE en Puerto Rico.",
        "service_status": service_status,
        "available_layers": list(LAYER_TO_RASTER_FUNCTION.keys()),
        "bbox": PR_BBOX,
        "limitations": [
            "La imagen depende del servicio externo de NOAA/NWS y de la conexión del navegador.",
            "Debe validarse con fuentes oficiales antes de decisiones operacionales.",
        ],
    }
    image_urls_path = processed / "mrms_real_image_urls_v16.csv"
    summary_path = processed / "mrms_real_summary_v16.json"
    image_table.to_csv(image_urls_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return MrmsRealtimeResult("ok", generated_at_utc, str(image_urls_path), str(summary_path), "v1.6 MRMS real image URLs generated.")
