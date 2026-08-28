/* PR-WX v3.0.0 - Historical storm data readiness panel. */
(function () {
  const VERSION = "3.0.0";
  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
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

  function fmtInt(value) {
    const n = Number(value);
    return Number.isFinite(n) ? Math.round(n).toLocaleString("es-PR") : "0";
  }

  function smallCard(title, value, detail, cls = "ok") {
    return `<article class="card metric ${cls}"><span>${esc(title)}</span><strong>${esc(value)}</strong><p>${esc(detail || "")}</p></article>`;
  }

  function render(status, model, plan) {
    const panel = $("stormHistoricalPanel");
    if (!panel) return;
    const readiness = status.readiness || {};
    const modelMeta = model.metadata || {};
    const cls = readiness.operational_candidate ? "ok" : (readiness.research_ready ? "warn" : "bad");
    const sources = Array.isArray(status.sources) ? status.sources : [];
    panel.innerHTML = `
      <div class="grid">
        ${smallCard("Datos históricos", status.training_table_exists ? "Disponible" : "Pendiente", `Tabla: ${esc(status.training_table || "sin tabla")}`, status.training_table_exists ? "ok" : "warn")}
        ${smallCard("Filas", fmtInt(readiness.rows), `${fmtInt(readiness.storms)} sistemas · ${fmtInt(readiness.years)} años`, cls)}
        ${smallCard("Casos cerca de PR", fmtInt(readiness.approach_500km_cases), `${fmtInt(readiness.direct_150km_cases)} casos directos ≤150 km`, cls)}
        ${smallCard("Modelo IA", model.model_file_exists ? "Entrenado" : "Pendiente", modelMeta.status || "sin entrenamiento", model.model_file_exists ? "ok" : "warn")}
      </div>
      <h3>Fuentes históricas preparadas</h3>
      <ul>
        ${sources.map((s) => `<li><strong>${esc(s.name)}</strong> — ${esc(s.agency)}. ${esc(s.role)}</li>`).join("")}
      </ul>
      <h3>Comandos para completar el entrenamiento</h3>
      <pre>${esc(JSON.stringify((plan && plan.commands) || {}, null, 2))}</pre>
      <p class="note">${esc(readiness.note || "Producto experimental. Validar con NHC/NWS antes de uso operacional.")}</p>
    `;
  }

  async function loadHistoricalPanel() {
    const panel = $("stormHistoricalPanel");
    if (panel) panel.innerHTML = `<p class="note">Consultando datos históricos de tormentas...</p>`;
    try {
      const [status, model, plan] = await Promise.all([
        getJSON(paths.stormHistoricalStatus || "/ai/storm-tracks/historical/status"),
        getJSON(paths.stormHistoricalModelStatus || "/ai/storm-tracks/historical/model-status"),
        getJSON(paths.stormHistoricalDownloadPlan || "/ai/storm-tracks/historical/download-plan")
      ]);
      render(status, model, plan);
      const link = $("stormHistoricalPlanLink");
      if (link) link.href = `${apiBase()}${paths.stormHistoricalDownloadPlan || "/ai/storm-tracks/historical/download-plan"}`;
    } catch (err) {
      if (panel) panel.innerHTML = `<p class="note">No se pudo cargar datos históricos: ${esc(err.message)}</p>`;
    }
  }

  function init() {
    const btn = $("stormHistoricalRefreshBtn");
    if (btn) btn.addEventListener("click", loadHistoricalPanel);
    const api = $("apiBase");
    if (api) api.addEventListener("change", loadHistoricalPanel);
    loadHistoricalPanel();
  }

  document.addEventListener("DOMContentLoaded", init);
  window.PRWX_STORM_HISTORY_PANEL_VERSION = VERSION;
})();
