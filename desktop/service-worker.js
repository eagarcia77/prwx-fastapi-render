const CACHE = "prwx-desktop-v390-live-rain-impact-ready";
const ASSETS = ["./", "./index.html", "./live-rain.html", "./styles.css", "./storm-cinematic.css", "./map-enhancements-v33.css", "./dust-layer-v35.css", "./aurora-3d.css", "./live-rain-v37.css", "./live-rain-v38.css", "./live-rain-v39.css", "./app.js", "./api-config.js", "./aurora-caribe-panel.js", "./aurora-dust-panel.js", "./aurora-3d-command-center.js", "./live-rain-map.js", "./live-rain-v38.js", "./live-rain-v39.js", "./real-map.js", "./storm-map.js", "./storm-history-panel.js", "./manifest.webmanifest"];
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/healthz") || url.pathname.startsWith("/readyz") || url.pathname.startsWith("/api/") || url.pathname.startsWith("/ai/") || url.pathname.startsWith("/aurora-caribe/") || url.pathname.startsWith("/rain/live/") || url.pathname.includes("/desktop-health") || url.pathname.includes("/web-bridge/") || url.pathname.includes("/seismic/") || url.pathname.includes("/alerts/") || url.pathname.includes("/temperature/") || url.pathname.includes("/services/") || url.pathname.includes("/weather/report/") || url.pathname.includes("/caribbean/")) return;
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
