const $ = (id) => document.getElementById(id);
const cfg = window.PRWX_CONFIG || {};
const paths = cfg.paths || {};
let lastMapPayload = null;

function log(message) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  $("log").textContent = `${line}\n${$("log").textContent}`.slice(0, 8000);
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
  const priority = ["municipality", "risk_level", "risk_score", "temp_f", "feels_like_f", "rain_in", "wind_mph", "headline", "severity", "cluster_status", "rows", "research_ready", "operational_candidate"];
  const columns = [...priority.filter((c) => c in rows[0]), ...Object.keys(rows[0]).filter((c) => !priority.includes(c))].slice(0, 9);
  thead.innerHTML = `<tr>${columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr>`;
  tbody.innerHTML = rows.slice(0, 20).map((r) => `<tr>${columns.map((c) => `<td>${esc(r[c] ?? "")}</td>`).join("")}</tr>`).join("");
}

function riskClass(level) {
  const key = String(level || "").toLowerCase();
  if (key.includes("alto")) return "riskHigh";
  if (key.includes("moderado")) return "riskModerate";
  return "riskLow";
}

function riskCardClass(level) {
  const key = String(level || "").toLowerCase();
  if (key.includes("alto")) return "bad";
  if (key.includes("moderado")) return "warn";
  return "ok";
}

function projectPoint(lon, lat) {
  const minLon = -67.35, maxLon = -65.20, minLat = 17.86, maxLat = 18.54;
  const x = 60 + ((lon - minLon) / (maxLon - minLon)) * 880;
  const y = 320 - ((lat - minLat) / (maxLat - minLat)) * 260;
  return [Math.max(20, Math.min(980, x)), Math.max(30, Math.min(340, y))];
}

function renderMapDetails(feature) {
  const target = $("mapDetails");
  if (!feature || !feature.properties) {
    target.innerHTML = `<p class="note">Seleccione un pueblo en el mapa para ver el análisis IA.</p>`;
    return;
  }
  const p = feature.properties;
  const c = p.conditions || {};
  const alerts = Array.isArray(p.alerts) ? p.alerts : [];
  target.innerHTML = `
    <h3>${esc(p.municipality)}</h3>
    <p><span class="riskPill ${esc(p.risk_level)}">${esc(p.risk_level || "N/D")}</span></p>
    <div class="municipalityMeta">
      <div><strong>Riesgo IA</strong><br>${fmtInt(p.risk_score)}/100</div>
      <div><strong>Confianza</strong><br>${esc(p.confidence || "N/D")}</div>
      <div><strong>Región</strong><br>${esc(p.region || "N/D")}</div>
      <div><strong>Alertas</strong><br>${fmtInt(p.alert_count)}</div>
      <div><strong>Sensación</strong><br>${fmt(c.feels_like_f)} °F</div>
      <div><strong>Lluvia 24h</strong><br>${fmt(c.rain_24h_in, 2)} in</div>
      <div><strong>Viento</strong><br>${fmt(c.wind_mph)} mph</div>
      <div><strong>Ráfaga</strong><br>${fmt(c.gust_mph)} mph</div>
    </div>
    <p><strong>Análisis IA:</strong> ${esc(p.ai_analysis || "")}</p>
    <p><strong>Recomendación:</strong> ${esc(p.recommended_action || "")}</p>
    <p class="note">Datos: ${esc(p.data_status || "")}. ${alerts.length ? "Hay alertas asociadas; verifique la fuente oficial." : "No hay alertas asociadas en el dataset local."}</p>
  `;
}

function selectMapMunicipality(name) {
  const select = $("mapMunicipalitySelect");
  if (select) select.value = name;
  if (!lastMapPayload) return;
  const feature = lastMapPayload.features.find((f) => f.properties.municipality === name);
  renderMapDetails(feature);
}

