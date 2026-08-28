const $ = (id) => document.getElementById(id);
const cfg = window.PRWX_CONFIG || {};
const paths = cfg.paths || {};

function log(message) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  $("log").textContent = `${line}\n${$("log").textContent}`.slice(0, 6000);
}

function apiBase() {
  return ($("apiBase").value || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
}

async function getJSON(path) {
  const url = `${apiBase()}${path}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} - ${url}`);
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

function fmtInt(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.round(n).toLocaleString("es-PR") : "0";
}

function card(title, value, detail, cls = "ok") {
  return `<article class="card metric ${cls}"><span>${esc(title)}</span><strong>${esc(value)}</strong><p>${esc(detail || "")}</p></article>`;
}

function renderTable(rows) {
  const table = $("dataTable");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";
  if (!Array.isArray(rows) || rows.length === 0) {
    tbody.innerHTML = `<tr><td>No hay datos para mostrar.</td></tr>`;
    return;
  }
  const priority = ["municipality", "risk_level", "risk_score", "temp_f", "feels_like_f", "rain_in", "wind_mph", "headline", "severity", "cluster_status"];
  const columns = [...priority.filter((c) => c in rows[0]), ...Object.keys(rows[0]).filter((c) => !priority.includes(c))].slice(0, 9);
  thead.innerHTML = `<tr>${columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr>`;
  tbody.innerHTML = rows.slice(0, 20).map((r) => `<tr>${columns.map((c) => `<td>${esc(r[c] ?? "")}</td>`).join("")}</tr>`).join("");
}

function renderWeatherReport(report) {
  const target = $("weatherReport");
  if (!report || report.error) {
    target.innerHTML = `<p class="note">No se pudo generar el informe: ${esc(report?.error || "sin datos")}</p>`;
    return;
  }
  const c = report.conditions || {};
  const p = report.precipitation || {};
  const h = report.hazards || {};
  const m = report.model || {};
  const alerts = Array.isArray(h.alerts) ? h.alerts : [];
  target.innerHTML = `
    <div class="grid">
      ${card("Temperatura", `${fmt(c.temperature_f)} °F`, `Sensación: ${fmt(c.feels_like_f)} °F`)}
      ${card("Humedad", `${fmt(c.relative_humidity_pct, 0)}%`, "Humedad relativa")}
      ${card("Viento", `${fmt(c.wind_mph)} mph`, `Ráfaga: ${fmt(c.wind_gust_mph)} mph`)}
      ${card("Lluvia 24 h", `${fmt(p.forecast_24h_in, 2)} in`, `Rango P10–P90: ${fmt(p.p10_in, 2)}–${fmt(p.p90_in, 2)} in`)}
      ${card("Impacto", h.risk_level || "N/D", `${alerts.length} alerta(s) asociada(s)`, alerts.length ? "warn" : "ok")}
      ${card("PR-CARIBE v2", m.status || "training_required", m.production_validated ? "Validado" : "Aún no validado para producción", m.production_validated ? "ok" : "warn")}
    </div>
    <p><strong>Resumen:</strong> ${esc(report.summary_es || "")}</p>
    <p class="note">${esc(report.disclaimer || "")}</p>
  `;
}

function renderCaribbeanAtlanticReport(report) {
  const target = $("caribbeanReport");
  if (!report || report.error) {
    target.innerHTML = `<p class="note">No se pudo cargar el informe Caribe-Atlántico: ${esc(report?.error || "sin datos")}</p>`;
    return;
  }
  const analysis = report.model_analysis || {};
  const decision = analysis.decision || {};
  const matrix = Array.isArray(report.feature_matrix) ? report.feature_matrix : [];
  const plan = report.training_plan || {};
  const minimum = plan.minimum_real_training_dataset || {};
  target.innerHTML = `
    <div class="grid">
      ${card("Informe", report.report_version || "2.6.0", "Caribe · Atlántico · Puerto Rico")}
      ${card("Modelo", analysis.current_model_name || "PR-CARIBE WX", analysis.current_model_version || "v2", "Modelo híbrido experimental")}
      ${card("Preparación", analysis.readiness_label || "entrenamiento requerido", decision.recommendation || "train_new_caribbean_atlantic_model", "warn")}
      ${card("Mínimo operacional", `${fmtInt(minimum.rows_operational_candidate)} filas`, `${fmtInt(minimum.minimum_days_operational_candidate)} días · ${fmtInt(minimum.minimum_stations_operational_candidate)} estaciones`, "warn")}
    </div>
    <h3>Matriz de fuentes</h3>
    <ul>
      ${matrix.map((item) => `<li><strong>${esc(item.domain)}</strong>: ${esc((item.sources || []).join(", "))}. ${esc(item.training_role || "")}</li>`).join("")}
    </ul>
    <p class="note">${esc(report.disclaimer || "")}</p>
  `;
}

async function loadWeatherReport() {
  const municipality = ($("municipalityInput").value || "").trim();
  if (!municipality) {
    $("weatherReport").innerHTML = `<p class="note">Escriba un municipio.</p>`;
    return;
  }
  $("weatherReport").innerHTML = `<p class="note">Generando informe para ${esc(municipality)}...</p>`;
  const template = paths.weatherReport || "/weather/report/{municipality}";
  const path = template.replace("{municipality}", encodeURIComponent(municipality));
  try {
    const report = await getJSON(path);
    renderWeatherReport(report);
    log(`Informe meteorológico generado para ${municipality}.`);
  } catch (err) {
    renderWeatherReport({ error: err.message });
    log(`Error de informe: ${err.message}`);
  }
}

async function loadCaribbeanAtlanticReport() {
  $("caribbeanReport").innerHTML = `<p class="note">Generando informe meteorológico Caribe-Atlántico...</p>`;
  try {
    const report = await getJSON(paths.caribbeanAtlanticReport || "/weather/report/caribbean-atlantic");
    renderCaribbeanAtlanticReport(report);
    log("Informe Caribe-Atlántico actualizado.");
  } catch (err) {
    renderCaribbeanAtlanticReport({ error: err.message });
    log(`Error en informe Caribe-Atlántico: ${err.message}`);
  }
}

async function refresh() {
  const cards = $("cards");
  cards.innerHTML = card("Estado", "Cargando", "Consultando Render...", "warn");
  log(`API: ${apiBase()}`);
  const results = await Promise.allSettled([
    getJSON(paths.health || "/healthz"),
    getJSON(paths.desktopHealth || "/desktop-health"),
    getJSON(paths.apiStatus || "/api/status"),
    getJSON(paths.webBridge || "/web-bridge/status"),
    getJSON(paths.alerts || "/alerts/active"),
    getJSON(paths.temperatureFocus || "/temperature/focus"),
    getJSON(paths.mobileCluster || "/seismic/mobile-cluster"),
    getJSON(paths.caribbeanModelStatus || "/caribbean/model/status"),
    getJSON(paths.caribbeanModelReadiness || "/caribbean/model/readiness"),
    getJSON(paths.caribbeanTrainingStatus || "/caribbean/training/status"),
    getJSON(paths.caribbeanTrainingPlan || "/caribbean/model/training-plan")
  ]);
  const [health, desktopHealth, apiStatus, webBridge, alerts, focus, cluster, modelStatus, readiness, trainingStatus, trainingPlan] = results.map((r) => r.status === "fulfilled" ? r.value : { error: r.reason.message });
  const alertsCount = Array.isArray(alerts) ? alerts.length : 0;
  const focusCount = Array.isArray(focus) ? focus.length : 0;
  const clusterStatus = cluster.cluster_status || cluster.status || "sin cluster";
  const modelState = modelStatus.status || "training_required";
  const candidate = readiness.operational_candidate === true;
  const observations = trainingStatus.observations || {};
  const trainingTable = trainingStatus.training_table || {};
  const minData = trainingPlan.minimum_real_training_dataset || {};
  const historicalDetail = observations.available
    ? `${fmtInt(observations.rows)} observaciones · ${fmtInt(observations.stations)} estaciones`
    : "Backfill histórico aún no disponible en este servidor";
  const tableDetail = trainingTable.available
    ? `${fmtInt(trainingTable.rows)} filas ensambladas`
    : "Tabla de entrenamiento pendiente";

  cards.innerHTML = [
    card("API", health.status || "error", health.service || health.error || "healthz"),
    card("Desktop", desktopHealth.status || "error", `index: ${desktopHealth.desktop_index_exists === true}`),
    card("Versión", apiStatus.version || webBridge.version || cfg.version || "N/D", "Render + GitHub"),
    card("Alertas", alertsCount, "Registros de alertas activas"),
    card("Municipios foco", focusCount, "Temperatura y riesgo"),
    card("Datos históricos", observations.available ? fmtInt(observations.rows) : "Pendiente", historicalDetail, observations.available ? "ok" : "warn"),
    card("Dataset PR-CARIBE", trainingTable.available ? fmtInt(trainingTable.rows) : "Pendiente", tableDetail, candidate ? "ok" : "warn"),
    card("Modelo Atlántico", modelState, `Mínimo operacional: ${fmtInt(minData.rows_operational_candidate)} filas`, modelStatus.production_validated ? "ok" : "warn"),
    card("Mobile cluster", clusterStatus, "Señales web/móvil experimentales")
  ].join("");
  if (Array.isArray(alerts) && alerts.length) renderTable(alerts);
  else if (Array.isArray(focus) && focus.length) renderTable(focus);
  else renderTable([health, desktopHealth, apiStatus, webBridge, cluster, modelStatus, readiness, trainingStatus, trainingPlan]);
  log("Panel actualizado correctamente.");
}

function updateLinks() {
  $("docsLink").href = `${apiBase()}/docs`;
  $("healthLink").href = `${apiBase()}/desktop-health`;
  $("mobileLink").href = `${apiBase()}/mobile/`;
  $("caribbeanReportMdLink").href = `${apiBase()}${paths.caribbeanAtlanticReportMarkdown || "/weather/report/caribbean-atlantic.md"}`;
}

function init() {
  $("apiBase").value = cfg.defaultApiBase || window.location.origin;
  updateLinks();
  $("apiBase").addEventListener("change", updateLinks);
  $("refreshBtn").addEventListener("click", () => refresh().catch((err) => log(`Error: ${err.message}`)));
  $("weatherReportBtn").addEventListener("click", loadWeatherReport);
  $("caribbeanReportBtn").addEventListener("click", loadCaribbeanAtlanticReport);
  $("municipalityInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadWeatherReport();
  });
  $("clearBtn").addEventListener("click", async () => {
    if ("caches" in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
    log("Cache visual limpiado. Recargue la página si todavía ve una versión vieja.");
  });
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js?v=2.6.0").catch(() => {});
  refresh().catch((err) => log(`Error inicial: ${err.message}`));
  loadWeatherReport();
  loadCaribbeanAtlanticReport();
}

document.addEventListener("DOMContentLoaded", init);
