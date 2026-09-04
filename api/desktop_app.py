from __future__ import annotations

import os
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from api.app import ROOT, app, utc_now_iso
from api.ai_maps_router import router as ai_maps_router
from api.ai_storm_historical_router import router as ai_storm_historical_router
from api.ai_storm_tracks_router import router as ai_storm_tracks_router
from api.ai_training_router import router as ai_training_router
from api.aurora_3d_router import router as aurora_3d_router
from api.aurora_caribe_router import router as aurora_caribe_router
from api.aurora_dust_router import router as aurora_dust_router
from api.caribbean_router import router as caribbean_router
from api.live_rain_router import router as live_rain_router
from api.meteorological_report_router import router as meteorological_report_router

VERSION = "6.0.0"
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


_ensure_router(meteorological_report_router, "meteorological_report_router_installed", "meteorological_report_router_paths")
_ensure_router(ai_training_router, "ai_training_router_installed", "ai_training_router_paths")
_ensure_router(ai_maps_router, "ai_maps_router_installed", "ai_maps_router_paths")
_ensure_router(ai_storm_tracks_router, "ai_storm_tracks_router_installed", "ai_storm_tracks_router_paths")
_ensure_router(ai_storm_historical_router, "ai_storm_historical_router_installed", "ai_storm_historical_router_paths")
_ensure_router(aurora_caribe_router, "aurora_caribe_router_installed", "aurora_caribe_router_paths")
_ensure_router(aurora_dust_router, "aurora_dust_router_installed", "aurora_dust_router_paths")
_ensure_router(aurora_3d_router, "aurora_3d_router_installed", "aurora_3d_router_paths")
_ensure_router(live_rain_router, "live_rain_router_installed", "live_rain_router_paths")
_ensure_router(caribbean_router, "caribbean_router_installed", "caribbean_router_paths")

if not getattr(app.state, "desktop_wrapper_installed", False):
    app.router.routes.insert(0, APIRoute("/", _root_desktop_redirect, methods=["GET"], include_in_schema=False, name="root_desktop_redirect"))
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
        "api_docs": "/docs",
        "live_rain_model": "/rain/live/model",
        "live_rain_status": "/rain/live/status",
        "live_rain_layers": "/rain/live/layers",
        "live_rain_alerts": "/rain/live/alerts",
        "live_rain_summary": "/rain/live/summary",
        "live_rain_municipal_risk": "/rain/live/municipal-risk",
        "live_rain_satellite_latest": "/rain/live/satellite/latest",
        "live_rain_satellite_self_test": "/rain/live/satellite/self-test",
        "live_rain_satellite_proxy_band13": "/rain/live/satellite/proxy/band13",
        "live_rain_satellite_image_band13": "/rain/live/satellite/image/band13.jpg",
        "live_rain_satellite_wfo_band13": "/rain/live/satellite/wfo/band13.jpg",
        "live_rain_satellite_loop_band13": "/rain/live/satellite/loop/band13.gif",
        "live_rain_satellite_debug_band13": "/rain/live/satellite/debug/band13.html",
        "aurora_caribe_model": "/aurora-caribe/model",
        "aurora_caribe_status": "/aurora-caribe/status",
        "aurora_caribe_predictions": "/aurora-caribe/predictions/summary",
        "aurora_sahara_model": "/aurora-caribe/dust/model",
        "aurora_sahara_status": "/aurora-caribe/dust/status",
        "aurora_sahara_analysis": "/aurora-caribe/dust/analysis",
        "aurora_sahara_map_geojson": "/aurora-caribe/dust/map.geojson",
        "aurora_3d_scene": "/aurora-caribe/3d/scene",
        "ai_maps_geojson": "/ai/maps/pr-municipalities.geojson",
        "ai_storm_tracks_geojson": "/ai/storm-tracks/map.geojson",
        "caribbean_atlantic_report": "/weather/report/caribbean-atlantic",
        "weather_report_example": "/weather/report/San Juan",
        "render_url": _public_render_url(),
        "note": "Experimental operational dashboard. Official warnings must come from NOAA/NWS/NHC, health agencies and emergency-management agencies.",
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
        "desktop_live_rain_css_exists": (DESKTOP_CLIENT / "live-rain-v60.css").exists(),
        "desktop_live_rain_js_exists": (DESKTOP_CLIENT / "live-rain-v60.js").exists(),
        "mobile_folder_exists": MOBILE_CLIENT.exists(),
        "mobile_index_exists": (MOBILE_CLIENT / "index.html").exists(),
        "live_rain_router_installed": bool(getattr(app.state, "live_rain_router_installed", False)),
        "root_redirects_to": "/desktop/",
    }


@app.get("/desktop/config.json")
def desktop_config_json():
    return {
        "version": VERSION,
        "default_api_base": _public_render_url(),
        "health_endpoint": "/healthz",
        "status_endpoint": "/api/status",
        "live_rain_status_endpoint": "/rain/live/status",
        "live_rain_layers_endpoint": "/rain/live/layers",
        "live_rain_alerts_endpoint": "/rain/live/alerts",
        "live_rain_summary_endpoint": "/rain/live/summary",
        "live_rain_municipal_risk_endpoint": "/rain/live/municipal-risk",
        "live_rain_satellite_latest_endpoint": "/rain/live/satellite/latest",
        "live_rain_satellite_self_test_endpoint": "/rain/live/satellite/self-test",
        "live_rain_satellite_proxy_band13_endpoint": "/rain/live/satellite/proxy/band13",
        "live_rain_satellite_image_band13_endpoint": "/rain/live/satellite/image/band13.jpg",
        "live_rain_satellite_wfo_band13_endpoint": "/rain/live/satellite/wfo/band13.jpg",
        "live_rain_satellite_loop_band13_endpoint": "/rain/live/satellite/loop/band13.gif",
        "live_rain_satellite_debug_band13_endpoint": "/rain/live/satellite/debug/band13.html",
        "aurora_caribe_status_endpoint": "/aurora-caribe/status",
        "aurora_sahara_status_endpoint": "/aurora-caribe/dust/status",
        "aurora_3d_scene_endpoint": "/aurora-caribe/3d/scene",
        "ai_maps_geojson_endpoint": "/ai/maps/pr-municipalities.geojson",
        "ai_storm_tracks_geojson_endpoint": "/ai/storm-tracks/map.geojson",
        "caribbean_atlantic_report_endpoint": "/weather/report/caribbean-atlantic",
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