function renderInteractiveMap(payload) {
  lastMapPayload = payload;
  const canvas = $("aiMapCanvas");
  const select = $("mapMunicipalitySelect");
  const features = Array.isArray(payload?.features) ? payload.features : [];
  if (!features.length) {
    canvas.innerHTML = `<p class="note">No hay datos de mapa disponibles.</p>`;
    return;
  }
  select.innerHTML = features.map((f) => `<option value="${esc(f.properties.municipality)}">${esc(f.properties.municipality)}</option>`).join("");
  const markers = features.map((f) => {
    const [lon, lat] = f.geometry.coordinates;
    const [x, y] = projectPoint(lon, lat);
    const p = f.properties;
    const radius = 5 + Math.min(10, Number(p.risk_score || 0) / 12);
    const cls = riskClass(p.risk_level);
    const label = p.risk_score >= 70 || ["San Juan", "Ponce", "Mayagüez", "Caguas", "Arecibo", "Juana Díaz", "San Germán"].includes(p.municipality)
      ? `<text class="mapLabel" x="${x + 8}" y="${y - 8}">${esc(p.municipality)}</text>` : "";
    return `<g tabindex="0" role="button" aria-label="${esc(p.municipality)} riesgo ${esc(p.risk_level)}" data-municipality="${esc(p.municipality)}">
      <circle class="mapMarker ${cls}" cx="${x}" cy="${y}" r="${radius}"><title>${esc(p.municipality)} · ${esc(p.risk_level)} · ${fmtInt(p.risk_score)}/100</title></circle>${label}
    </g>`;
  }).join("");
  canvas.innerHTML = `
    <svg class="prMap" viewBox="0 0 1000 360" preserveAspectRatio="xMidYMid meet" aria-labelledby="mapTitle mapDesc">
      <title id="mapTitle">Mapa IA experimental de Puerto Rico</title>
      <desc id="mapDesc">Marcadores municipales por riesgo IA; los puntos son centroides aproximados.</desc>
      <rect x="0" y="0" width="1000" height="360" fill="#dbeafe"></rect>
      <path class="mapIsland" d="M52,160 C120,98 255,68 410,72 C578,76 705,98 815,126 C890,146 936,176 920,211 C899,255 789,272 650,276 C478,282 324,270 188,243 C85,222 20,198 52,160 Z"></path>
      <ellipse class="mapIsland" cx="872" cy="242" rx="58" ry="18"></ellipse>
      <ellipse class="mapIsland" cx="940" cy="153" rx="26" ry="13"></ellipse>
      ${markers}
    </svg>`;
  canvas.querySelectorAll("[data-municipality]").forEach((node) => {
    node.addEventListener("click", () => selectMapMunicipality(node.dataset.municipality));
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") selectMapMunicipality(node.dataset.municipality);
    });
  });
  const priority = features.find((f) => f.properties.municipality === select.value) || features.find((f) => f.properties.municipality === "San Juan") || features[0];
  select.value = priority.properties.municipality;
  renderMapDetails(priority);
  log(`Mapa IA cargado con ${features.length} municipios.`);
}

async function loadAIMap() {
  const canvas = $("aiMapCanvas");
  if (canvas) canvas.innerHTML = `<p class="note">Cargando mapa IA municipal...</p>`;
  try {
    const payload = await getJSON(paths.aiMapsPR || "/ai/maps/pr-municipalities");
    renderInteractiveMap(payload);
  } catch (err) {
    if (canvas) canvas.innerHTML = `<p class="note">No se pudo cargar el mapa IA: ${esc(err.message)}</p>`;
    log(`Error mapa IA: ${err.message}`);
  }
}

async function loadSelectedMunicipalityMapAnalysis() {
  const name = $("mapMunicipalitySelect").value;
  if (!name) return;
  const template = paths.aiMapsMunicipality || "/ai/maps/municipality/{municipality}";
  try {
    const feature = await getJSON(template.replace("{municipality}", encodeURIComponent(name)));
    renderMapDetails(feature);
    log(`Análisis IA municipal cargado: ${name}.`);
  } catch (err) {
    log(`Error análisis municipal: ${err.message}`);
  }
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
    <p class="note">${esc(report.disclaimer || "")}</p>`;
}

function renderAITrainingPanel(aiStatus, aiAnalysis, aiTrainStatus) {
  const target = $("aiTrainingPanel");
  if (!target) return;
  if (!aiStatus || aiStatus.error) {
    target.innerHTML = `<p class="note">No se pudo cargar el módulo IA: ${esc(aiStatus?.error || "sin datos")}</p>`;
    return;
  }
  const readiness = aiAnalysis?.readiness || aiStatus.readiness || {};
  const train = aiTrainStatus || {};
  const readyClass = readiness.operational_candidate ? "ok" : (readiness.research_ready ? "warn" : "bad");
  target.innerHTML = `
    <div class="grid">
      ${card("Motor IA", aiStatus.version || "2.8.0", aiStatus.engine || "PR-WX AI Trainer")}
      ${card("Filas", fmtInt(readiness.rows), `${fmtInt(readiness.columns)} columnas · ${fmtInt(readiness.usable_features)} variables útiles`, readyClass)}
      ${card("Cobertura", `${fmtInt(readiness.span_days)} días`, `${fmtInt(readiness.stations)} puntos · ${fmtInt(readiness.territories)} territorios`, readyClass)}
      ${card("Objetivos", fmtInt(readiness.trainable_targets), "temperatura · lluvia · viento · humedad · presión", readyClass)}
      ${card("Entrenamiento", train.status || aiStatus.training_status || "not_trained", train.model_file_exists ? "modelo disponible" : "modelo pendiente", train.model_file_exists ? "ok" : "warn")}
      ${card("Producción", aiStatus.production_validated ? "validado" : "no validado", "requiere revisión meteorológica independiente", aiStatus.production_validated ? "ok" : "warn")}
    </div>
    <p><strong>Recomendación IA:</strong> ${esc(readiness.recommendation || "Completar el dataset histórico antes del entrenamiento operacional.")}</p>
    <p class="note">El entrenamiento desde Render está ${aiStatus.runtime_training_enabled ? "activo" : "desactivado"}. Recomendado: entrenar con el script local y luego subir el modelo validado.</p>`;
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
    <ul>${matrix.map((item) => `<li><strong>${esc(item.domain)}</strong>: ${esc((item.sources || []).join(", "))}. ${esc(item.training_role || "")}</li>`).join("")}</ul>
    <p class="note">${esc(report.disclaimer || "")}</p>`;
}

