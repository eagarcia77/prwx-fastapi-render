/* PR-WX v3.5.0 - AURORA Sahara-Caribe dust and aerosol panel. */
(function () {
  const VERSION = "3.5.0";
  let dustMap = null;
  let dustLayer = null;

  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
  }

  function route(name, fallback) {
    return paths[name] || fallback;
  }

  async function getJSON(path) {
    const response = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  function esc(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }

  function riskClass(value) {
    const key = String(value || "bajo").toLowerCase();
    if (key.includes("alto")) return "alto";
    if (key.includes("moder")) return "moderado";
    return "bajo";
  }

  function color(level, score) {
    const cls = riskClass(level);
    if (cls === "alto" || Number(score) >= 70) return "#b91c1c";
    if (cls === "moderado" || Number(score) >= 42) return "#f59e0b";
    return "#16a34a";
  }

  function initMap() {
    const canvas = $("dustMapCanvas");
    if (!canvas || !window.L) return false;
    if (dustMap) return true;
    canvas.innerHTML = '<div id="dustLeafletMap" class="leafletAiMap dustLeafletMap"></div>';
    dustMap = L.map("dustLeafletMap", { zoomControl: true, preferCanvas: true }).setView([18.2, -63.5], 5);
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 18,
      attribution: "Tiles &copy; Esri"
    });
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    });
    satellite.addTo(dustMap);
    L.control.layers({ "Satélite": satellite, "Calles": street }, {}, { collapsed: false }).addTo(dustMap);
    dustLayer = L.layerGroup().addTo(dustMap);
    return true;
  }

  function renderPanel(analysis, status) {
    const panel = $("auroraDustPanel");
    if (!panel) return;
    const highest = analysis.highest_risk_municipality || {};
    const training = status.training_status || {};
    panel.innerHTML = `
      <div class="mapDashboardGrid">
        <div class="mapKpi"><span>Modelo</span><strong>${esc(status.model?.model_name || "AURORA Sahara-Caribe")}</strong></div>
        <div class="mapKpi"><span>Mayor riesgo</span><strong>${esc(highest.municipality || "N/D")}</strong></div>
        <div class="mapKpi"><span>Puntuación polvo</span><strong>${esc(highest.dust_risk_score ?? "N/D")}/100</strong></div>
        <div class="mapKpi"><span>AOD 550 nm</span><strong>${esc(highest.aod_550nm ?? "N/D")}</strong></div>
        <div class="mapKpi"><span>PM2.5 estimado</span><strong>${esc(highest.estimated_pm25_ug_m3 ?? "N/D")} µg/m³</strong></div>
        <div class="mapKpi"><span>Filas entrenamiento</span><strong>${esc(training.rows_available ?? 0)}</strong></div>
      </div>
      <p><strong>Resumen regional:</strong> ${esc(analysis.regional_summary || "Sin resumen disponible.")}</p>
      <p><strong>Modo:</strong> ${esc(analysis.mode || "N/D")}</p>
      <p class="note">Incluye AOD, polvo mineral, PM2.5 estimado, visibilidad y riesgo respiratorio experimental. Validar con fuentes oficiales.</p>
    `;
  }

  function featurePopup(props) {
    if (props.kind === "dust_corridor") {
      return `<h3>${esc(props.name)}</h3><p>${esc(props.context)}</p><p class="note">Corredor experimental de polvo/aerosoles.</p>`;
    }
    return `
      <h3>${esc(props.municipality || "Municipio")}</h3>
      <p><span class="riskPill ${riskClass(props.dust_risk_level)}">${esc(String(props.dust_risk_level || "bajo").toUpperCase())}</span></p>
      <p><strong>Polvo IA:</strong> ${esc(props.dust_risk_score ?? "N/D")}/100</p>
      <p><strong>AOD:</strong> ${esc(props.aod_550nm ?? "N/D")} · <strong>PM2.5:</strong> ${esc(props.estimated_pm25_ug_m3 ?? "N/D")} µg/m³</p>
      <p>${esc(props.ai_summary || "Análisis no disponible.")}</p>
    `;
  }

  function renderMap(geojson) {
    if (!initMap()) return;
    dustLayer.clearLayers();
    const bounds = [];
    for (const feature of geojson.features || []) {
      const props = feature.properties || {};
      const geom = feature.geometry || {};
      if (geom.type === "LineString") {
        const latlngs = (geom.coordinates || []).map((c) => [c[1], c[0]]);
        latlngs.forEach((p) => bounds.push(p));
        const line = L.polyline(latlngs, { color: "#f59e0b", weight: 5, opacity: 0.7, dashArray: "12 8" });
        line.bindPopup(`<div class="leafletPopup">${featurePopup(props)}</div>`);
        dustLayer.addLayer(line);
      }
      if (geom.type === "Point") {
        const [lon, lat] = geom.coordinates || [];
        if (!Number.isFinite(Number(lat)) || !Number.isFinite(Number(lon))) continue;
        bounds.push([lat, lon]);
        const marker = L.circleMarker([lat, lon], {
          radius: Math.max(8, Math.min(22, 7 + Number(props.dust_risk_score || 0) / 7)),
          color: "#0f172a",
          weight: 1.5,
          fillColor: color(props.dust_risk_level, props.dust_risk_score),
          fillOpacity: 0.76,
        });
        marker.bindTooltip(props.municipality || "Municipio", { direction: "top" });
        marker.bindPopup(`<div class="leafletPopup">${featurePopup(props)}</div>`);
        dustLayer.addLayer(marker);
      }
    }
    if (bounds.length) dustMap.fitBounds(bounds, { padding: [24, 24] });
    setTimeout(() => dustMap.invalidateSize(), 250);
  }

  async function refreshDust() {
    const panel = $("auroraDustPanel");
    if (panel) panel.innerHTML = '<p class="note">Cargando AURORA Sahara-Caribe...</p>';
    try {
      const [status, analysis, mapPayload] = await Promise.all([
        getJSON(route("auroraDustStatus", "/aurora-caribe/dust/status")),
        getJSON(route("auroraDustAnalysis", "/aurora-caribe/dust/analysis")),
        getJSON(route("auroraDustMap", "/aurora-caribe/dust/map.geojson")),
      ]);
      renderPanel(analysis, status);
      renderMap(mapPayload);
      const link = $("auroraDustGeoJsonLink");
      if (link) link.href = `${apiBase()}${route("auroraDustMap", "/aurora-caribe/dust/map.geojson")}`;
    } catch (err) {
      if (panel) panel.innerHTML = `<p class="note">No se pudo cargar AURORA Sahara-Caribe: ${esc(err.message)}</p>`;
    }
  }

  function bind() {
    const btn = $("auroraDustRefreshBtn");
    if (btn) btn.addEventListener("click", refreshDust);
    setTimeout(refreshDust, 900);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();

  window.PRWX_AURORA_DUST = { version: VERSION, refresh: refreshDust };
})();
