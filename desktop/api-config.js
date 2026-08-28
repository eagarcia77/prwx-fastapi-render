window.PRWX_CONFIG = {
  version: "2.7.0",
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
    aiModelStatus: "/ai/model/status",
    aiModelAnalyze: "/ai/model/analyze",
    aiTrainingPlan: "/ai/model/training-plan",
    aiTrainingPlanMarkdown: "/ai/model/training-plan.md",
    aiFeatureMatrix: "/ai/model/feature-matrix",
    aiTrainStatus: "/ai/model/train-status",
    aiModelReport: "/ai/model/report",
    caribbeanModelStatus: "/caribbean/model/status",
    caribbeanModelReadiness: "/caribbean/model/readiness",
    caribbeanModelSources: "/caribbean/model/sources",
    caribbeanTrainingStatus: "/caribbean/training/status",
    caribbeanTrainingPlan: "/caribbean/model/training-plan",
    caribbeanFeatureMatrix: "/caribbean/model/feature-matrix",
    caribbeanAtlanticReport: "/weather/report/caribbean-atlantic",
    caribbeanAtlanticReportMarkdown: "/weather/report/caribbean-atlantic.md",
    weatherReport: "/weather/report/{municipality}"
  }
};