async function loadWeatherReport() {
  const municipality = ($("municipalityInput").value || "").trim();
  if (!municipality) { $("weatherReport").innerHTML = `<p class="note">Escriba un municipio.</p>`; return; }
  $("weatherReport").innerHTML = `<p class="note">Generando informe para ${esc(municipality)}...</p>`;
  const template = paths.weatherReport || "/weather/report/{municipality}";
  try {
    const report = await getJSON(template.replace("{municipality}", encodeURIComponent(municipality)));
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

async function loadAITrainingPanel(runAnalysis = false) {
  const panel = $("aiTrainingPanel");
  if (panel) panel.innerHTML = `<p class="note">Analizando datos con IA...</p>`;
  try {
    const statusPath = paths.aiModelStatus || "/ai/model/status";
    const analysisPath = runAnalysis ? (paths.aiModelAnalyze || "/ai/model/analyze") : (paths.aiModelReport || "/ai/model/report");
    const trainPath = paths.aiTrainStatus || "/ai/model/train-status";
    const [status, analysisOrReport, trainStatus] = await Promise.all([getJSON(statusPath), getJSON(analysisPath), getJSON(trainPath)]);
    renderAITrainingPanel(status, analysisOrReport.analysis || analysisOrReport, trainStatus);
    log(runAnalysis ? "Análisis IA ejecutado y guardado." : "Estado IA cargado.");
  } catch (err) {
    renderAITrainingPanel({ error: err.message });
    log(`Error IA: ${err.message}`);
  }
}

async function refresh() {
  const cards = $("cards");
  cards.innerHTML = card("Estado", "Cargando", "Consultando Render...", "warn");
  log(`API: ${apiBase()}`);
  const results = await Promise.allSettled([
    getJSON(paths.health || "/healthz"), getJSON(paths.desktopHealth || "/desktop-health"), getJSON(paths.apiStatus || "/api/status"),
    getJSON(paths.webBridge || "/web-bridge/status"), getJSON(paths.alerts || "/alerts/active"), getJSON(paths.temperatureFocus || "/temperature/focus"),
    getJSON(paths.mobileCluster || "/seismic/mobile-cluster"), getJSON(paths.aiModelStatus || "/ai/model/status"), getJSON(paths.aiModelReport || "/ai/model/report"),
    getJSON(paths.aiMapsSummary || "/ai/maps/summary"), getJSON(paths.caribbeanModelStatus || "/caribbean/model/status"),
    getJSON(paths.caribbeanModelReadiness || "/caribbean/model/readiness"), getJSON(paths.caribbeanTrainingStatus || "/caribbean/training/status"), getJSON(paths.caribbeanTrainingPlan || "/caribbean/model/training-plan")
  ]);
  const [health, desktopHealth, apiStatus, webBridge, alerts, focus, cluster, aiStatus, aiReport, mapSummary, modelStatus, readiness, trainingStatus, trainingPlan] = results.map((r) => r.status === "fulfilled" ? r.value : { error: r.reason.message });
  const alertsCount = Array.isArray(alerts) ? alerts.length : 0;
  const focusCount = Array.isArray(focus) ? focus.length : 0;
  const clusterStatus = cluster.cluster_status || cluster.status || "sin cluster";
  const modelState = modelStatus.status || "training_required";
  const observations = trainingStatus.observations || {};
  const trainingTable = trainingStatus.training_table || {};
  const minData = trainingPlan.minimum_real_training_dataset || {};
  const aiReadiness = aiReport.analysis?.readiness || aiStatus.readiness || {};
  const aiState = aiStatus.training_status || "not_trained";
  cards.innerHTML = [
    card("API", health.status || "error", health.service || health.error || "healthz"),
    card("Desktop", desktopHealth.status || "error", `index: ${desktopHealth.desktop_index_exists === true}`),
    card("Versión", apiStatus.version || webBridge.version || cfg.version || "N/D", "Render + GitHub"),
    card("Mapa IA", fmtInt(mapSummary.municipalities), `${fmtInt(mapSummary.high_risk)} alto · ${fmtInt(mapSummary.moderate_risk)} moderado`, mapSummary.high_risk ? "bad" : (mapSummary.moderate_risk ? "warn" : "ok")),
    card("Alertas", alertsCount, "Registros de alertas activas"),
    card("Municipios foco", focusCount, "Temperatura y riesgo"),
    card("IA Dataset", fmtInt(aiReadiness.rows), `${fmtInt(aiReadiness.usable_features)} variables · ${fmtInt(aiReadiness.trainable_targets)} objetivos`, aiReadiness.research_ready ? "ok" : "warn"),
    card("IA Training", aiState, aiStatus.runtime_training_enabled ? "runtime activo" : "runtime protegido", aiState.includes("trained") ? "ok" : "warn"),
    card("Datos históricos", observations.available ? fmtInt(observations.rows) : "Pendiente", observations.available ? `${fmtInt(observations.stations)} estaciones` : "Backfill histórico pendiente", observations.available ? "ok" : "warn"),
    card("Dataset PR-CARIBE", trainingTable.available ? fmtInt(trainingTable.rows) : "Pendiente", trainingTable.available ? "filas ensambladas" : "tabla pendiente", readiness.operational_candidate ? "ok" : "warn"),
    card("Modelo Atlántico", modelState, `Mínimo operacional: ${fmtInt(minData.rows_operational_candidate)} filas`, modelStatus.production_validated ? "ok" : "warn"),
    card("Mobile cluster", clusterStatus, "Señales web/móvil experimentales")
  ].join("");
  renderAITrainingPanel(aiStatus, aiReport.analysis, aiReport.training);
  if (Array.isArray(alerts) && alerts.length) renderTable(alerts);
  else if (Array.isArray(focus) && focus.length) renderTable(focus);
  else renderTable([health, desktopHealth, apiStatus, webBridge, cluster, mapSummary, aiStatus, aiReadiness, modelStatus, readiness, trainingStatus, trainingPlan]);
  log("Panel actualizado correctamente.");
}

function updateLinks() {
  $("docsLink").href = `${apiBase()}/docs`;
  $("healthLink").href = `${apiBase()}/desktop-health`;
  $("mobileLink").href = `${apiBase()}/mobile/`;
  $("caribbeanReportMdLink").href = `${apiBase()}${paths.caribbeanAtlanticReportMarkdown || "/weather/report/caribbean-atlantic.md"}`;
  $("aiMapGeoJsonLink").href = `${apiBase()}${paths.aiMapsGeoJSON || "/ai/maps/pr-municipalities.geojson"}`;
  const aiPlan = $("aiPlanMdLink");
  if (aiPlan) aiPlan.href = `${apiBase()}${paths.aiTrainingPlanMarkdown || "/ai/model/training-plan.md"}`;
}

function init() {
  $("apiBase").value = cfg.defaultApiBase || window.location.origin;
  updateLinks();
  $("apiBase").addEventListener("change", updateLinks);
  $("refreshBtn").addEventListener("click", () => refresh().catch((err) => log(`Error: ${err.message}`)));
  $("weatherReportBtn").addEventListener("click", loadWeatherReport);
  $("caribbeanReportBtn").addEventListener("click", loadCaribbeanAtlanticReport);
  $("aiAnalyzeBtn").addEventListener("click", () => loadAITrainingPanel(true));
  $("aiMapRefreshBtn").addEventListener("click", loadAIMap);
  $("mapMunicipalityBtn").addEventListener("click", loadSelectedMunicipalityMapAnalysis);
  $("mapMunicipalitySelect").addEventListener("change", loadSelectedMunicipalityMapAnalysis);
  $("municipalityInput").addEventListener("keydown", (event) => { if (event.key === "Enter") loadWeatherReport(); });
  $("clearBtn").addEventListener("click", async () => {
    if ("caches" in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
    log("Cache visual limpiado. Recargue la página si todavía ve una versión vieja.");
  });
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js?v=2.8.0").catch(() => {});
  refresh().catch((err) => log(`Error inicial: ${err.message}`));
  loadAIMap();
  loadWeatherReport();
  loadCaribbeanAtlanticReport();
  loadAITrainingPanel();
}

document.addEventListener("DOMContentLoaded", init);
