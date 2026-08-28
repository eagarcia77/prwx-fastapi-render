/* PR-WX v3.3.0 - Advanced cinematic AI storm trajectory map. */
(function () {
  const VERSION = "3.3.0";
  const PR = { name: "Puerto Rico", lat: 18.2208, lon: -66.5901 };
  const TOWNS = [
    { name: "San Juan", lat: 18.4655, lon: -66.1057 },
    { name: "Ponce", lat: 18.0111, lon: -66.6141 },
    { name: "Juana Díaz", lat: 18.0525, lon: -66.5063 },
    { name: "San Germán", lat: 18.0816, lon: -67.0449 },
    { name: "Fajardo", lat: 18.3258, lon: -65.6524 },
    { name: "Mayagüez", lat: 18.2011, lon: -67.1396 }
  ];

  let map = null;
  let baseStormLayer = null;
  let animationLayer = null;
  let impactLayer = null;
  let radarOverlay = null;
  let animatedMarker = null;
  let animationTimer = null;
  let activeTrack = [];
  let activeEvent = null;
  let eventIndex = new Map();
  let impactVisible = true;
  let radarVisible = false;

  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
  }
  function route(name, fallback) { return paths[name] || fallback; }
  async function getJSON(path) {
    const response = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }
  function esc(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }
  function fmt(value, digits = 1) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : "N/D";
  }
  function pct(value) {
    const n = Number(value);
    return Number.isFinite(n) ? `${Math.round(n * 100)}%` : "N/D";
  }
  function riskKey(level, score) {
    const key = String(level || "").toLowerCase();
    if (key.includes("alto") || Number(score) >= 65) return "alto";
    if (key.includes("moder") || Number(score) >= 35) return "moderado";
    return "bajo";
  }
  function riskColor(level, score) {
    const key = riskKey(level, score);
    if (key === "alto") return "#b91c1c";
    if (key === "moderado") return "#f59e0b";
    return "#16a34a";
  }
  function distanceKm(a, b) {
    const r = 6371;
    const dLat = (b.lat - a.lat) * Math.PI / 180;
    const dLon = (b.lon - a.lon) * Math.PI / 180;
    const lat1 = a.lat * Math.PI / 180;
    const lat2 = b.lat * Math.PI / 180;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    return 2 * r * Math.asin(Math.min(1, Math.sqrt(h)));
  }

  function initMap() {
    const canvas = $("stormTrackMapCanvas");
    if (!canvas) return false;
    if (!window.L) {
      canvas.innerHTML = `<div class="realMapFallback"><p class="note">Leaflet no cargó. Verifique conexión a Internet.</p></div>`;
      return false;
    }
    if (map) return true;
    canvas.innerHTML = `<div id="stormLeafletMap" class="leafletAiMap stormLeafletMap"></div>`;
    map = L.map("stormLeafletMap", { zoomControl: true, preferCanvas: true }).setView([18.2, -63.8], 5);

    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 18, attribution: "Tiles &copy; Esri" });
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" });
    const dark = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap &copy; CARTO" });
    satellite.addTo(map);
    L.control.layers({ "Satélite": satellite, "Calles": street, "Centro de Operaciones": dark }, {}, { collapsed: false }).addTo(map);
    baseStormLayer = L.layerGroup().addTo(map);
    animationLayer = L.layerGroup().addTo(map);
    impactLayer = L.layerGroup().addTo(map);
    L.circleMarker([PR.lat, PR.lon], { radius: 10, color: "#0f172a", weight: 2, fillColor: "#fed141", fillOpacity: 0.95 }).addTo(baseStormLayer).bindPopup("<strong>Puerto Rico</strong><br>Punto central de análisis IA.");
    addLegend();
    addRadarOverlay(false);
    return true;
  }

  function addLegend() {
    const legend = L.control({ position: "bottomleft" });
    legend.onAdd = function () {
      const div = L.DomUtil.create("div", "customLegend");
      div.innerHTML = `<strong>PR-WX IA</strong><br><b class="low"></b>Bajo<br><b class="mod"></b>Moderado<br><b class="high"></b>Alto`;
      return div;
    };
    legend.addTo(map);
  }
  function addRadarOverlay(show) {
    const container = $("stormTrackMapCanvas");
    if (!container) return;
    if (!radarOverlay) {
      radarOverlay = document.createElement("div");
      radarOverlay.className = "radarSweep off";
      container.appendChild(radarOverlay);
    }
    radarOverlay.classList.toggle("off", !show);
  }

  function detailHTML(event) {
    if (!event) return `<p class="note">Seleccione una tormenta, onda, vaguada o corredor de trayectoria.</p>`;
    const level = riskKey(event.risk_level, event.ai_risk_score);
    const impacts = townImpacts(event).map((item) => `<div class="impactItem ${item.level}"><strong>${esc(item.name)}</strong><br>${item.score}/100 · ${esc(item.mainHazard)}</div>`).join("");
    return `
      <h3>${esc(event.event_name || event.name || event.event_id || "Sistema tropical")}</h3>
      <p><span class="riskPill ${level}">${esc(level.toUpperCase())}</span> <span class="mapLayerBadge">IA ${pct(event.impact_probability)}</span></p>
      <div class="mapDashboardGrid">
        <div class="mapKpi"><strong>${fmt(event.ai_risk_score, 0)}</strong><span>Puntuación IA</span></div>
        <div class="mapKpi"><strong>${fmt(event.closest_distance_km, 0)} km</strong><span>Distancia a PR</span></div>
        <div class="mapKpi"><strong>${fmt(event.max_wind_mph, 0)} mph</strong><span>Viento máx.</span></div>
      </div>
      <p><strong>Análisis IA:</strong> ${esc(event.summary_es || event.risk_context || "Análisis no disponible.")}</p>
      <p><strong>Recomendación:</strong> ${esc(event.recommendation_es || "Validar con NHC/NWS antes de tomar decisiones.")}</p>
      <p><strong>Impacto estimado por pueblo:</strong></p>
      <div class="impactList">${impacts}</div>
      <p class="note">Producto experimental; use NHC, NWS San Juan y manejo de emergencias para avisos oficiales.</p>
    `;
  }
  function showDetails(event) {
    activeEvent = event || activeEvent;
    const target = $("stormTrackDetails");
    if (target) target.innerHTML = detailHTML(activeEvent);
  }

  function stormIcon(level, score) {
    const key = riskKey(level, score);
    return L.divIcon({
      className: "storm-div-icon",
      html: `<div class="stormVisual"><div class="stormCore ${key}"><div class="stormEye"></div></div></div>`,
      iconSize: [66, 66],
      iconAnchor: [33, 33]
    });
  }

  function addFeature(feature) {
    const props = feature.properties || {};
    const geom = feature.geometry || {};
    const color = riskColor(props.risk_level, props.ai_risk_score);
    if (geom.type === "LineString") {
      const latlngs = (geom.coordinates || []).map((c) => [c[1], c[0]]);
      const isCorridor = props.kind === "training_corridor";
      const line = L.polyline(latlngs, { color, weight: isCorridor ? 4 : 6, opacity: isCorridor ? 0.42 : 0.95, dashArray: isCorridor ? "10 9" : "12 8", lineCap: "round" });
      line.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      line.on("click", () => { showDetails(props); setTrack(latlngs, props); });
      baseStormLayer.addLayer(line);
      if (!isCorridor && latlngs.length && !activeTrack.length) setTrack(latlngs, props);
    } else if (geom.type === "Point") {
      const [lon, lat] = geom.coordinates || [];
      const marker = L.circleMarker([lat, lon], { radius: props.kind === "reference" ? 9 : 7, fillColor: props.kind === "reference" ? "#fed141" : color, color: "#0f172a", weight: 1.5, opacity: 1, fillOpacity: 0.85 });
      marker.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      marker.on("click", () => showDetails(props));
      baseStormLayer.addLayer(marker);
    }
  }

  function setTrack(latlngs, event) {
    activeTrack = latlngs || [];
    activeEvent = event || activeEvent;
    const range = $("stormTimeline") || $("stormTimelineRange");
    if (range) { range.max = Math.max(0, activeTrack.length - 1); range.value = 0; }
    updateTimelineLabel(0);
    drawAnimatedMarker(0);
    if (impactVisible) drawImpactLayer();
    showDetails(activeEvent);
  }
  function updateTimelineLabel(index) {
    const label = $("stormTimelineLabel") || $("stormTimeBadge");
    if (!label) return;
    const hour = activeEvent && Number.isFinite(Number(activeEvent.forecast_hour)) ? Number(activeEvent.forecast_hour) : index * 12;
    label.textContent = `+${Math.round(hour)}h`;
  }
  function drawAnimatedMarker(index) {
    if (!map || !activeTrack.length) return;
    const latlng = activeTrack[Math.max(0, Math.min(index, activeTrack.length - 1))];
    if (!animatedMarker) {
      animatedMarker = L.marker(latlng, { icon: stormIcon(activeEvent && activeEvent.risk_level, activeEvent && activeEvent.ai_risk_score), keyboard: false }).addTo(animationLayer);
    } else {
      animatedMarker.setLatLng(latlng);
    }
  }
  function play() {
    if (!activeTrack.length) return;
    pause();
    const range = $("stormTimeline") || $("stormTimelineRange");
    animationTimer = setInterval(() => {
      const next = ((range ? Number(range.value) : 0) + 1) % activeTrack.length;
      if (range) range.value = next;
      drawAnimatedMarker(next);
      updateTimelineLabel(next);
    }, 1100);
  }
  function pause() { if (animationTimer) { clearInterval(animationTimer); animationTimer = null; } }
  function reset() { pause(); const range = $("stormTimeline") || $("stormTimelineRange"); if (range) range.value = 0; drawAnimatedMarker(0); updateTimelineLabel(0); }

  function townImpacts(event) {
    const baseProb = Number(event && event.impact_probability) || 0.12;
    const levelBoost = riskKey(event && event.risk_level, event && event.ai_risk_score) === "alto" ? 26 : riskKey(event && event.risk_level, event && event.ai_risk_score) === "moderado" ? 15 : 6;
    const center = activeTrack.length ? { lat: activeTrack[Math.floor(activeTrack.length / 2)][0], lon: activeTrack[Math.floor(activeTrack.length / 2)][1] } : PR;
    return TOWNS.map((town) => {
      const d = distanceKm(town, center);
      const score = Math.max(8, Math.min(96, Math.round(baseProb * 58 + levelBoost + Math.max(0, 35 - d / 7))));
      const level = score >= 65 ? "alto" : score >= 38 ? "moderado" : "bajo";
      const mainHazard = level === "alto" ? "viento, lluvia e inundaciones" : level === "moderado" ? "lluvia y ráfagas" : "monitoreo preventivo";
      return { ...town, score, level, mainHazard };
    }).sort((a, b) => b.score - a.score);
  }
  function drawImpactLayer() {
    impactLayer.clearLayers();
    if (!impactVisible || !activeEvent) return;
    townImpacts(activeEvent).forEach((item) => {
      const color = riskColor(item.level, item.score);
      const circle = L.circle([item.lat, item.lon], { radius: 8000 + item.score * 180, color, weight: 1, fillColor: color, fillOpacity: 0.13, className: "impactRing" }).addTo(impactLayer);
      circle.bindPopup(`<strong>${esc(item.name)}</strong><br>Impacto IA: ${item.score}/100<br>${esc(item.mainHazard)}`);
      const dot = L.circleMarker([item.lat, item.lon], { radius: 5, color: "#0f172a", fillColor: color, fillOpacity: 0.95, weight: 1 }).addTo(impactLayer);
      dot.bindTooltip(`${item.name}: ${item.score}/100`, { direction: "top" });
    });
  }

  function fillSelect(events) {
    const select = $("stormEventSelect");
    if (!select) return;
    select.innerHTML = "";
    if (!events.length) { select.innerHTML = `<option value="">Sin sistemas activos verificados</option>`; return; }
    events.forEach((event) => {
      const opt = document.createElement("option");
      opt.value = event.event_id;
      opt.textContent = `${event.event_name || event.event_id} · ${event.risk_level || "bajo"} · ${pct(event.impact_probability)}`;
      select.appendChild(opt);
    });
  }

  async function loadStormMap() {
    const details = $("stormTrackDetails");
    if (details) details.innerHTML = `<p class="note">Cargando mapa IA de trayectorias...</p>`;
    if (!initMap()) return;
    try {
      const payload = await getJSON(route("aiStormTracksGeoJSON", "/ai/storm-tracks/map.geojson"));
      baseStormLayer.clearLayers(); animationLayer.clearLayers(); impactLayer.clearLayers(); activeTrack = []; activeEvent = null; animatedMarker = null; pause();
      eventIndex = new Map();
      const events = payload.analysis && payload.analysis.events ? payload.analysis.events : [];
      events.forEach((event) => eventIndex.set(String(event.event_id), event));
      (payload.features || []).forEach(addFeature);
      fillSelect(events);
      if (events.length && !activeEvent) activeEvent = events[0];
      if (activeEvent) showDetails(activeEvent);
      const bounds = [];
      (payload.features || []).forEach((f) => {
        if (f.geometry && f.geometry.type === "Point") bounds.push([f.geometry.coordinates[1], f.geometry.coordinates[0]]);
        if (f.geometry && f.geometry.type === "LineString") (f.geometry.coordinates || []).forEach((c) => bounds.push([c[1], c[0]]));
      });
      if (bounds.length) map.fitBounds(bounds, { padding: [28, 28] });
      const link = $("stormTrackGeoJsonLink"); if (link) link.href = `${apiBase()}${route("aiStormTracksGeoJSON", "/ai/storm-tracks/map.geojson")}`;
    } catch (err) {
      if (details) details.innerHTML = `<p class="note">No se pudo cargar el mapa de trayectoria IA: ${esc(err.message)}</p>`;
    }
  }

  function bind() {
    const refresh = $("stormTrackRefreshBtn"); if (refresh) refresh.addEventListener("click", loadStormMap);
    const analyze = $("stormEventBtn"); const select = $("stormEventSelect");
    if (analyze && select) {
      const choose = () => { const event = eventIndex.get(String(select.value)); if (event) { activeEvent = event; showDetails(event); drawImpactLayer(); } };
      analyze.addEventListener("click", choose); select.addEventListener("change", choose);
    }
    const range = $("stormTimeline") || $("stormTimelineRange");
    if (range) range.addEventListener("input", () => { const i = Number(range.value); drawAnimatedMarker(i); updateTimelineLabel(i); });
    const playBtn = $("stormPlayBtn"); if (playBtn) playBtn.addEventListener("click", play);
    const pauseBtn = $("stormPauseBtn"); if (pauseBtn) pauseBtn.addEventListener("click", pause);
    const resetBtn = $("stormResetBtn"); if (resetBtn) resetBtn.addEventListener("click", reset);
    const impactBtn = $("stormImpactBtn"); if (impactBtn) impactBtn.addEventListener("click", () => { impactVisible = !impactVisible; drawImpactLayer(); });
    const radarBtn = $("stormRadarBtn"); if (radarBtn) radarBtn.addEventListener("click", () => { radarVisible = !radarVisible; addRadarOverlay(radarVisible); });
  }

  document.addEventListener("DOMContentLoaded", () => { bind(); loadStormMap(); });
  window.PRWX_STORM_MAP = { version: VERSION, refresh: loadStormMap, play, pause, reset };
})();
