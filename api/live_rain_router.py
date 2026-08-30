from __future__ import annotations

from fastapi import APIRouter

from prwx.live_rain_v37 import (
    active_pr_alerts,
    live_rain_summary,
    map_layers,
    model_identity,
    municipal_risk,
    source_catalog,
    status,
)

router = APIRouter(tags=["AURORA RainCast PR v3.7"])


@router.get("/rain/live/model")
def rain_live_model():
    return model_identity()


@router.get("/rain/live/status")
def rain_live_status():
    return status()


@router.get("/rain/live/sources")
def rain_live_sources():
    return source_catalog()


@router.get("/rain/live/layers")
def rain_live_layers():
    return map_layers()


@router.get("/rain/live/alerts")
def rain_live_alerts():
    return active_pr_alerts()


@router.get("/rain/live/summary")
def rain_live_summary():
    return live_rain_summary()


@router.get("/rain/live/municipal-risk")
def rain_live_municipal_risk():
    return municipal_risk()
