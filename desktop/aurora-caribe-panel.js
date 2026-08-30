/* PR-WX v3.4.0 — AURORA Caribe-Atlántico model panel */
(function () {
  const VERSION = "3.4.0";
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

  function pct(value) {
    const n = Number(value);
    return Number.isFinite(n) ? `${Math.round(n)}%` : "N/D";
  }

  function layerHTML(layers) {
    if (!Array.isArray(layers) || !layers.length) return "<p class=\"note\">No hay capas registradas.</p>";
    return layers.map((layer) => `
      <div class="impactItem bajo">
        <strong>${esc(layer.name)}</strong>
        <p>${esc(layer.purpose)}</p>
        <code>${esc(layer.map)}</code>
      </div>
    `).join("");
  }

  function render(status, predictions, training) {
    const panel = $("auroraCaribePanel");
    if (!panel) return;
    const model = status.model || predictions.model || {};
    const readiness = predictions.readiness || training.readiness || {};
    const cadence = training.cadence || {};
    const available = readiness.available_inputs || {};
    const layers = (status.prediction_layers || {}).layers || [];
    const availableRows = Object.entries(available).map(([key, value]) => `
      <div class="impactItem ${value ? "bajo" : "moderado"}">
        <strong>${esc(key.replaceAll("_", " "))}</strong>
        <p>${value ? "Disponible" : "Pendiente / no encontrado"}</p>
      </div>
    `).join("");

    panel.innerHTML = `
      <div class="mapDashboardGrid">
        <div class="mapKpi"><span>Modelo</span><strong>${esc(model.model_name || "AURORA Caribe-Atlántico")}</strong></div>
        <div class="mapKpi"><span>Confianza predictiva</span><strong>${pct(predictions.prediction_confidence)}</strong></div>
        <div class="mapKpi"><span>Preparación datos</span><strong>${pct(readiness.readiness_score)}</strong></div>
      </div>
      <p><strong>Nombre del modelo:</strong> ${esc(model.full_name || "AURORA Caribe-Atlántico AI Forecast Model")}</p>
      <p><strong>Significado:</strong> ${esc(model.tagline || "Análisis Unificado de Riesgo Operacional, Radar y Atmósfera")}</p>
      <p><strong>Entrenamiento continuo:</strong> ${esc(cadence.cadence_readable_es || "cada 6 horas mediante GitHub Actions")}</p>
      <p><strong>Workflow:</strong> <code>${esc(cadence.github_action || ".github/workflows/aurora-caribe-continuous-training-v34.yml")}</code></p>
      <div class="actions">
        <a class="btn" href="https://github.com/eagarcia77/prwx-fastapi-render/actions/workflows/aurora-caribe-continuous-training-v34.yml" target="_blank" rel="noopener">Abrir entrenamiento AURORA</a>
        <a class="btn" href="${apiBase()}${route("auroraCaribeReport", "/aurora-caribe/report")}" target="_blank" rel="noopener">Ver reporte JSON</a>
      </div>
      <h3>Capas predictivas conectadas</h3>
      <div class="impactList">${layerHTML(layers)}</div>
      <h3>Disponibilidad de datos</h3>
      <div class="impactList">${availableRows}</div>
      <p class="note">AURORA-CARIBE es experimental. Sus predicciones apoyan análisis y visualización, pero los avisos oficiales deben venir de NHC, NWS San Juan y manejo de emergencias.</p>
    `;
  }

  async function loadAurora() {
    const panel = $("auroraCaribePanel");
    if (panel) panel.innerHTML = `<p class="note">Cargando AURORA Caribe-Atlántico...</p>`;
    try {
      const [status, predictions, training] = await Promise.all([
        getJSON(route("auroraCaribeStatus", "/aurora-caribe/status")),
        getJSON(route("auroraCaribePredictions", "/aurora-caribe/predictions/summary")),
        getJSON(route("auroraCaribeTrainingStatus", "/aurora-caribe/training/status")),
      ]);
      render(status, predictions, training);
    } catch (err) {
      if (panel) panel.innerHTML = `<p class="note">No se pudo cargar AURORA-CARIBE: ${esc(err.message)}</p>`;
    }
  }

  function bind() {
    const btn = $("auroraRefreshBtn");
    if (btn) btn.addEventListener("click", loadAurora);
    setTimeout(loadAurora, 900);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();

  window.PRWX_AURORA_CARIBE = { version: VERSION, refresh: loadAurora };
})();
