from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from prwx.ai_storm_tracks_v29 import analyze_events, generate_artifacts, status, storm_geojson, train_if_possible, training_plan, training_status

router = APIRouter(tags=["AI Storm Trajectory Map v2.9"])


@router.get("/ai/storm-tracks/status")
def ai_storm_tracks_status():
    return status()


@router.get("/ai/storm-tracks/analysis")
def ai_storm_tracks_analysis():
    return analyze_events()


@router.get("/ai/storm-tracks/map")
def ai_storm_tracks_map():
    return storm_geojson()


@router.get("/ai/storm-tracks/map.geojson")
def ai_storm_tracks_map_geojson():
    return storm_geojson()


@router.get("/ai/storm-tracks/training/status")
def ai_storm_tracks_training_status():
    return training_status()


@router.get("/ai/storm-tracks/training/plan")
def ai_storm_tracks_training_plan():
    return training_plan()


@router.get("/ai/storm-tracks/training/plan.md")
def ai_storm_tracks_training_plan_markdown():
    plan = training_plan()
    lines = [
        f"# {plan['engine']} v{plan['version']}",
        "",
        "## Objetivo",
        plan["objective"],
        "",
        "## Variables objetivo",
        *[f"- {item}" for item in plan["target_variables"]],
        "",
        "## Variables predictoras IA",
        *[f"- {item}" for item in plan["features"]],
        "",
        "## Fuentes oficiales",
        *[f"- {item}" for item in plan["official_sources"]],
        "",
        "## Regla de seguridad",
        plan["safety_rule"],
    ]
    return {"markdown": "\n".join(lines)}


@router.post("/ai/storm-tracks/train")
def ai_storm_tracks_train(force: bool = Query(False, description="Allow small experimental training if data is below research threshold.")):
    return train_if_possible(force=force)


@router.post("/ai/storm-tracks/generate-artifacts")
def ai_storm_tracks_generate_artifacts():
    return generate_artifacts()


@router.get("/ai/storm-tracks/event/{event_id}")
def ai_storm_tracks_event(event_id: str):
    analysis = analyze_events()
    for event in analysis.get("events", []):
        if str(event.get("event_id", "")).casefold() == event_id.casefold():
            return event
    raise HTTPException(status_code=404, detail=f"Storm event not found: {event_id}")
