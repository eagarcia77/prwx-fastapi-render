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

function card(title, value, detail, cls = "ok") {
  return `<article class="card metric ${cls}"><span>${title}</span><strong>${value}</strong><p>${detail || ""}</p></article>`;
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
  thead.innerHTML = `<tr>${columns.map((c) => `<th>${c}</th>`).join("")}</tr>`;
  tbody.innerHTML = rows.slice(0, 20).map((r) => `<tr>${columns.map((c) => `<td>${r[c] ?? ""}</td>`).join("")}</tr>`).join("");
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
    getJSON(paths.mobileCluster || "/seismic/mobile-cluster")
  ]);
  const [health, desktopHealth, apiStatus, webBridge, alerts, focus, cluster] = results.map((r) => r.status === "fulfilled" ? r.value : { error: r.reason.message });
  const alertsCount = Array.isArray(alerts) ? alerts.length : 0;
  const focusCount = Array.isArray(focus) ? focus.length : 0;
  const clusterStatus = cluster.cluster_status || cluster.status || "sin cluster";
  cards.innerHTML = [
    card("API", health.status || "error", health.service || health.error || "healthz"),
    card("Desktop", desktopHealth.status || "error", `index: ${desktopHealth.desktop_index_exists === true}`),
    card("Versión", apiStatus.version || webBridge.version || cfg.version || "N/D", "Render + GitHub"),
    card("Alertas", alertsCount, "Registros de alertas activas"),
    card("Municipios foco", focusCount, "Temperatura y riesgo"),
    card("Mobile cluster", clusterStatus, "Señales web/móvil experimentales")
  ].join("");
  if (Array.isArray(alerts) && alerts.length) renderTable(alerts);
  else if (Array.isArray(focus) && focus.length) renderTable(focus);
  else renderTable([health, desktopHealth, apiStatus, webBridge, cluster]);
  log("Panel actualizado correctamente.");
}

function init() {
  $("apiBase").value = cfg.defaultApiBase || window.location.origin;
  $("docsLink").href = `${apiBase()}/docs`;
  $("healthLink").href = `${apiBase()}/desktop-health`;
  $("mobileLink").href = `${apiBase()}/mobile/`;
  $("apiBase").addEventListener("change", () => {
    $("docsLink").href = `${apiBase()}/docs`;
    $("healthLink").href = `${apiBase()}/desktop-health`;
    $("mobileLink").href = `${apiBase()}/mobile/`;
  });
  $("refreshBtn").addEventListener("click", () => refresh().catch((err) => log(`Error: ${err.message}`)));
  $("clearBtn").addEventListener("click", async () => {
    if ("caches" in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
    log("Cache visual limpiado. Recargue la página si todavía ve una versión vieja.");
  });
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js?v=2.4.1").catch(() => {});
  refresh().catch((err) => log(`Error inicial: ${err.message}`));
}

document.addEventListener("DOMContentLoaded", init);
