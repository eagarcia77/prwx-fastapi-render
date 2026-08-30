/* PR-WX v3.7.0 — AURORA RainCast PR live rain and flood map */
(function () {
  const VERSION = "3.7.0";
  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  const PR_TOWNS = [
    { name: "San Juan", lat: 18.4655, lon: -66.1057 },
    { name: "Ponce", lat: 18.0111, lon: -66.6141 },
    { name: "Juana Díaz", lat: 18.0525, lon: -66.5063 },
    { name: "San Germán", lat: 18.0816, lon: -67.0449 },
    { name: "Mayagüez", lat: 18.2011, lon: -67.1396 },
    { name: "Fajardo", lat: 18.3258, lon: -65.6524 },
    { name: "Arecibo", lat: 18.4724, lon: -66.7157 },
    { name: "Caguas", lat: 18.2341, lon: -66.0485 },
  ];

  class ArcGISExportOverlay {
    constructor(map, url, layerIds, options = {}) {
      this.map = map;
      this.url = String(url).replace(/\/$/, "");
      this.layerIds = Array.isArray(layerIds) ? layerIds : [layerIds];
      this.opacity = options.opacity ?? 0.72;
      this.format = options.format || "png32";
      this.transparent = options.transparent ?? true;
      this._overlay = null;
      this._visible = false;
      this._boundUpdate = this.update.bind(this);
    }

    buildUrl() {
      const bounds = this.map.getBounds();
      const sw = this.map.options.crs.project(bounds.getSouthWest());
      const ne = this.map.options.crs.project(bounds.getNorthEast());
      const size = this.map.getSize();
      const params = new URLSearchParams({
        bbox: [sw.x, sw.y, ne.x, ne.y].join(","),
        bboxSR: "3857",
        imageSR: "3857",
        size: `${Math.max(320, size.x)},${Math.max(240, size.y)}`,
        format: this.format,
        transparent: String(this.transparent),
        dpi: "96",
        f: "image",
        layers: `show:${this.layerIds.join(",")}`,
        cacheBust: String(Date.now()),
      });
      return `${this.url}/export?${params.toString()}`;
    }

    addToMap() {
      if (this._visible) {
        this.update();
        return;
      }
      this._visible = true;
      this.update();
      this.map.on("moveend zoomend resize", this._boundUpdate);
    }

    removeFromMap() {
      this._visible = false;
      this.map.off("moveend zoomend resize", this._boundUpdate);
      if (this._overlay) {
        this.map.removeLayer(this._overlay);
        this._overlay = null;
      }
    }

    update() {
      if (!this._visible) return;
      const bounds = this.map.getBounds();
      const url = this.buildUrl();
      if (this._overlay) {
        this._overlay.setUrl(url);
        this._overlay.setBounds(bounds);
      } else {
        this._overlay = L.imageOverlay(url, bounds, { opacity: this.opacity, interactive: false });
        this._overlay.addTo(this.map);
      }
    }
  }

  function apiBase() {
    const input = $("apiBase");
    if (input && input.value) return input.value.replace(/\/$/, "");
    return cfg.defaultApiBase || cfg.renderApiBase || window.location.origin;
  }

  async function getJson(path) {
    const response = await fetch(`${apiBase()}${path}`, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
    return response.json();
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (s) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[s]));
  }

  function badgeClass(levelOrEvent) {
    const text = String(levelOrEvent || "").toLowerCase();
    if (text.includes("alto") || text.includes("flash flood") || text.includes("warning") || text.includes("inund")) return "rainHigh";
    if (text.includes("moderado") || text.includes("flood") || text.includes("advisory") || text.includes("lluv")) return "rainModerate";
    return "rainLow";
  }

  function setHud(summary) {
    const now = new Date().toLocaleString("es-PR");
    const risk = summary?.risk || {};
    const alerts = summary?.alerts || {};
    const hud = $("liveRainHud");
    if (!hud) return;
    hud.innerHTML = `
      <article><span>Actualización</span><strong>${escapeHtml(now)}</strong></article>
      <article><span>Alertas lluvia/inundación</span><strong>${escapeHtml(alerts.rain_flood_alerts ?? 0)}</strong></article>
      <article><span>Riesgo PR</span><strong class="${badgeClass(risk.overall_risk_level)}">${escapeHtml(risk.overall_risk_level || "bajo")}</strong></article>
      <article><span>Modelo</span><strong>AURORA RainCast PR</strong></article>
    `;
  }

  function renderAlerts(summary) {
    const panel = $("liveRainAlertsPanel");
    if (!panel) return;
    const topAlerts = summary?.alerts?.top_alerts || [];
    const actions = summary?.recommended_actions || [];
    if (!topAlerts.length) {
      panel.innerHTML = `
        <h3>Sin anuncios prioritarios de lluvia/inundación</h3>
        <p>No se encontraron alertas activas filtradas para lluvia o inundación en Puerto Rico al momento de la consulta.</p>
        <ul>${actions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      `;
      return;
    }
    panel.innerHTML = `
      <h3>Anuncios de inundación y lluvia</h3>
      <div class="rainAlertList">
        ${topAlerts.map((alert) => `
          <article class="rainAlertCard">
            <div class="rainBadge ${badgeClass(alert.rain_priority || alert.event)}">${escapeHtml(alert.event || "Aviso")}</div>
            <h4>${escapeHtml(alert.headline || alert.event || "Alerta")}</h4>
            <p><strong>Área:</strong> ${escapeHtml(alert.area_desc || "Puerto Rico")}</p>
            <p><strong>Vigencia:</strong> ${escapeHtml(alert.effective || "N/D")} → ${escapeHtml(alert.expires || "N/D")}</p>
            <p>${escapeHtml((alert.description || alert.instruction || "Sin descripción adicional.").slice(0, 360))}${(alert.description || alert.instruction || "").length > 360 ? "…" : ""}</p>
          </article>
        `).join("")}
      </div>
      <h4>Acciones recomendadas</h4>
      <ul>${actions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    `;
  }

  function renderMunicipalRisk(payload, markerLayer) {
    const list = $("liveRainMunicipalPanel");
    if (!list || !payload) return;
    const rows = payload.municipalities || [];
    list.innerHTML = `
      <h3>Riesgo por municipio</h3>
      <div class="rainMunicipalGrid">
        ${rows.map((town) => `
          <article>
            <span class="rainBadge ${badgeClass(town.rain_risk_level)}">${escapeHtml(town.rain_risk_level)}</span>
            <strong>${escapeHtml(town.name)}</strong>
            <p>${escapeHtml(town.analysis)}</p>
            <small>Puntuación experimental: ${escapeHtml(town.rain_risk_score)}</small>
          </article>
        `).join("")}
      </div>
    `;

    if (!markerLayer) return;
    markerLayer.clearLayers();
    rows.forEach((town) => {
      const level = town.rain_risk_level;
      const color = level === "alto" ? "#ef4444" : level === "moderado" ? "#f59e0b" : "#10b981";
      const marker = L.circleMarker([town.lat, town.lon], {
        radius: Math.max(8, Math.min(18, 7 + (town.rain_risk_score || 0) / 8)),
        color: "#ffffff",
        weight: 2,
        fillColor: color,
        fillOpacity: 0.88,
      });
      marker.bindPopup(`<strong>${escapeHtml(town.name)}</strong><br>Riesgo: ${escapeHtml(level)}<br>${escapeHtml(town.analysis)}`);
      marker.addTo(markerLayer);
    });
  }

  function createMap() {
    const canvas = $("liveRainMapCanvas");
    if (!canvas || !window.L) return null;
    const map = L.map(canvas, { zoomControl: true, preferCanvas: true }).setView([18.2208, -66.5901], 8);
    const streets = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors",
    });
    const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17,
      attribution: "&copy; OpenTopoMap contributors",
    });
    streets.addTo(map);
    L.control.layers({ Calles: streets, Topográfico: topo }, {}, { collapsed: true }).addTo(map);

    const overlays = {
      radar_live: new ArcGISExportOverlay(map, "https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity/MapServer", [3], { opacity: 0.78 }),
      rain_1h: new ArcGISExportOverlay(map, "https://mapservices.weather.noaa.gov/raster/rest/services/obs/rfc_qpe/MapServer", [8], { opacity: 0.70 }),
      rain_3h: new ArcGISExportOverlay(map, "https://mapservices.weather.noaa.gov/raster/rest/services/obs/rfc_qpe/MapServer", [16], { opacity: 0.70 }),
      rain_24h: new ArcGISExportOverlay(map, "https://mapservices.weather.noaa.gov/raster/rest/services/obs/rfc_qpe/MapServer", [28], { opacity: 0.70 }),
      qpf_forecast: new ArcGISExportOverlay(map, "https://mapservices.weather.noaa.gov/vector/rest/services/precip/wpc_qpf/MapServer", [1, 2, 3], { opacity: 0.54 }),
    };
    const markerLayer = L.layerGroup().addTo(map);
    let active = "radar_live";
    overlays[active].addToMap();

    function setLayer(layerId) {
      if (!overlays[layerId]) return;
      Object.entries(overlays).forEach(([id, overlay]) => (id === layerId ? overlay.addToMap() : overlay.removeFromMap()));
      active = layerId;
      const label = $("liveRainLayerLabel");
      if (label) label.textContent = layerId.replace(/_/g, " ");
    }

    function refreshLayer() {
      overlays[active]?.update();
    }

    document.querySelectorAll("[data-rain-layer]").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll("[data-rain-layer]").forEach((btn) => btn.classList.remove("isActive"));
        button.classList.add("isActive");
        setLayer(button.getAttribute("data-rain-layer"));
      });
    });

    return { map, overlays, setLayer, refreshLayer, markerLayer };
  }

  let rainMap;
  async function refreshRain() {
    try {
      if (!rainMap) rainMap = createMap();
      const [summary, risk] = await Promise.all([
        getJson(paths.liveRainSummary || "/rain/live/summary"),
        getJson(paths.liveRainMunicipalRisk || "/rain/live/municipal-risk"),
      ]);
      setHud(summary);
      renderAlerts(summary);
      renderMunicipalRisk(risk, rainMap?.markerLayer);
      rainMap?.refreshLayer();
    } catch (error) {
      const panel = $("liveRainAlertsPanel");
      if (panel) {
        panel.innerHTML = `<h3>No se pudo cargar lluvia en vivo</h3><p>${escapeHtml(error.message)}</p>`;
      }
    }
  }

  function init() {
    if (!$("liveRainMapCanvas")) return;
    const refreshBtn = $("liveRainRefreshBtn");
    if (refreshBtn) refreshBtn.addEventListener("click", refreshRain);
    refreshRain();
    setInterval(refreshRain, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
