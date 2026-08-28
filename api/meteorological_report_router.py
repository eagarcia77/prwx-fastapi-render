from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.caribbean_router import _model_status_payload, _training_status_payload
from prwx.meteorological_report_v26 import (
    build_report_markdown,
    build_report_payload,
    model_feature_matrix,
    training_plan_payload,
)

router = APIRouter(tags=["PR-WX Meteorological Report v2.6"])


@router.get("/weather/report/caribbean-atlantic")
def caribbean_atlantic_meteorological_report():
    model_status = _model_status_payload()
    training_status = _training_status_payload()
    return build_report_payload(model_status, training_status)


@router.get("/weather/report/caribbean-atlantic.md", response_class=PlainTextResponse)
def caribbean_atlantic_meteorological_report_markdown():
    model_status = _model_status_payload()
    training_status = _training_status_payload()
    return build_report_markdown(model_status, training_status)


@router.get("/caribbean/model/training-plan")
def caribbean_atlantic_training_plan():
    model_status = _model_status_payload()
    training_status = _training_status_payload()
    return training_plan_payload(model_status, training_status)


@router.get("/caribbean/model/feature-matrix")
def caribbean_atlantic_feature_matrix():
    return {"version": "2.6.0", "matrix": model_feature_matrix()}
