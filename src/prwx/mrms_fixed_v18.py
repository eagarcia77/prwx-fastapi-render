from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

MRMS_IMAGE_SERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"
MRMS_ITEMINFO = f"{MRMS_IMAGE_SERVER}/info/iteminfo"
PR_EXTENT_4326 = {"xmin": -68.25, "ymin": 17.55, "xmax": -64.25, "ymax": 19.25, "spatialReference": {"wkid": 4326}}
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
class MrmsFixedResult:
    status: str
    generated_at_utc: str
    url_table_path: str
    summary_path: str
    html_path: str
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def arcgis_rendering_rule(raster_function: str) -> str:
    return json.dumps({"rasterFunction": raster_function}, separators=(",", ":"))


def build_export_image_url(layer: str, *, f: str = "image", width: int = 1400, height: int = 820) -> str:
    raster_function = LAYER_TO_RASTER_FUNCTION.get(layer, "rft_1hr")
    params = {
        "bbox": json.dumps(PR_EXTENT_4326, separators=(",", ":")),
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width},{height}",
        "format": "png32",
        "transparent": "true",
        "renderingRule": arcgis_rendering_rule(raster_function),
        "f": f,
    }
    return f"{MRMS_IMAGE_SERVER}/exportImage?{urllib.parse.urlencode(params)}"


def build_arcgis_js_html(default_layer: str = "QPE 1h") -> str:
    # This avoids Streamlit/server-side image fetching and lets the browser load the ArcGIS ImageServer directly.
    layer_options = "\n".join([f'<option value="{fn}" {"selected" if name == default_layer else ""}>{name}</option>' for name, fn in LAYER_TO_RASTER_FUNCTION.items()])
    return f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="stylesheet" href="https://js.arcgis.com/4.30/esri/themes/light/main.css">
