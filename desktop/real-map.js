/* PR-WX v2.8.1 - Realistic Leaflet map layer for AI municipal weather analysis.
   This file enhances the existing SVG map with a real basemap, tile layers,
   clickable municipal markers and an AI analysis panel. */

(function () {
  const VERSION = "2.8.1";
  let leafletMap = null;
  let markerLayer = null;
  let lastFeatures = [];

  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
  }

  function path(name, fallback) {
    return paths[name] || fallback;
  }

  async function getJSON(urlPath) {
    const response = await fetch(`${apiBase()}${urlPath}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function fmt(value, digits = 1) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : "N/D";
  }

  function fmtPct(value) {
    const n = Number(value);
    return Number.isFinite(n) ? `${Math.round(n)}%` : "N/D";
  }

  function riskLevel(props) {
    return String(props.ai_risk_level || props.risk_level || props.level || "bajo").toLowerCase();
  }

  function riskColor(props) {
    const level = riskLevel(props);
    const score = Number(props.ai_risk_score ?? props.risk_score ?? props.score ?? 0);
    if (level.includes("alto") || score >= 70) return "#b91c1c";
    if (level.includes("moder") || score >= 40) return "#f59e0b";
    return "#16a34a";
  }

  function riskClass(props) {
    const level = riskLevel(props);
    const score = Number(props.ai_risk_score ?? props.risk_score ?? props.score ?? 0);
    if (level.includes("alto") || score >= 70) return "alto";
    if (level.includes("moder") || score >= 40) return "moderado";
    return "bajo";
  }

  function score(props) {
    const n = Number(props.ai_risk_score ?? props.risk_score ?? props.score ?? 0);
    return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
  }

  function popupHTML(props) {
    const name = props.municipality || props.name || "Municipio";
    const c = props.conditions || props;
    const analysis = props.ai_summary || props.analysis || props.summary_es || "Análisis IA experimental disponible.";
    return `
      <div class="leafletPopup">
        <h3>${esc(name)}</h3>
        <p><span class="riskPill ${riskClass(props)}">${esc(riskLevel(props).toUpperCase())}</span></p>
        <p><strong>Riesgo IA:</strong> ${fmt(score(props), 0)}/100</p>
        <p><strong>Temperatura:</strong> ${fmt(c.temperature_f ?? c.temp_f)} °F · <strong>Lluvia 24h:</strong> ${fmt(c.forecast_24h_in ?? c.rain_24h_in ?? c.rain_in, 2)} in</p>
        <p>${esc(analysis)}</p>
      </div>`;
  }

  function detailHTML(props) {
    const name = props.municipality || props.name || "Municipio";
    const c = props.conditions || props;
    const p = props.precipitation || props;
    const hazards = props.hazards || props;
    const alerts = Array.isArray(hazards.alerts) ? hazards.alerts.length : Number(props.alert_count || 0);
    const recommendation = props.ai_recommendation || props.recommendation || props.action || "Validar con fuentes oficiales antes de tomar decisiones operacionales.";
    const analysis = props.ai_summary || props.analysis || props.summary_es || "El análisis combina datos meteorológicos disponibles, alertas y puntuación IA experimental por municipio.";
    return `
      <h3>${esc(name)}</h3>
      <p><span class="riskPill ${riskClass(props)}">${esc(riskLevel(props).toUpperCase())}</span></p>
      <div class="municipalityMeta">
        <div><strong>Riesgo IA</strong><br>${fmt(score(props), 0)}/100</div>
        <div><strong>Confianza</strong><br>${fmtPct(props.ai_confidence ?? props.confidence_pct ?? props.confidence)}</div>
        <div><strong>Temperatura</strong><br>${fmt(c.temperature_f ?? c.temp_f)} °F</div>
        <div><strong>Sensación</strong><br>${fmt(c.feels_like_f ?? c.heat_index_f)} °F</div>
        <div><strong>Lluvia 24h</strong><br>${fmt(p.forecast_24h_in ?? p.rain_24h_in ?? p.rain_in, 2)} in</div>
        <div><strong>Viento</strong><br>${fmt(c.wind_mph ?? c.wind_speed_mph)} mph</div>
        <div><strong>Alertas</strong><br>${Number.isFinite(alerts) ? alerts : 0}</div>
        <div><strong>Fuente</strong><br>PR-WX IA</div>
      </div>
      <p><strong>Análisis:</strong> ${esc(analysis)}</p>
      <p><strong>Recomendación:</strong> ${esc(recommendation)}</p>
      <p class="note">Mapa experimental. Los avisos oficiales deben confirmarse con NWS San Juan, NHC y manejo de emergencias.</p>`;
  }

  function chooseFeature(name) {
    const key = String(name || "").trim().toLowerCase();
    return lastFeatures.find((feature) => {
      const props = feature.properties || {};
      return String(props.municipality || props.name || "").trim().toLowerCase() === key;
    });
  }

  function setDetails(props) {
    const details = $("mapDetails");
    if (details) details.innerHTML = detailHTML(props || {});
  }

  function populateSelect(features) {
    const select = $("mapMunicipalitySelect");
    if (!select) return;
    const current = select.value;
    const names = features
      .map((f) => (f.properties || {}).municipality || (f.properties || {}).name)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, "es"));
    select.innerHTML = names.map((name) => `<option value="${esc(name)}">${esc(name)}</option>`).join("");
    if (current && names.includes(current)) select.value = current;
  }

  function addLayerControl() {
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    });
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19,
      attribution: "Tiles &copy; Esri"
    });
    const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17,
      attribution: "Map data &copy; OpenStreetMap contributors, SRTM | OpenTopoMap"
    });
    street.addTo(leafletMap);
    L.control.layers({ "Calles": street, "Satélite": satellite, "Topográfico": topo }, {}, { collapsed: false }).addTo(leafletMap);
  }

  function renderLeaflet(features) {
    const canvas = $("aiMapCanvas");
    if (!canvas || !window.L) return false;
    canvas.innerHTML = `<div id="leafletAiMap" class="leafletAiMap" aria-label="Mapa real interactivo de Puerto Rico con análisis IA por pueblo"></div>`;
    leafletMap = L.map("leafletAiMap", { scrollWheelZoom: true }).setView([18.22, -66.59], 9);
    addLayerControl();
    markerLayer = L.layerGroup().addTo(leafletMap);

    const bounds = [];
    features.forEach((feature) => {
      const props = feature.properties || {};
      const geom = feature.geometry || {};
      let lat = Number(props.lat);
      let lon = Number(props.lon);
      if (geom.type === "Point" && Array.isArray(geom.coordinates)) {
        lon = Number(geom.coordinates[0]);
        lat = Number(geom.coordinates[1]);
      }
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      bounds.push([lat, lon]);
      const s = score(props);
      const marker = L.circleMarker([lat, lon], {
        radius: Math.max(7, Math.min(18, 7 + s / 10)),
        color: "#0f172a",
        weight: 1.4,
        fillColor: riskColor(props),
        fillOpacity: 0.82
      });
      marker.bindTooltip(props.municipality || props.name || "Municipio", { direction: "top", offset: [0, -8] });
      marker.bindPopup(popupHTML(props), { maxWidth: 320 });
      marker.on("click", () => setDetails(props));
      marker.addTo(markerLayer);
    });

    if (bounds.length) leafletMap.fitBounds(bounds, { padding: [22, 22] });
    setTimeout(() => leafletMap.invalidateSize(), 200);
    return true;
  }

  function renderFallback(features) {
    const canvas = $("aiMapCanvas");
    if (!canvas) return;
    canvas.innerHTML = `<p class="note realMapFallback">No se pudo cargar el mapa real. Verifique conexión a internet o use el GeoJSON.</p>`;
  }

  async function loadRealMap() {
    const details = $("mapDetails");
    if (details) details.innerHTML = `<p class="note">Cargando mapa real con IA...</p>`;
    try {
      const geo = await getJSON(path("aiMapsGeojson", "/ai/maps/pr-municipalities.geojson"));
      lastFeatures = Array.isArray(geo.features) ? geo.features : [];
      populateSelect(lastFeatures);
      if (!renderLeaflet(lastFeatures)) renderFallback(lastFeatures);
      const first = chooseFeature(($('mapMunicipalitySelect') || {}).value) || lastFeatures[0];
      if (first) setDetails(first.properties || {});
    } catch (err) {
      if (details) details.innerHTML = `<p class="note">Error cargando mapa real: ${esc(err.message)}</p>`;
    }
  }

  function analyzeSelectedMunicipality() {
    const select = $("mapMunicipalitySelect");
    const feature = chooseFeature(select && select.value);
    if (!feature) return;
    const props = feature.properties || {};
    setDetails(props);
    if (leafletMap && feature.geometry && feature.geometry.type === "Point") {
      const [lon, lat] = feature.geometry.coordinates;
      leafletMap.flyTo([lat, lon], 11, { duration: 0.8 });
    }
  }

  function initRealMap() {
    const button = $("aiMapRefreshBtn");
    if (button) button.addEventListener("click", () => setTimeout(loadRealMap, 50));
    const select = $("mapMunicipalitySelect");
    if (select) select.addEventListener("change", analyzeSelectedMunicipality);
    const municipalityButton = $("mapMunicipalityBtn");
    if (municipalityButton) municipalityButton.addEventListener("click", analyzeSelectedMunicipality);
    const geoLink = $("aiMapGeoJsonLink");
    if (geoLink) geoLink.href = `${apiBase()}${path("aiMapsGeojson", "/ai/maps/pr-municipalities.geojson")}`;
    setTimeout(loadRealMap, 750);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initRealMap);
  else initRealMap();

  window.PRWX_REAL_MAP_VERSION = VERSION;
})();
