from __future__ import annotations

import os
from pathlib import Path

from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from api.app import ROOT, app, utc_now_iso
from api.ai_storm_historical_router import router as ai_storm_historical_router
from api.ai_storm_tracks_router import router as ai_storm_tracks_router
from api.ai_maps_router import router as ai_maps_router
from api.ai_training_router import router as ai_training_router
from api.meteorological_report_router import router as meteorological_report_router
from api.caribbean_router import router as caribbean_router

VERSION = "3.0.0"
DESKTOP_CLIENT = ROOT / "desktop"
MOBILE_CLIENT = ROOT / "mobile"


def _public_render_url() -> str:
    return os.getenv("PRWX_PUBLIC_RENDER_URL", "https://prwx-fastapi-render.onrender.com").rstrip("/")


def _route_exists(path: str) -> bool:
    return any(getattr(route, "path", None) == path for route in app.router.routes)


def _ensure_router(router, state_flag: str, paths_attr: str) -> None:
    expected = [getattr(route, "path", None) for route in router.routes]
    if not getattr(app.state, state_flag, False):
        app.include_router(router)
    for route in router.routes:
        path = getattr(route, "path", None)
        if path and not _route_exists(path):
            app.router.routes.append(route)
    missing = [path for path in expected if path and not _route_exists(path)]
    if missing:
        raise RuntimeError(f"PR-WX routes were not registered: {missing}")
    setattr(app.state, state_flag, True)
    setattr(app.state, paths_attr, expected)


def _root_desktop_redirect():
    return RedirectResponse(url="/desktop/")


# Register exact report, AI, municipal maps, storm map and historical-data routes
# before the municipal wildcard route /weather/report/{municipality}.
_ensure_router(meteorological_report_router, "meteorological_report_router_installed", "meteorological_report_router_paths")
_ensure_router(ai_training_router, "ai_training_router_installed", "ai_training_router_paths")
_ensure_router(ai_maps_router, "ai_maps_router_installed", "ai_maps_router_paths")
_ensure_router(ai_storm_tracks_router, "ai_storm_tracks_router_installed", "ai_storm_tracks_router_paths")
_ensure_router(ai_storm_historical_router, "ai_storm_historical_router_installed", "ai_storm_historical_router_paths")
_ensure_router(caribbean_router, "caribbean_router_installed", "caribbean_router_paths")

if not getattr(app.state, "desktop_wrapper_installed", False):
    app.router.routes.insert(
        0,
        APIRoute(
            "/",
            _root_desktop_redirect,
            methods=["GET"],
            include_in_schema=False,
            name="root_desktop_redirect",
        ),
    )
    app.state.desktop_wrapper_installed = True


@app.get("/api/status")
def api_status():
    return {
        "name": "PR-WX Desktop + Mobile Web Service",
        "version": VERSION,
        "status": "experimental",
        "timestamp_utc": utc_now_iso(),
        "desktop_web": "/desktop/",
        "mobile_web": "/mobile/",
        "desktop_health": "/desktop-health",
        "web_bridge_status": "/web-bridge/status",
        "api_docs": "/docs",
        "ai_model_status": "/ai/model/status",
        "ai_model_analyze": "/ai/model/analyze",
        "ai_training_plan": "/ai/model/training-plan",
        "ai_training_plan_markdown": "/ai/model/training-plan.md",
        "ai_feature_matrix": "/ai/model/feature-matrix",
        "ai_train_status": "/ai/model/train-status",
        "ai_model_report": "/ai/model/report",
        "ai_maps_status": "/ai/maps/status",
        "ai_maps_layers": "/ai/maps/layers",
        "ai_maps_summary": "/ai/maps/summary",
        "ai_maps_pr_municipalities": "/ai/maps/pr-municipalities",
        "ai_maps_geojson": "/ai/maps/pr-municipalities.geojson",
        "ai_maps_municipality": "/ai/maps/municipality/{municipality}",
        "ai_storm_tracks_status": "/ai/storm-tracks/status",
        "ai_storm_tracks_analysis": "/ai/storm-tracks/analysis",
        "ai_storm_tracks_map": "/ai/storm-tracks/map",
        "ai_storm_tracks_geojson": "/ai/storm-tracks/map.geojson",
        "ai_storm_tracks_training_status": "/ai/storm-tracks/training/status",
        "ai_storm_tracks_training_plan": "/ai/storm-tracks/training/plan",
        "ai_storm_historical_sources": "/ai/storm-tracks/historical/sources",
        "ai_storm_historical_status": "/ai/storm-tracks/historical/status",
        "ai_storm_historical_readiness": "/ai/storm-tracks/historical/readiness",
        "ai_storm_historical_schema": "/ai/storm-tracks/historical/schema",
        "ai_storm_historical_model_status": "/ai/storm-tracks/historical/model-status",
        "ai_storm_historical_download_plan": "/ai/storm-tracks/historical/download-plan",
        "caribbean_model_status": "/caribbean/model/status",
        "caribbean_model_sources": "/caribbean/model/sources",
        "caribbean_model_readiness": "/caribbean/model/readiness",
        "caribbean_training_status": "/caribbean/training/status",
        "caribbean_training_plan": "/caribbean/model/training-plan",
        "caribbean_feature_matrix": "/caribbean/model/feature-matrix",
        "weather_report_example": "/weather/report/San Juan",
        "caribbean_atlantic_report": "/weather/report/caribbean-atlantic",
        "caribbean_atlantic_report_markdown": "/weather/report/caribbean-atlantic.md",
        "render_url": _public_render_url(),
        "note": "Experimental operational dashboard. Official storm tracks and public warnings must come from NOAA/NWS/NHC and emergency-management agencies.",
    }