<script src="https://js.arcgis.com/4.30/"></script>
<style>
html, body, #viewDiv {{ padding:0; margin:0; height:650px; width:100%; font-family:Arial, sans-serif; }}
#panel {{ position:absolute; z-index:10; top:12px; left:12px; background:white; border:2px solid #0f172a; border-radius:10px; padding:10px; max-width:460px; }}
#panel label {{ font-weight:700; color:#0f172a; }}
#status {{ margin-top:6px; font-size:14px; color:#334155; }}
select, button {{ padding:6px; margin-top:5px; font-size:14px; }}
</style>
</head>
<body>
<div id="panel">
<label for="layerSelect">Capa MRMS QPE real</label><br>
<select id="layerSelect">{layer_options}</select>
<button id="reloadBtn">Actualizar capa</button>
<div id="status">Cargando MRMS ImageServer de NOAA/NWS…</div>
</div>
<div id="viewDiv" role="img" aria-label="Mapa MRMS QPE real de Puerto Rico"></div>
<script>
require(["esri/Map", "esri/views/MapView", "esri/layers/ImageryLayer", "esri/geometry/Extent"], function(Map, MapView, ImageryLayer, Extent) {{
  const serviceUrl = "{MRMS_IMAGE_SERVER}";
  const prExtent = new Extent({json.dumps(PR_EXTENT_4326)});
  let layer = null;
  const map = new Map({{ basemap: "gray-vector" }});
  const view = new MapView({{
    container: "viewDiv",
    map: map,
    extent: prExtent,
    constraints: {{ minZoom: 5, maxZoom: 14 }}
  }});

  function setLayer(fn) {{
    document.getElementById("status").textContent = "Cargando función raster " + fn + "…";
    if (layer) {{ map.remove(layer); }}
    layer = new ImageryLayer({{
      url: serviceUrl,
      opacity: 0.72,
      renderingRule: {{ rasterFunction: fn }}
    }});
    layer.when(function() {{
      document.getElementById("status").textContent = "MRMS cargado. Si no se ve precipitación, puede que no haya lluvia significativa o el servicio externo esté lento.";
    }}).catch(function(error) {{
      document.getElementById("status").textContent = "No se pudo cargar MRMS. Use el radar de respaldo o abra el enlace REST.";
      console.error(error);
    }});
    map.add(layer);
  }}

  document.getElementById("reloadBtn").addEventListener("click", function() {{
    setLayer(document.getElementById("layerSelect").value);
  }});
  document.getElementById("layerSelect").addEventListener("change", function() {{
    setLayer(this.value);
  }});
  setLayer(document.getElementById("layerSelect").value);
}});
</script>
</body>
</html>
""".strip()


def test_service(timeout: int = 10) -> dict[str, Any]:
    result: dict[str, Any] = {"service_url": MRMS_IMAGE_SERVER, "metadata_ok": False, "export_image_ok": False, "notes": []}
    try:
        r = requests.get(f"{MRMS_IMAGE_SERVER}?f=pjson", timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.8 educational"})
        result["metadata_status"] = int(r.status_code)
        result["metadata_ok"] = bool(r.ok and "rasterFunctionInfos" in r.text)
    except Exception as exc:
        result["metadata_error"] = str(exc)[:240]
    try:
        # JSON form is lighter and validates the export endpoint without downloading a large image.
        test_url = build_export_image_url("QPE 1h", f="json", width=500, height=320)
        r = requests.get(test_url, timeout=timeout, headers={"User-Agent": "PR-WX-Hybrid-Model/1.8 educational"})
        result["export_status"] = int(r.status_code)
        result["export_image_ok"] = bool(r.ok and ("href" in r.text or "Image" in r.text or r.headers.get("content-type", "").startswith("image")))
        result["export_content_type"] = r.headers.get("content-type", "")
    except Exception as exc:
        result["export_error"] = str(exc)[:240]
    if not result.get("export_image_ok"):
        result["notes"].append("MRMS may still be available in the browser through ArcGIS JS even if server-side testing fails.")
    return result


def build_url_table(generated_at_utc: str | None = None) -> pd.DataFrame:
    generated_at_utc = generated_at_utc or utc_now_iso()
    rows: list[dict[str, Any]] = []
    for layer, fn in LAYER_TO_RASTER_FUNCTION.items():
        rows.append({
            "generated_at_utc": generated_at_utc,
            "layer": layer,
            "raster_function": fn,
            "arcgis_export_image_url": build_export_image_url(layer, f="image"),
            "arcgis_export_json_url": build_export_image_url(layer, f="json"),
            "arcgis_service_url": MRMS_IMAGE_SERVER,
            "iteminfo_url": MRMS_ITEMINFO,
            "status": "browser_arcgis_js_preferred",
            "screen_reader_label": f"{layer}: MRMS QPE real de NOAA/NWS para Puerto Rico. Si la imagen no carga, use radar de respaldo.",
        })
    return pd.DataFrame(rows)


def write_mrms_fixed_artifacts(root: Path, *, generated_at_utc: str | None = None) -> MrmsFixedResult:
    generated_at_utc = generated_at_utc or utc_now_iso()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    url_table = build_url_table(generated_at_utc)
    status = test_service()
    summary = {
        "generated_at_utc": generated_at_utc,
        "model_version": "1.8.0",
        "headline": "MRMS corregido: se usa ArcGIS JS en el navegador y se mantiene radar de respaldo.",
        "why_previous_may_fail": [
            "Algunos entornos Docker/Streamlit no descargan bien imágenes externas generadas por exportImage.",
            "El navegador puede cargar el ImageServer con ArcGIS JS aunque el servidor local no pueda bajar la imagen.",
            "Si no hay precipitación significativa, la capa puede verse transparente aunque esté funcionando.",
        ],
        "service_test": status,
        "life_safety_note": "El radar es apoyo operacional; las decisiones de emergencia deben validarse con NWS/NOAA y manejo de emergencias.",
    }
    url_path = processed / "mrms_fixed_urls_v18.csv"
    summary_path = processed / "mrms_fixed_summary_v18.json"
    html_path = processed / "mrms_arcgis_viewer_v18.html"
    url_table.to_csv(url_path, index=False)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(build_arcgis_js_html(), encoding="utf-8")
    return MrmsFixedResult("ok", generated_at_utc, str(url_path), str(summary_path), str(html_path), "v1.8 MRMS fixed artifacts generated.")
