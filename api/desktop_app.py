from __future__ import annotations

import os
from pathlib import Path

from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from api.app import ROOT, app, utc_now_iso
from api.caribbean_router import router as caribbean_router

VERSION = "2.5.1"
DESKTOP_CLIENT = ROOT / "desktop"
MOBILE_CLIENT = ROOT / "mobile"


def _public_render_url() -> str:
    return os.getenv("PRWX_PUBLIC_RENDER_URL", "https://prwx-fastapi-render.onrender.com").rstrip("/")


def _route_exists(path: str) -> bool:
    return any(getattr(route, "path", None) == path for route in app.router.routes)


def _ensure_caribbean_router() -> None:
    expected = [getattr(route, "path", None) for route in caribbean_router.routes]
    if not all(path and _route_exists(path) for path in expected):
        app.include_router(caribbean_router)
    for route in caribbean_router.routes:
        path = getattr(route, "path", None)
        if path and not _route_exists(path):
            app.router.routes.append(route)
    missing = [path for path in expected if path and not _route_exists(path)]
    if missing:
        raise RuntimeError(f"PR-CARIBE routes were not registered: {missing}")
    app.state.caribbean_router_installed = True
    app.state.caribbean_router_paths = expected


def _root_desktop_redirect():
    return RedirectResponse(url="/desktop/")


_ensure_caribbean_router()

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
        "caribbean_model_status": "/caribbean/model/status",
        "caribbean_model_sources": "/caribbean/model/sources",
        "caribbean_model_readiness": "/caribbean/model/readiness",
        "caribbean_training_status": "/caribbean/training/status",
        "weather_report_example": "/weather/report/San Juan",
        "render_url": _public_render_url(),
        "note": "Experimental operational dashboard. Official warnings must come from NOAA/NWS/NHC and emergency-management agencies.",
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
        "mobile_folder_exists": MOBILE_CLIENT.exists(),
        "mobile_index_exists": (MOBILE_CLIENT / "index.html").exists(),
        "caribbean_router_installed": bool(getattr(app.state, "caribbean_router_installed", False)),
        "caribbean_router_paths": list(getattr(app.state, "caribbean_router_paths", [])),
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
        "caribbean_model_status_endpoint": "/caribbean/model/status",
        "caribbean_model_sources_endpoint": "/caribbean/model/sources",
        "caribbean_model_readiness_endpoint": "/caribbean/model/readiness",
        "caribbean_training_status_endpoint": "/caribbean/training/status",
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
