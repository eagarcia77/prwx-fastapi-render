const $ = (id) => document.getElementById(id);
const logEl = $("log");
const stateEl = $("state");
const peakEl = $("peak");
const sentEl = $("sent");
const lastEl = $("last");

const CONFIG = window.PRWX_CONFIG || {};
let monitoring = false;
let sensorAllowed = false;
let peakG = 0;
let sent = Number(localStorage.getItem("prwx_sent_count") || "0");
let lastSent = 0;
let deferredInstallPrompt = null;

const thresholdG = 0.18;
const cooldownMs = 15000;
const G = 9.80665;

function log(msg) {
  const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.textContent = `${line}\n${logEl.textContent}`.slice(0, 7000);
}

function defaultApiBase() {
  const host = window.location.hostname;
  if (host.includes("github.io")) return CONFIG.renderApiBase || "https://prwx-fastapi-render.onrender.com";
  if (window.location.origin && window.location.origin.startsWith("http")) return window.location.origin;
  return CONFIG.renderApiBase || "https://prwx-fastapi-render.onrender.com";
}

function apiBase() {
  const typed = $("apiBase").value.trim().replace(/\/$/, "");
  return typed || defaultApiBase();
}

function endpoint(path) {
  return `${apiBase()}${path}`;
}

function requireConsent() {
  if (!$("consent").checked) {
    log("Debe aceptar consentimiento antes de enviar.");
    return false;
  }
  return true;
}

function roundedLocation(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return Math.round(n * 100) / 100;
}

async function requestSensors() {
  try {
    if (typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function") {
      const permission = await DeviceMotionEvent.requestPermission();
      sensorAllowed = permission === "granted";
      log(`Permiso de movimiento: ${permission}`);
    } else if ("DeviceMotionEvent" in window) {
      sensorAllowed = true;
      log("Sensores de movimiento disponibles en este navegador.");
    } else {
      sensorAllowed = false;
      log("Este navegador no expone DeviceMotionEvent. Puede usar Enviar prueba segura.");
    }
  } catch (err) {
    sensorAllowed = false;
    log(`No se pudo pedir permiso de sensores: ${err.message}`);
  }
}

async function requestNotifications() {
  if (!("Notification" in window)) {
    log("Este navegador no soporta notificaciones locales.");
    return;
  }
  try {
    const permission = await Notification.requestPermission();
    log(`Permiso de notificaciones: ${permission}`);
  } catch (err) {
    log(`No se pudo pedir permiso de notificaciones: ${err.message}`);
  }
}

function localNotify(title, body) {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body, requireInteraction: false });
  }
}

function useGeolocation() {
  if (!("geolocation" in navigator)) {
    log("Geolocalización no disponible.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      $("lat").value = roundedLocation(pos.coords.latitude);
      $("lon").value = roundedLocation(pos.coords.longitude);
      localStorage.setItem("prwx_lat", $("lat").value);
      localStorage.setItem("prwx_lon", $("lon").value);
      log("Ubicación aproximada actualizada.");
    },
    (err) => log(`Ubicación no concedida: ${err.message}`),
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
  );
}

function calcDynamicG(event) {
  const a = event.accelerationIncludingGravity || event.acceleration;
  if (!a || a.x == null || a.y == null || a.z == null) return 0;
  const total = Math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z);
  if (event.accelerationIncludingGravity) return Math.abs(total - G) / G;
  return total / G;
}

