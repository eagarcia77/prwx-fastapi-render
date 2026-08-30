from __future__ import annotations

from fastapi import APIRouter, Query

from prwx.aurora_caribe_ai_v34 import (
    MODEL_NAME,
    data_readiness,
    model_identity,
    model_status,
    prediction_layers,
    prediction_summary,
    run_training_iteration,
    training_plan,
    training_status,
)

router = APIRouter(tags=["AURORA Caribe-Atlántico v3.4"])


@router.get("/aurora-caribe/model")
def aurora_caribe_model_identity():
    return model_identity()


@router.get("/aurora-caribe/status")
def aurora_caribe_status():
    return model_status()


@router.get("/aurora-caribe/readiness")
def aurora_caribe_readiness():
    return data_readiness()


@router.get("/aurora-caribe/training/status")
def aurora_caribe_training_status():
    return training_status()


@router.get("/aurora-caribe/training/plan")
def aurora_caribe_training_plan():
    return training_plan()


@router.get("/aurora-caribe/maps/layers")
def aurora_caribe_map_layers():
    return prediction_layers()


@router.get("/aurora-caribe/predictions/summary")
def aurora_caribe_predictions_summary():
    return prediction_summary()


@router.get("/aurora-caribe/report")
def aurora_caribe_report():
    return {
        "title": f"Reporte operacional experimental de {MODEL_NAME}",
        "status": model_status(),
        "predictions": prediction_summary(),
        "plan": training_plan(),
    }


@router.post("/aurora-caribe/training/run")
def aurora_caribe_training_run(force: bool = Query(False, description="Force an experimental training manifest even if readiness is low.")):
    return run_training_iteration(force=force)