@app.get("/desktop-health")
def desktop_health():
    return {
        "status": "ok" if (DESKTOP_CLIENT / "index.html").exists() else "missing_desktop_index",
        "version": VERSION,
        "desktop_folder_exists": DESKTOP_CLIENT.exists(),
        "desktop_index_exists": (DESKTOP_CLIENT / "index.html").exists(),
        "desktop_app_js_exists": (DESKTOP_CLIENT / "app.js").exists(),
        "desktop_config_exists": (DESKTOP_CLIENT / "api-config.js").exists(),
        "desktop_real_map_exists": (DESKTOP_CLIENT / "real-map.js").exists(),
        "desktop_storm_map_exists": (DESKTOP_CLIENT / "storm-map.js").exists(),
        "desktop_storm_history_panel_exists": (DESKTOP_CLIENT / "storm-history-panel.js").exists(),
        "mobile_folder_exists": MOBILE_CLIENT.exists(),
        "mobile_index_exists": (MOBILE_CLIENT / "index.html").exists(),
        "caribbean_router_installed": bool(getattr(app.state, "caribbean_router_installed", False)),
        "meteorological_report_router_installed": bool(getattr(app.state, "meteorological_report_router_installed", False)),
        "ai_training_router_installed": bool(getattr(app.state, "ai_training_router_installed", False)),
        "ai_maps_router_installed": bool(getattr(app.state, "ai_maps_router_installed", False)),
        "ai_storm_tracks_router_installed": bool(getattr(app.state, "ai_storm_tracks_router_installed", False)),
        "ai_storm_historical_router_installed": bool(getattr(app.state, "ai_storm_historical_router_installed", False)),
        "root_redirects_to": "/desktop/",
    }


@app.get("/desktop/config.json")
def desktop_config_json():
    return {
        "version": VERSION,
        "default_api_base": _public_render_url(),
        "health_endpoint": "/healthz",
        "status_endpoint": "/api/status",
        "predictions_endpoint": "/predictions",
        "alerts_endpoint": "/alerts/active",
        "temperature_endpoint": "/temperature/focus",
        "mobile_cluster_endpoint": "/seismic/mobile-cluster",
        "ai_model_status_endpoint": "/ai/model/status",
        "ai_model_analyze_endpoint": "/ai/model/analyze",
        "ai_training_plan_endpoint": "/ai/model/training-plan",
        "ai_training_plan_markdown_endpoint": "/ai/model/training-plan.md",
        "ai_feature_matrix_endpoint": "/ai/model/feature-matrix",
        "ai_train_status_endpoint": "/ai/model/train-status",
        "ai_maps_status_endpoint": "/ai/maps/status",
        "ai_maps_pr_endpoint": "/ai/maps/pr-municipalities",
        "ai_maps_geojson_endpoint": "/ai/maps/pr-municipalities.geojson",
        "ai_storm_tracks_status_endpoint": "/ai/storm-tracks/status",
        "ai_storm_tracks_analysis_endpoint": "/ai/storm-tracks/analysis",
        "ai_storm_tracks_map_endpoint": "/ai/storm-tracks/map",
        "ai_storm_tracks_geojson_endpoint": "/ai/storm-tracks/map.geojson",
        "ai_storm_tracks_training_status_endpoint": "/ai/storm-tracks/training/status",
        "ai_storm_tracks_training_plan_endpoint": "/ai/storm-tracks/training/plan",
        "ai_storm_historical_sources_endpoint": "/ai/storm-tracks/historical/sources",
        "ai_storm_historical_status_endpoint": "/ai/storm-tracks/historical/status",
        "ai_storm_historical_readiness_endpoint": "/ai/storm-tracks/historical/readiness",
        "ai_storm_historical_schema_endpoint": "/ai/storm-tracks/historical/schema",
        "ai_storm_historical_model_status_endpoint": "/ai/storm-tracks/historical/model-status",
        "ai_storm_historical_download_plan_endpoint": "/ai/storm-tracks/historical/download-plan",
        "caribbean_model_status_endpoint": "/caribbean/model/status",
        "caribbean_atlantic_report_endpoint": "/weather/report/caribbean-atlantic",
        "weather_report_endpoint_template": "/weather/report/{municipality}",
    }


@app.get("/desktop-app", include_in_schema=False)
def desktop_app_redirect():
    return RedirectResponse(url="/desktop/")


@app.get("/computer", include_in_schema=False)
def computer_redirect():
    return RedirectResponse(url="/desktop/")


if DESKTOP_CLIENT.exists() and not _route_exists("/desktop"):
    app.mount("/desktop", StaticFiles(directory=str(DESKTOP_CLIENT), html=True), name="desktop-web")

if MOBILE_CLIENT.exists() and not _route_exists("/mobile"):
    app.mount("/mobile", StaticFiles(directory=str(MOBILE_CLIENT), html=True), name="mobile-web")
