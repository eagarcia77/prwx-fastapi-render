/* PR-WX v3.3.0 - Advanced Leaflet municipal AI weather map. */
(function () {
  const VERSION = "3.3.0";
  let leafletMap = null;
  let markerLayer = null;
  let heatLayer = null;
  let windLayer = null;
  let lastFeatures = [];
  let heatVisible = true;
  let windVisible = false;

  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
  }
  function route(names, fallback) {
    const list = Array.isArray(names) ? names : [names];
    for (const name of list) if (paths[name]) return paths[name];
    return fallback;
  }
  async function getJSON(urlPath) {
    const response = await fetch(`${apiBase()}${urlPath}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }
  function esc(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }
  function fmt(value, digits = 1) { const n = Number(value); return Number.isFinite(n) ? n.toFixed(digits) : "N/D"; }
  function fmtPct(value) { const n = Number(value); return Number.isFinite(n) ? `${Math.round(n)}%` : "N/D"; }
  function riskLevel(props) { return String(props.ai_risk_level || props.risk_level || props.level || "bajo").toLowerCase(); }
  function score(props) {
    const n = Number(props.ai_risk_score ?? props.risk_score ?? props.score ?? 0);
    return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
  }
  function riskClass(props) {
    const level = riskLevel(props); const s = score(props);
    if (level.includes("alto") || s >= 70) return "alto";
    if (level.includes("moder") || s >= 40) return "moderado";
    return "bajo";
  }
  function riskColor(props) {
    const key = riskClass(props);
    if (key === "alto") return "#b91c1c";
    if (key === "moderado") return "#f59e0b";
    return "#16a34a";
  }
  function numeric(props, ...names) {
    for (const name of names) {
      const value = name.split(".").reduce((acc, key) => acc && acc[key], props);
      const n = Number(value);
      if (Number.isFinite(n)) return n;
    }
    return null;
  }
  function featureLatLon(feature) {
    const props = feature.properties || {}; const geom = feature.geometry || {};
    if (geom.type === "Point" && Array.isArray(geom.coordinates)) return { lat: Number(geom.coordinates[1]), lon: Number(geom.coordinates[0]) };
    return { lat: Number(props.lat), lon: Number(props.lon) };
  }

  function popupHTML(props) {
    const name = props.municipality || props.name || "Municipio";
    const temp = numeric(props, "conditions.temperature_f", "temperature_f", "temp_f");
    const rain = numeric(props, "precipitation.forecast_24h_in", "forecast_24h_in", "rain_24h_in", "rain_in");
    const analysis = props.ai_summary || props.analysis || props.summary_es || "Análisis IA experimental disponible.";
    return `<div class="leafletPopup"><h3>${esc(name)}</h3><p><span class="riskPill ${riskClass(props)}">${esc(riskLevel(props).toUpperCase())}</span></p><p><strong>Riesgo IA:</strong> ${fmt(score(props), 0)}/100</p><p><strong>Temperatura:</strong> ${fmt(temp)} °F · <strong>Lluvia 24h:</strong> ${fmt(rain, 2)} in</p><p>${esc(analysis)}</p></div>`;
  }
  function detailHTML(props) {
    const name = props.municipality || props.name || "Municipio";
    const temp = numeric(props, "conditions.temperature_f", "temperature_f", "temp_f");
    const feels = numeric(props, "conditions.feels_like_f", "feels_like_f", "heat_index_f");
    const rain = numeric(props, "precipitation.forecast_24h_in", "forecast_24h_in", "rain_24h_in", "rain_in");
    const wind = numeric(props, "conditions.wind_mph", "wind_mph", "wind_speed_mph");
    const gust = numeric(props, "conditions.wind_gust_mph", "wind_gust_mph", "gust_mph");
    const alerts = Array.isArray((props.hazards || {}).alerts) ? props.hazards.alerts.length : Number(props.alert_count || 0);
    const recommendation = props.ai_recommendation || props.recommendation || props.action || "Validar con fuentes oficiales antes de tomar decisiones operacionales.";
    const analysis = props.ai_summary || props.analysis || props.summary_es || "El análisis combina datos meteorológicos disponibles, alertas y puntuación IA experimental por municipio.";
    return `<h3>${esc(name)}</h3><p><span class="riskPill ${riskClass(props)}">${esc(riskLevel(props).toUpperCase())}</span> <span class="mapLayerBadge">Mapa IA</span></p><div class="mapDashboardGrid"><div class="mapKpi"><strong>${fmt(score(props),0)}/100</strong><span>Riesgo IA</span></div><div class="mapKpi"><strong>${fmtPct(props.ai_confidence ?? props.confidence_pct ?? props.confidence)}</strong><span>Confianza</span></div><div class="mapKpi"><strong>${fmt(temp)} °F</strong><span>Temperatura</span></div><div class="mapKpi"><strong>${fmt(feels)} °F</strong><span>Sensación</span></div><div class="mapKpi"><strong>${fmt(rain,2)} in</strong><span>Lluvia 24h</span></div><div class="mapKpi"><strong>${fmt(wind)} / ${fmt(gust)}</strong><span>Viento/ráfaga mph</span></div></div><p><strong>Alertas:</strong> ${Number.isFinite(alerts) ? alerts : 0}</p><p><strong>Análisis:</strong> ${esc(analysis)}</p><p><strong>Recomendación:</strong> ${esc(recommendation)}</p><p class="note">Mapa experimental. Los avisos oficiales deben confirmarse con NWS San Juan, NHC y manejo de emergencias.</p>`;
  }

  function chooseFeature(name) {
    const key = String(name || "").trim().toLowerCase();
    return lastFeatures.find((feature) => {
      const props = feature.properties || {};
      return String(props.municipality || props.name || "").trim().toLowerCase() === key;
    });
  }
  function setDetails(props) { const details = $("mapDetails"); if (details) details.innerHTML = detailHTML(props || {}); }
  function populateSelect(features) {
    const select = $("mapMunicipalitySelect"); if (!select) return;
    const current = select.value;
    const names = features.map((f) => (f.properties || {}).municipality || (f.properties || {}).name).filter(Boolean).sort((a,b)=>a.localeCompare(b,"es"));
    select.innerHTML = names.map((name) => `<option value="${esc(name)}">${esc(name)}</option>`).join("");
    if (current && names.includes(current)) select.value = current;
  }

  function addLayerControl() {
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" });
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Tiles &copy; Esri" });
    const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "Map data &copy; OpenStreetMap contributors, SRTM | OpenTopoMap" });
    street.addTo(leafletMap);
    L.control.layers({ "Calles": street, "Satélite": satellite, "Topográfico": topo }, {}, { collapsed: false }).addTo(leafletMap);
  }
  function addLegend() {
    const legend = L.control({ position: "bottomright" });
    legend.onAdd = function () {
      const div = L.DomUtil.create("div", "customLegend");
      div.innerHTML = `<strong>Riesgo municipal IA</strong><br><b class="low"></b>Bajo<br><b class="mod"></b>Moderado<br><b class="high"></b>Alto`;
      return div;
    };
    legend.addTo(leafletMap);
  }

  function drawMarkers(features) {
    markerLayer.clearLayers();
    features.forEach((feature) => {
      const props = feature.properties || {}; const ll = featureLatLon(feature);
      if (!Number.isFinite(ll.lat) || !Number.isFinite(ll.lon)) return;
      const s = score(props);
      const marker = L.circleMarker([ll.lat, ll.lon], { radius: Math.max(7, Math.min(18, 7 + s/10)), color: "#0f172a", weight: 1.4, fillColor: riskColor(props), fillOpacity: 0.82, className: "municipalHalo" });
      marker.bindTooltip(props.municipality || props.name || "Municipio", { direction: "top", offset: [0,-8] });
      marker.bindPopup(popupHTML(props), { maxWidth: 320 });
      marker.on("click", () => setDetails(props));
      marker.addTo(markerLayer);
    });
  }
  function drawHeat(features) {
    heatLayer.clearLayers();
    if (!heatVisible) return;
    features.forEach((feature) => {
      const props = feature.properties || {}; const ll = featureLatLon(feature);
      if (!Number.isFinite(ll.lat) || !Number.isFinite(ll.lon)) return;
      const s = score(props); const color = riskColor(props);
      L.circle([ll.lat, ll.lon], { radius: 2500 + s * 145, color, weight: 0.8, fillColor: color, fillOpacity: 0.10 }).addTo(heatLayer);
    });
  }
  function drawWind(features) {
    windLayer.clearLayers();
    if (!windVisible) return;
    features.forEach((feature, index) => {
      if (index % 2 !== 0) return;
      const props = feature.properties || {}; const ll = featureLatLon(feature);
      if (!Number.isFinite(ll.lat) || !Number.isFinite(ll.lon)) return;
      const wind = numeric(props, "conditions.wind_mph", "wind_mph", "wind_speed_mph") || 10;
      const rotation = Math.min(355, Math.max(0, wind * 9));
      const icon = L.divIcon({ className: "windArrowIcon", html: `<span style="display:inline-block;transform:rotate(${rotation}deg)">➤</span>`, iconSize: [22,22], iconAnchor: [11,11] });
      L.marker([ll.lat, ll.lon], { icon, keyboard: false }).addTo(windLayer).bindTooltip(`${props.municipality || props.name}: ${fmt(wind)} mph`);
    });
  }

  function renderLeaflet(features) {
    const canvas = $("aiMapCanvas"); if (!canvas || !window.L) return false;
    canvas.innerHTML = `<div id="leafletAiMap" class="leafletAiMap" aria-label="Mapa real interactivo de Puerto Rico con análisis IA por pueblo"></div>`;
    leafletMap = L.map("leafletAiMap", { scrollWheelZoom: true }).setView([18.22, -66.59], 9);
    addLayerControl(); addLegend();
    heatLayer = L.layerGroup().addTo(leafletMap);
    markerLayer = L.layerGroup().addTo(leafletMap);
    windLayer = L.layerGroup().addTo(leafletMap);
    drawHeat(features); drawMarkers(features); drawWind(features);
    const bounds = features.map(featureLatLon).filter((ll) => Number.isFinite(ll.lat) && Number.isFinite(ll.lon)).map((ll) => [ll.lat, ll.lon]);
    if (bounds.length) leafletMap.fitBounds(bounds, { padding: [22,22] });
    setTimeout(() => leafletMap.invalidateSize(), 200);
    return true;
  }
  function renderFallback() { const canvas = $("aiMapCanvas"); if (canvas) canvas.innerHTML = `<p class="note realMapFallback">No se pudo cargar el mapa real. Verifique conexión a internet o use el GeoJSON.</p>`; }

  async function loadRealMap() {
    const details = $("mapDetails"); if (details) details.innerHTML = `<p class="note">Cargando mapa real con IA...</p>`;
    try {
      const geo = await getJSON(route(["aiMapsGeoJSON", "aiMapsGeojson"], "/ai/maps/pr-municipalities.geojson"));
      lastFeatures = Array.isArray(geo.features) ? geo.features : [];
      populateSelect(lastFeatures);
      if (!renderLeaflet(lastFeatures)) renderFallback();
      const first = chooseFeature(($('mapMunicipalitySelect') || {}).value) || lastFeatures[0];
      if (first) setDetails(first.properties || {});
      const geoLink = $("aiMapGeoJsonLink"); if (geoLink) geoLink.href = `${apiBase()}${route(["aiMapsGeoJSON", "aiMapsGeojson"], "/ai/maps/pr-municipalities.geojson")}`;
    } catch (err) {
      if (details) details.innerHTML = `<p class="note">Error cargando mapa real: ${esc(err.message)}</p>`;
    }
  }
  function redrawLayers() { if (!leafletMap) return; drawHeat(lastFeatures); drawMarkers(lastFeatures); drawWind(lastFeatures); }
  function analyzeSelectedMunicipality() {
    const select = $("mapMunicipalitySelect"); const feature = chooseFeature(select && select.value); if (!feature) return;
    const props = feature.properties || {}; const ll = featureLatLon(feature);
    setDetails(props); if (leafletMap && Number.isFinite(ll.lat) && Number.isFinite(ll.lon)) leafletMap.flyTo([ll.lat, ll.lon], 11, { duration: 0.8 });
  }
  function resetView() {
    if (!leafletMap) return;
    const bounds = lastFeatures.map(featureLatLon).filter((ll) => Number.isFinite(ll.lat) && Number.isFinite(ll.lon)).map((ll) => [ll.lat, ll.lon]);
    if (bounds.length) leafletMap.fitBounds(bounds, { padding: [22,22] });
  }
  function initRealMap() {
    const button = $("aiMapRefreshBtn"); if (button) button.addEventListener("click", () => setTimeout(loadRealMap, 50));
    const select = $("mapMunicipalitySelect"); if (select) select.addEventListener("change", analyzeSelectedMunicipality);
    const municipalityButton = $("mapMunicipalityBtn"); if (municipalityButton) municipalityButton.addEventListener("click", analyzeSelectedMunicipality);
    const heatBtn = $("municipalHeatBtn"); if (heatBtn) heatBtn.addEventListener("click", () => { heatVisible = !heatVisible; redrawLayers(); });
    const windBtn = $("municipalWindBtn"); if (windBtn) windBtn.addEventListener("click", () => { windVisible = !windVisible; redrawLayers(); });
    const resetBtn = $("municipalResetBtn"); if (resetBtn) resetBtn.addEventListener("click", resetView);
    setTimeout(loadRealMap, 750);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initRealMap); else initRealMap();
  window.PRWX_REAL_MAP = { version: VERSION, refresh: loadRealMap, reset: resetView };
})();