async function postJson(path, payload) {
  const res = await fetch(endpoint(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  let data = {};
  try { data = await res.json(); } catch (_) { data = { status: "non_json_response" }; }
  if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(data)}`);
  return data;
}

async function sendTrigger(pgaG, confidence, source = "web_sensor_bridge") {
  if (!requireConsent()) return;
  const lat = roundedLocation($("lat").value);
  const lon = roundedLocation($("lon").value);
  if (lat === null || lon === null) {
    log("Latitud y longitud aproximada son requeridas.");
    return;
  }

  const payload = {
    trigger_time_utc: new Date().toISOString(),
    coarse_lat: lat,
    coarse_lon: lon,
    pga_g: Number(pgaG.toFixed(4)),
    confidence: Number(confidence.toFixed(3)),
    source
  };

  try {
    let data;
    try {
      data = await postJson(CONFIG.triggerEndpoint || "/seismic/web-trigger", payload);
    } catch (err) {
      if (String(err.message).startsWith("404")) {
        log("/seismic/web-trigger no está disponible; intentando endpoint legado.");
        data = await postJson(CONFIG.fallbackTriggerEndpoint || "/seismic/android-trigger", payload);
      } else {
        throw err;
      }
    }
    sent += 1;
    localStorage.setItem("prwx_sent_count", String(sent));
    sentEl.textContent = sent;
    lastEl.textContent = new Date().toLocaleTimeString();
    log(`Trigger enviado. Cluster: ${data.cluster?.cluster_status || "recibido"}`);
    localNotify("PR-WX Web Bridge", "Señal experimental enviada al dashboard.");
  } catch (err) {
    log(`Error enviando trigger: ${err.message}. Verifique URL de API, CORS y que Render esté activo.`);
  }
}

function onMotion(event) {
  if (!monitoring) return;
  const dynamicG = calcDynamicG(event);
  peakG = Math.max(peakG, dynamicG);
  peakEl.textContent = peakG.toFixed(3);
  const now = Date.now();
  if (dynamicG >= thresholdG && now - lastSent > cooldownMs) {
    lastSent = now;
    const confidence = Math.min(0.95, Math.max(0.3, dynamicG / 0.45));
    sendTrigger(dynamicG, confidence, "web_sensor_bridge");
  }
}

async function toggleMonitoring() {
  if (!requireConsent()) return;
  if (!sensorAllowed) await requestSensors();
  if (!sensorAllowed) {
    log("Sensores no autorizados o no disponibles. Use Enviar prueba segura para verificar conexión.");
    return;
  }
  monitoring = !monitoring;
  if (monitoring) {
    peakG = 0;
    window.addEventListener("devicemotion", onMotion);
    stateEl.textContent = "monitoreando";
    $("startBtn").textContent = "Detener monitoreo";
    log("Monitoreo iniciado. Mantenga el teléfono seguro; no haga movimientos peligrosos.");
  } else {
    window.removeEventListener("devicemotion", onMotion);
    stateEl.textContent = "detenido";
    $("startBtn").textContent = "Iniciar monitoreo";
    log("Monitoreo detenido.");
  }
}

async function verifyApi() {
  try {
    const health = await fetch(endpoint(CONFIG.healthEndpoint || "/healthz"));
    const healthData = await health.json();
    const bridge = await fetch(endpoint(CONFIG.bridgeStatusEndpoint || "/web-bridge/status"));
    const bridgeData = await bridge.json();
    log(`API OK: ${healthData.status}; bridge ${bridgeData.version || "N/D"}; mobile folder: ${bridgeData.mobile_folder_exists}`);
  } catch (err) {
    log(`No se pudo verificar API: ${err.message}`);
  }
}

async function viewCluster() {
  try {
    const res = await fetch(endpoint(CONFIG.clusterEndpoint || "/seismic/mobile-cluster"));
    const data = await res.json();
    log(`Cluster: ${JSON.stringify(data).slice(0, 900)}`);
  } catch (err) {
    log(`No se pudo leer cluster: ${err.message}`);
  }
}

function setupInstallPrompt() {
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    log("La página puede instalarse como acceso directo.");
  });
}

async function installApp() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    const choice = await deferredInstallPrompt.userChoice;
    log(`Instalación: ${choice.outcome}`);
    deferredInstallPrompt = null;
  } else {
    log("En Android Chrome: menú ⋮ > Agregar a pantalla principal.");
  }
}

function initDefaults() {
  $("apiBase").value = localStorage.getItem("prwx_api") || defaultApiBase();
  $("lat").value = localStorage.getItem("prwx_lat") || "18.02";
  $("lon").value = localStorage.getItem("prwx_lon") || "-66.61";
  sentEl.textContent = sent;
  $("apiBase").addEventListener("change", () => localStorage.setItem("prwx_api", $("apiBase").value));
  $("lat").addEventListener("change", () => localStorage.setItem("prwx_lat", $("lat").value));
  $("lon").addEventListener("change", () => localStorage.setItem("prwx_lon", $("lon").value));
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js").catch((err) => log(`Service worker no registrado: ${err.message}`));
  setupInstallPrompt();
}

$("sensorBtn").addEventListener("click", requestSensors);
$("notifyBtn").addEventListener("click", requestNotifications);
$("geoBtn").addEventListener("click", useGeolocation);
$("startBtn").addEventListener("click", toggleMonitoring);
$("testBtn").addEventListener("click", () => sendTrigger(0.05, 0.35, "web_sensor_bridge_test"));
$("statusBtn").addEventListener("click", verifyApi);
$("clusterBtn").addEventListener("click", viewCluster);
$("installBtn").addEventListener("click", installApp);

initDefaults();
log("Página lista. En Android use Chrome con HTTPS. Presione Verificar API primero.");
