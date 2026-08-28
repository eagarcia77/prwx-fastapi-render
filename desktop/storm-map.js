/* PR-WX v2.9.0 - AI storm trajectory map for Puerto Rico. */
(function () {
  const VERSION = "2.9.0";
  let map = null;
  let stormLayer = null;
  let eventIndex = new Map();

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

  function riskColor(level, score) {
    const key = String(level || "").toLowerCase();
    if (key.includes("alto") || Number(score) >= 65) return "#b91c1c";
    if (key.includes("moder") || Number(score) >= 35) return "#f59e0b";
    return "#16a34a";
  }

  function detailHTML(event) {
    if (!event) {
      return `<p class="note">Seleccione una tormenta, onda, vaguada o corredor de trayectoria.</p>`;
    }
    const level = event.risk_level || "bajo";
    return `
      <h3>${esc(event.event_name || event.name || event.event_id || "Sistema tropical")}</h3>
      <p><span class="riskPill ${esc(level)}">${esc(level)}</span></p>
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
      <p class="note">Producto experimental; use NHC, NWS San Juan y manejo de emergencias para avisos oficiales.</p>
    `;
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
    const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors"
    });
    const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17,
      attribution: "&copy; OpenTopoMap contributors"
    });
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 18,
      attribution: "Tiles &copy; Esri"
    });
    street.addTo(map);
    L.control.layers({ "Calles": street, "Satélite": satellite, "Topográfico": topo }, {}, { collapsed: false }).addTo(map);
    stormLayer = L.layerGroup().addTo(map);
    return true;
  }

  function addFeature(feature) {
    const props = feature.properties || {};
    const geom = feature.geometry || {};
    const color = riskColor(props.risk_level, props.ai_risk_score);
    if (geom.type === "LineString") {
      const latlngs = (geom.coordinates || []).map((c) => [c[1], c[0]]);
      const line = L.polyline(latlngs, {
        color,
        weight: props.kind === "training_corridor" ? 4 : 5,
        opacity: props.kind === "training_corridor" ? 0.45 : 0.9,
        dashArray: props.kind === "training_corridor" ? "8 8" : null,
      });
      line.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      line.on("click", () => showDetails(props));
      stormLayer.addLayer(line);
    } else if (geom.type === "Point") {
      const [lon, lat] = geom.coordinates || [];
      const radius = props.kind === "reference" ? 9 : (props.kind === "storm_point" ? 7 : 8);
      const marker = L.circleMarker([lat, lon], {
        radius,
        fillColor: props.kind === "reference" ? "#0f766e" : color,
        color: "#0f172a",
        weight: 1.5,
        opacity: 1,
        fillOpacity: props.kind === "reference" ? 0.85 : 0.78,
      });
      marker.bindPopup(`<div class="leafletPopup">${detailHTML(props)}</div>`);
      marker.on("click", () => showDetails(props));
      stormLayer.addLayer(marker);
    }
  }

  function showDetails(event) {
    const target = $("stormTrackDetails");
    if (target) target.innerHTML = detailHTML(event);
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
    if (details) details.innerHTML = `<p class="note">Cargando mapa IA de trayectorias...</p>`;
    if (!initMap()) return;
    try {
      const payload = await getJSON(route("aiStormTracksGeoJSON", "/ai/storm-tracks/map.geojson"));
      stormLayer.clearLayers();
      eventIndex = new Map();
      const events = payload.analysis?.events || [];
      for (const event of events) eventIndex.set(String(event.event_id), event);
      for (const feature of payload.features || []) addFeature(feature);
      fillSelect(events);
      if (events.length) showDetails(events[0]);
      else showDetails({
        event_name: "Sin sistemas activos verificados",
        risk_level: "bajo",
        impact_probability: 0,
        ai_risk_score: 0,
        summary_es: "No hay trayectoria activa verificada en los archivos locales. Se muestran corredores históricos de entrenamiento para referencia.",
        recommendation_es: "Mantener monitoreo con NHC/NWS durante temporada ciclónica.",
      });
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
      analyze.addEventListener("click", () => {
        const event = eventIndex.get(String(select.value));
        if (event) showDetails(event);
      });
      select.addEventListener("change", () => {
        const event = eventIndex.get(String(select.value));
        if (event) showDetails(event);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    bind();
    loadStormMap();
  });
  window.PRWX_STORM_MAP = { version: VERSION, refresh: loadStormMap };
})();
