/* PR-WX v3.2.0 - Cinematic AI storm trajectory map for Puerto Rico. */
(function () {
  const VERSION = "3.2.0";
  let map = null;
  let stormLayer = null;
  let animationLayer = null;
  let eventIndex = new Map();
  let trackIndex = new Map();
  let selectedEventId = null;
  let stormMarker = null;
  let playTimer = null;
  let currentStep = 0;

  const PR_REFERENCE = { name: "Puerto Rico", lat: 18.2208, lon: -66.5901 };
  const MUNICIPALITIES = [
    { name: "San Juan", lat: 18.4655, lon: -66.1057 },
    { name: "Ponce", lat: 18.0111, lon: -66.6141 },
    { name: "Juana Díaz", lat: 18.0525, lon: -66.5066 },
    { name: "San Germán", lat: 18.0807, lon: -67.0410 },
    { name: "Fajardo", lat: 18.3258, lon: -65.6524 },
    { name: "Mayagüez", lat: 18.2011, lon: -67.1396 }
  ];

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
    const risk = riskKey(level, score);
    if (risk === "alto") return "#dc2626";
    if (risk === "moderado") return "#f59e0b";
    return "#2563eb";
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    const r = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return 2 * r * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  function impactForMunicipality(muni, track, event) {
    if (!track || !track.length) return { municipality: muni.name, distance: null, risk: "bajo", message: "Sin trayectoria activa." };
    const minDistance = Math.min(...track.map((p) => haversineKm(muni.lat, muni.lon, p[0], p[1])));
    const baseScore = Number(event?.ai_risk_score || 0);
    const proximityBoost = Math.max(0, 40 - Math.min(minDistance, 400) / 10);
    const score = Math.min(100, Math.max(0, baseScore * 0.75 + proximityBoost));
    const risk = riskKey("", score);
    let message = "Monitoreo informativo.";
    if (risk === "moderado") message = "Posible lluvia, ráfagas o deterioro indirecto.";
    if (risk === "alto") message = "Priorizar preparación y validar avisos oficiales.";
    return { municipality: muni.name, distance: Math.round(minDistance), risk, score: Math.round(score), message };
  }

  function impactGridHTML(event, track) {
    const impacts = MUNICIPALITIES.map((m) => impactForMunicipality(m, track, event));
    return `
      <h4>Impacto estimado por pueblo prioritario</h4>
      <div class="stormImpactGrid">
        ${impacts.map((item) => `
          <div class="stormImpactCard">
            <strong>${esc(item.municipality)}</strong>
            <span>${esc(item.risk)} · ${item.distance ?? "N/D"} km · ${item.score ?? 0}/100</span><br>
            <span>${esc(item.message)}</span>
          </div>
        `).join("")}
      </div>
    `;
  }

  function detailHTML(event) {
    if (!event) return `<p class="note">Seleccione una tormenta, onda, vaguada o corredor de trayectoria.</p>`;
    const level = event.risk_level || "bajo";
    const track = selectedEventId ? trackIndex.get(String(selectedEventId)) : [];
    return `
      <h3>${esc(event.event_name || event.name || event.event_id || "Sistema tropical")}</h3>
      <p><span class="riskPill ${esc(level)}">${esc(level)}</span> <span class="stormModeBadge">IA Cinemática v${VERSION}</span></p>
      <div class="municipalityMeta">
        <div><strong>Probabilidad IA</strong><br>${pct(event.impact_probability)}</div>
        <div><strong>Puntuación</strong><br>${fmt(event.ai_risk_score, 1)}/100</div>
        <div><strong>Distancia a PR</strong><br>${fmt(event.closest_distance_km, 0)} km</div>
        <div><strong>Viento máx.</strong><br>${fmt(event.max_wind_mph, 0)} mph</div>
        <div><strong>Acercándose</strong><br>${event.approaching_pr ? "Sí" : "No / incierto"}</div>
        <div><strong>Confianza</strong><br>${fmt(event.confidence, 2)}</div>
      </div>
      <p><strong>Análisis IA:</strong> ${esc(event.summary_es || event.risk_context || "Análisis no disponible.")}</p>
      <p><strong>Recomendación:</strong> ${esc(event.recommendation_es || "Validar con NHC/NWS antes de tomar decisiones.")}</p>
      ${track && track.length ? impactGridHTML(event, track) : ""}
      <p class="note">Producto experimental; use NHC, NWS San Juan y manejo de emergencias para avisos oficiales.</p>
    `;
  }

  function buildStormIcon(event) {
    const risk = riskKey(event?.risk_level, event?.ai_risk_score);
    return L.divIcon({
      className: "storm-div-icon",
      html: `
        <div class="stormIconWrap" aria-hidden="true">
          <div class="stormIconHalo"></div>
          <div class="stormIconOuter risk-${risk}"></div>
          <div class="stormIconCore"></div>
          <div class="stormIconEye"></div>
        </div>
      `,
      iconSize: [72, 72],
      iconAnchor: [36, 36]
    });
  }

  function initMap() {
    const canvas = $("stormTrackMapCanvas");
    if (!canvas) return false;
    if (!window.L) {
      canvas.innerHTML = `<div class="realMapFallback"><p class="note">Leaflet no cargó. Verifique conexión a Internet.</p></div>`;
      return false;
    }
    if (map) return true;
    canvas.innerHTML = `<div id="stormLeafletMap" class="leafletAiMap stormLeafletMap cinematic"></div>`;
    map = L.map("stormLeafletMap", { zoomControl: true, preferCanvas: true }).setView([18.2, -63.8], 5);
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "&copy; OpenStreetMap contributors" });
    const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "&copy; OpenTopoMap contributors" });
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 18, attribution: "Tiles &copy; Esri" });
    satellite.addTo(map);
    L.control.layers({ "Satélite": satellite, "Calles": street, "Topográfico": topo }, {}, { collapsed: false }).addTo(map);
    stormLayer = L.layerGroup().addTo(map);
    animationLayer = L.layerGroup().addTo(map);
    return true;
  }

  function addFeature(feature) {
    const props = feature.properties || {};
    const geom = feature.geometry || {};
    const color = riskColor(props.risk_level, props.ai_risk_score);
    if (geom.type === "LineString") {
      const latlngs = (geom.coordinates || []).map((c) => [c[1], c[0]]);
      const isCorridor = props.kind === "training_corridor";
      const line = L.polyline(latlngs, {
        color,
        weight: isCorridor ? 4 : 6,
        opacity: isCorridor ? 0.38 : 0.95,
        dashArray: isCorridor ? "8 8" : "12 7",
        className: "stormTrackGlow"
      });
      line.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      line.on("click", () => selectEvent(props.event_id, props));
      stormLayer.addLayer(line);
      if (!isCorridor && props.event_id) trackIndex.set(String(props.event_id), latlngs);
    } else if (geom.type === "Point") {
      const [lon, lat] = geom.coordinates || [];
      const radius = props.kind === "reference" ? 9 : (props.kind === "storm_point" ? 6 : 8);
      const marker = L.circleMarker([lat, lon], {
        radius,
        fillColor: props.kind === "reference" ? "#0f766e" : color,
        color: "#0f172a",
        weight: 1.5,
        opacity: 1,
        fillOpacity: props.kind === "reference" ? 0.9 : 0.75,
        className: "stormForecastDot"
      });
      marker.bindTooltip(props.forecast_label || props.name || props.event_name || "Punto", { className: "stormRouteTooltip" });
      marker.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      marker.on("click", () => props.event_id ? selectEvent(props.event_id, props) : showDetails(props));
      stormLayer.addLayer(marker);
    }
  }

  function showDetails(event) {
    const target = $("stormTrackDetails");
    if (target) target.innerHTML = detailHTML(event);
  }

  function timelineElements() {
    return {
      range: $("stormTimelineRange"),
      badge: $("stormTimeBadge"),
      play: $("stormPlayBtn"),
      pause: $("stormPauseBtn"),
      reset: $("stormResetBtn")
    };
  }

  function updateTimelineUI(track) {
    const { range, badge } = timelineElements();
    if (!range || !badge) return;
    const max = Math.max(0, (track || []).length - 1);
    range.max = String(max);
    range.value = String(Math.min(currentStep, max));
    badge.textContent = `Punto ${Math.min(currentStep, max) + 1} de ${max + 1}`;
  }

  function drawStormAtStep(eventId, step) {
    if (!map || !animationLayer) return;
    const event = eventIndex.get(String(eventId));
    const track = trackIndex.get(String(eventId)) || [];
    if (!event || !track.length) return;
    currentStep = Math.max(0, Math.min(Number(step) || 0, track.length - 1));
    animationLayer.clearLayers();
    const [lat, lon] = track[currentStep];
    stormMarker = L.marker([lat, lon], { icon: buildStormIcon(event), keyboard: false, title: event.event_name || event.event_id });
    stormMarker.bindPopup(`<div class="leafletPopup">${detailHTML(event)}</div>`);
    animationLayer.addLayer(stormMarker);
    const radius = L.circle([lat, lon], {
      radius: Math.max(40000, Math.min(220000, Number(event.closest_distance_km || 500) * 120)),
      color: riskColor(event.risk_level, event.ai_risk_score),
      fillColor: riskColor(event.risk_level, event.ai_risk_score),
      fillOpacity: 0.07,
      weight: 1
    });
    animationLayer.addLayer(radius);
    updateTimelineUI(track);
  }

  function selectEvent(eventId, fallbackProps) {
    selectedEventId = String(eventId || "");
    const event = eventIndex.get(selectedEventId) || fallbackProps;
    showDetails(event);
    currentStep = 0;
    const track = trackIndex.get(selectedEventId) || [];
    drawStormAtStep(selectedEventId, currentStep);
    if (track.length) {
      const bounds = L.latLngBounds(track.concat([[PR_REFERENCE.lat, PR_REFERENCE.lon]]));
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }

  function playSelected() {
    if (!selectedEventId) return;
    const track = trackIndex.get(selectedEventId) || [];
    if (track.length < 2) return;
    pauseSelected();
    playTimer = setInterval(() => {
      currentStep = (currentStep + 1) % track.length;
      drawStormAtStep(selectedEventId, currentStep);
    }, 1100);
  }

  function pauseSelected() {
    if (playTimer) clearInterval(playTimer);
    playTimer = null;
  }

  function resetSelected() {
    pauseSelected();
    currentStep = 0;
    if (selectedEventId) drawStormAtStep(selectedEventId, currentStep);
  }

  function fillSelect(events) {
    const select = $("stormEventSelect");
    if (!select) return;
    select.innerHTML = "";
    if (!events.length) {
      select.innerHTML = `<option value="">Sin sistemas activos verificados</option>`;
      return;
    }
    for (const event of events) {
      const opt = document.createElement("option");
      opt.value = event.event_id;
      opt.textContent = `${event.event_name || event.event_id} · ${event.risk_level || "bajo"} · ${pct(event.impact_probability)}`;
      select.appendChild(opt);
    }
  }

  async function loadStormMap() {
    const details = $("stormTrackDetails");
    if (details) details.innerHTML = `<p class="note">Cargando mapa IA cinemático de trayectorias...</p>`;
    if (!initMap()) return;
    try {
      pauseSelected();
      const payload = await getJSON(route("aiStormTracksGeoJSON", "/ai/storm-tracks/map.geojson"));
      stormLayer.clearLayers();
      animationLayer.clearLayers();
      eventIndex = new Map();
      trackIndex = new Map();
      const events = payload.analysis?.events || [];
      for (const event of events) eventIndex.set(String(event.event_id), event);
      for (const feature of payload.features || []) addFeature(feature);
      fillSelect(events);
      if (events.length) {
        selectEvent(events[0].event_id, events[0]);
      } else {
        selectedEventId = null;
        showDetails({
          event_name: "Sin sistemas activos verificados",
          risk_level: "bajo",
          impact_probability: 0,
          ai_risk_score: 0,
          summary_es: "No hay trayectoria activa verificada en los archivos locales. Se muestran corredores históricos de entrenamiento para referencia.",
          recommendation_es: "Mantener monitoreo con NHC/NWS durante temporada ciclónica."
        });
      }
      const bounds = [];
      (payload.features || []).forEach((f) => {
        if (f.geometry?.type === "Point") bounds.push([f.geometry.coordinates[1], f.geometry.coordinates[0]]);
        if (f.geometry?.type === "LineString") (f.geometry.coordinates || []).forEach((c) => bounds.push([c[1], c[0]]));
      });
      if (bounds.length) map.fitBounds(bounds, { padding: [24, 24] });
      const link = $("stormTrackGeoJsonLink");
      if (link) link.href = `${apiBase()}${route("aiStormTracksGeoJSON", "/ai/storm-tracks/map.geojson")}`;
    } catch (err) {
      if (details) details.innerHTML = `<p class="note">No se pudo cargar el mapa de trayectoria IA: ${esc(err.message)}</p>`;
    }
  }

  function bind() {
    const refresh = $("stormTrackRefreshBtn");
    if (refresh) refresh.addEventListener("click", loadStormMap);
    const analyze = $("stormEventBtn");
    const select = $("stormEventSelect");
    if (analyze && select) {
      analyze.addEventListener("click", () => selectEvent(select.value, eventIndex.get(String(select.value))));
      select.addEventListener("change", () => selectEvent(select.value, eventIndex.get(String(select.value))));
    }
    const { play, pause, reset, range } = timelineElements();
    if (play) play.addEventListener("click", playSelected);
    if (pause) pause.addEventListener("click", pauseSelected);
    if (reset) reset.addEventListener("click", resetSelected);
    if (range) range.addEventListener("input", () => {
      pauseSelected();
      drawStormAtStep(selectedEventId, Number(range.value));
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bind();
    loadStormMap();
  });
  window.PRWX_STORM_MAP = { version: VERSION, refresh: loadStormMap, play: playSelected, pause: pauseSelected };
})();
