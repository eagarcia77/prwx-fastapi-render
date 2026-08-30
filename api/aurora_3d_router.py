from __future__ import annotations

from fastapi import APIRouter

from prwx.aurora_3d_scene_v36 import model_identity, report, scene_layers, scene_payload, status

router = APIRouter(tags=["AURORA 3D Command Center v3.6"])


@router.get("/aurora-caribe/3d/model")
def aurora_3d_model():
    return model_identity()


@router.get("/aurora-caribe/3d/status")
def aurora_3d_status():
    return status()


@router.get("/aurora-caribe/3d/layers")
def aurora_3d_layers():
    return scene_layers()


@router.get("/aurora-caribe/3d/scene")
def aurora_3d_scene():
    return scene_payload()


@router.get("/aurora-caribe/3d/report")
def aurora_3d_report():
    return report()
