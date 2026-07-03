const $ = (id) => document.getElementById(id);
const logEl = $("log");
const stateEl = $("state");
const peakEl = $("peak");
const sentEl = $("sent");
const lastEl = $("last");

let monitoring = false;
let sensorAllowed = false;
let peakG = 0;
let sent = 0;
let lastSent = 0;
const thresholdG = 0.18;
const cooldownMs = 15000;
const G = 9.80665;

function log(msg) {
  const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.textContent = `${line}\n${logEl.textContent}`.slice(0, 5000);
}

function apiBase() {
  const typed = $("apiBase").value.trim().replace(/\/$/, "");
  return typed || window.location.origin;
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
  return Math.round(n * 100) / 100; // coarse location only
}

async function requestSensors() {
  try {
    if (typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function") {
      const permission = await DeviceMotionEvent.requestPermission();
      sensorAllowed = permission === "granted";
      log(`Permiso de movimiento: ${permission}`);
    } else {
      sensorAllowed = true;
      log("Permiso explícito no requerido por este navegador.");
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
    const res = await fetch(`${apiBase()}/seismic/web-trigger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(JSON.stringify(data));
    sent += 1;
    sentEl.textContent = sent;
    lastEl.textContent = new Date().toLocaleTimeString();
    log(`Trigger enviado. Cluster: ${data.cluster?.cluster_status || "recibido"}`);
    localNotify("PR-WX Web Bridge", "Señal experimental enviada al dashboard.");
  } catch (err) {
    log(`Error enviando trigger: ${err.message}`);
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
    log("Sensores no autorizados.");
    return;
  }
  monitoring = !monitoring;
  if (monitoring) {
    window.addEventListener("devicemotion", onMotion);
    stateEl.textContent = "monitoreando";
    $("startBtn").textContent = "Detener monitoreo";
    log("Monitoreo iniciado.");
  } else {
    window.removeEventListener("devicemotion", onMotion);
    stateEl.textContent = "detenido";
    $("startBtn").textContent = "Iniciar monitoreo";
    log("Monitoreo detenido.");
  }
}

function initDefaults() {
  $("apiBase").value = window.location.origin.startsWith("http") ? window.location.origin : "";
  $("lat").value = localStorage.getItem("prwx_lat") || "18.02";
  $("lon").value = localStorage.getItem("prwx_lon") || "-66.61";
  $("apiBase").addEventListener("change", () => localStorage.setItem("prwx_api", $("apiBase").value));
  $("lat").addEventListener("change", () => localStorage.setItem("prwx_lat", $("lat").value));
  $("lon").addEventListener("change", () => localStorage.setItem("prwx_lon", $("lon").value));
  const savedApi = localStorage.getItem("prwx_api");
  if (savedApi) $("apiBase").value = savedApi;
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js").catch(() => {});
}

$("sensorBtn").addEventListener("click", requestSensors);
$("notifyBtn").addEventListener("click", requestNotifications);
$("geoBtn").addEventListener("click", useGeolocation);
$("startBtn").addEventListener("click", toggleMonitoring);
$("testBtn").addEventListener("click", () => sendTrigger(0.05, 0.35, "web_sensor_bridge_test"));

initDefaults();
log("Página lista. Use HTTPS para sensores, ubicación y notificaciones.");
