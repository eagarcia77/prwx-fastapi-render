from __future__ import annotations

from fastapi import APIRouter

from prwx.storm_historical_ingest_v30 import sample_schema, source_catalog, status, training_readiness
from prwx.storm_historical_train_v30 import model_status

router = APIRouter(tags=["AI Storm Historical Data v3.0"])


@router.get("/ai/storm-tracks/historical/sources")
def historical_sources():
    return {"version": "3.0.0", "sources": source_catalog()}


@router.get("/ai/storm-tracks/historical/status")
def historical_status():
    return status()


@router.get("/ai/storm-tracks/historical/readiness")
def historical_readiness():
    return training_readiness()


@router.get("/ai/storm-tracks/historical/schema")
def historical_schema():
    return sample_schema()


@router.get("/ai/storm-tracks/historical/model-status")
def historical_model_status():
    return model_status()


@router.get("/ai/storm-tracks/historical/download-plan")
def historical_download_plan():
    return {
        "version": "3.0.0",
        "recommended_order": [
            "1. Download and parse NOAA/NHC HURDAT2 Atlantic best track.",
            "2. Build data/training/storm_tracks_atlantic_training.csv with 72-hour Puerto Rico approach labels.",
            "3. Train the experimental AI model locally with scripts/39_train_storm_historical_ai_v30.py.",
            "4. Add IBTrACS as an independent validation source.",
            "5. Add AEWC, ERA5 or NCEP/NCAR Reanalysis variables for tropical waves and troughs.",
        ],
        "commands": {
            "download_hurdat2_and_build_table": "python scripts/38_download_historical_storm_data_v30.py",
            "train_research_model": "python scripts/39_train_storm_historical_ai_v30.py --train",
            "train_small_test_model": "python scripts/39_train_storm_historical_ai_v30.py --train --force",
        },
        "safety_rule": "The AI product is experimental. Official tropical cyclone warnings must come from NHC/NWS and emergency-management agencies.",
    }
