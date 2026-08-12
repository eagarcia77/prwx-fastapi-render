window.PRWX_CONFIG = {
  version: "2.5.0",
  renderApiBase: "https://prwx-fastapi-render.onrender.com",
  defaultApiBase: window.location.hostname.includes("github.io")
    ? "https://prwx-fastapi-render.onrender.com"
    : window.location.origin,
  paths: {
    health: "/healthz",
    desktopHealth: "/desktop-health",
    apiStatus: "/api/status",
    webBridge: "/web-bridge/status",
    predictions: "/predictions",
    alerts: "/alerts/active",
    temperatureFocus: "/temperature/focus",
    mobileCluster: "/seismic/mobile-cluster",
    caribbeanModelStatus: "/caribbean/model/status",
    caribbeanModelReadiness: "/caribbean/model/readiness",
    caribbeanModelSources: "/caribbean/model/sources",
    weatherReport: "/weather/report/{municipality}"
  }
};
