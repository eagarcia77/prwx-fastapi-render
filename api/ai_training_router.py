from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from prwx.ai_training_engine_v27 import (
    AI_ENGINE_NAME,
    AI_ENGINE_VERSION,
    AI_TRAINING_PLAN_PATH,
    feature_matrix_catalog,
    load_ai_analysis,
    load_training_report,
    plan_as_markdown,
    read_training_table,
    save_ai_analysis_assets,
    train_ai_model_if_ready,
)

router = APIRouter(tags=["PR-WX AI Training v2.7"])


def _runtime_training_enabled() -> bool:
    return os.getenv("PRWX_ENABLE_RUNTIME_TRAINING", "false").strip().casefold() in {"1", "true", "yes", "on"}


@router.get("/ai/model/status")
def ai_model_status() -> dict[str, Any]:
    analysis = load_ai_analysis()
    training = load_training_report()
    return {
        "engine": AI_ENGINE_NAME,
        "version": AI_ENGINE_VERSION,
        "analysis_status": "available",
        "training_status": training.get("status", "not_trained"),
        "runtime_training_enabled": _runtime_training_enabled(),
        "readiness": analysis.get("readiness", {}),
        "model_path": training.get("model_path"),
        "model_file_exists": bool(training.get("model_file_exists", False)),
        "production_validated": False,
        "disclaimer": "AI training is experimental and must be validated by meteorological review before operational use.",
    }


@router.get("/ai/model/analyze")
def ai_model_analyze() -> dict[str, Any]:
    return save_ai_analysis_assets()


@router.get("/ai/model/training-plan")
def ai_model_training_plan() -> dict[str, Any]:
    return load_ai_analysis().get("plan", {})


@router.get("/ai/model/training-plan.md", response_class=PlainTextResponse)
def ai_model_training_plan_markdown() -> str:
    analysis = load_ai_analysis()
    plan = analysis.get("plan", {})
    if AI_TRAINING_PLAN_PATH.exists() and AI_TRAINING_PLAN_PATH.stat().st_size:
        return AI_TRAINING_PLAN_PATH.read_text(encoding="utf-8")
    return plan_as_markdown(plan)


@router.get("/ai/model/feature-matrix")
def ai_model_feature_matrix() -> dict[str, Any]:
    df, dataset_path = read_training_table()
    return {
        "engine": AI_ENGINE_NAME,
        "version": AI_ENGINE_VERSION,
        "dataset_path": dataset_path,
        "rows_loaded": int(len(df)),
        "feature_matrix": feature_matrix_catalog(),
    }


@router.get("/ai/model/train-status")
def ai_model_train_status() -> dict[str, Any]:
    return load_training_report()


@router.post("/ai/model/train")
def ai_model_train(force: bool = False) -> dict[str, Any]:
    if not _runtime_training_enabled():
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Runtime AI training is disabled on this server for stability.",
                "enable_with_env": "PRWX_ENABLE_RUNTIME_TRAINING=true",
                "recommended_command": "python scripts/35_ai_analyze_and_train_caribbean_atlantic_v27.py --train",
                "reason": "Render free services can restart and have limited resources; train offline or enable intentionally.",
            },
        )
    return train_ai_model_if_ready(force=force)


@router.get("/ai/model/report")
def ai_model_report() -> dict[str, Any]:
    return {
        "analysis": load_ai_analysis(),
        "training": load_training_report(),
    }
