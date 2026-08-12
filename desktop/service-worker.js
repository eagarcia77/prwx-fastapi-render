const CACHE = "prwx-desktop-v241";
const ASSETS = ["./", "./index.html", "./styles.css", "./app.js", "./api-config.js", "./manifest.webmanifest"];
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
  if (url.pathname.startsWith("/healthz") || url.pathname.startsWith("/readyz") || url.pathname.startsWith("/api/") || url.pathname.includes("/desktop-health") || url.pathname.includes("/web-bridge/") || url.pathname.includes("/seismic/") || url.pathname.includes("/alerts/") || url.pathname.includes("/temperature/") || url.pathname.includes("/services/")) return;
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
