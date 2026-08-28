from __future__ import annotations

from fastapi import APIRouter, HTTPException

from prwx.ai_maps_v28 import map_layers, municipality_analysis, pr_ai_map_payload, status

router = APIRouter(tags=["AI Interactive Maps v2.8"])


@router.get("/ai/maps/status")
def ai_maps_status():
    return status()


@router.get("/ai/maps/layers")
def ai_maps_layers():
    return {"layers": map_layers()}


@router.get("/ai/maps/summary")
def ai_maps_summary():
    payload = pr_ai_map_payload()
    return payload["summary"]


@router.get("/ai/maps/pr-municipalities")
def ai_maps_pr_municipalities():
    return pr_ai_map_payload()


@router.get("/ai/maps/pr-municipalities.geojson")
def ai_maps_pr_municipalities_geojson():
    return pr_ai_map_payload()


@router.get("/ai/maps/municipality/{municipality}")
def ai_maps_municipality(municipality: str):
    try:
        return municipality_analysis(municipality)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Municipality not found: {municipality}")
