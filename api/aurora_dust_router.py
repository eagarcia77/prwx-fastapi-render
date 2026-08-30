from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from prwx.aurora_dust_v35 import (
    dust_analysis,
    dust_geojson,
    generate_artifacts,
    health_guidance,
    source_catalog,
    status,
    training_plan,
    training_status,
)

router = APIRouter(tags=["AURORA Sahara-Caribe v3.5"])


@router.get("/aurora-caribe/dust/model")
def aurora_dust_model():
    return status()["model"]


@router.get("/aurora-caribe/dust/status")
def aurora_dust_status():
    return status()


@router.get("/aurora-caribe/dust/sources")
def aurora_dust_sources():
    return source_catalog()


@router.get("/aurora-caribe/dust/analysis")
def aurora_dust_analysis():
    return dust_analysis()


@router.get("/aurora-caribe/dust/map")
def aurora_dust_map():
    return dust_geojson()


@router.get("/aurora-caribe/dust/map.geojson")
def aurora_dust_map_geojson():
    return dust_geojson()


@router.get("/aurora-caribe/dust/training/plan")
def aurora_dust_training_plan():
    return training_plan()


@router.get("/aurora-caribe/dust/training/plan.md")
def aurora_dust_training_plan_md():
    plan = training_plan()
    lines = [
        f"# {plan['model']['model_name']} v{plan['model']['version']}",
        "",
        "## Objetivo",
        plan["objective"],
        "",
        "## Variables objetivo",
        *[f"- {item}" for item in plan["target_variables"]],
        "",
        "## Variables predictoras",
        *[f"- {item}" for item in plan["features"]],
        "",
        "## Seguridad",
        plan["safety_rule"],
    ]
    return JSONResponse({"markdown": "\n".join(lines)})


@router.get("/aurora-caribe/dust/training/status")
def aurora_dust_training_status():
    return training_status()


@router.get("/aurora-caribe/dust/health-guidance")
def aurora_dust_health_guidance():
    return health_guidance()


@router.post("/aurora-caribe/dust/generate-artifacts")
def aurora_dust_generate_artifacts():
    return generate_artifacts()
