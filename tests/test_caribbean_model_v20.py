from __future__ import annotations

import numpy as np
import pandas as pd

from prwx.caribbean_model_v20 import MODEL_NAME, MODEL_VERSION, predict_caribbean, train_caribbean_model, training_readiness
from prwx.caribbean_sources import source_ids


def sample_frame(rows: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-06-01", periods=rows, freq="6h", tz="UTC")
    gfs_temp = 82 + rng.normal(0, 3, rows)
    nws_temp = gfs_temp + rng.normal(0, 1.2, rows)
    gfs_rain = np.maximum(0, rng.gamma(1.2, 0.18, rows))
    mrms = np.maximum(0, gfs_rain + rng.normal(0, 0.08, rows))
    return pd.DataFrame({
        "valid_time_utc": dates,
        "station_id": [f"S{i % 10:02d}" for i in range(rows)],
        "island": ["Puerto Rico" if i % 2 else "USVI" for i in range(rows)],
        "lat": 17.8 + rng.random(rows) * 1.2,
        "lon": -67.3 + rng.random(rows) * 2.0,
        "elevation_m": rng.uniform(0, 800, rows),
        "coastal": rng.integers(0, 2, rows),
        "gfs_temp_f": gfs_temp,
        "nws_temp_f": nws_temp,
        "gfs_precip_24h_in": gfs_rain,
        "gefs_precip_mean_24h_in": gfs_rain * rng.uniform(0.85, 1.2, rows),
        "gefs_precip_spread_24h_in": rng.uniform(0.02, 0.25, rows),
        "mrms_qpe_24h_in": mrms,
        "observed_temp_f": 0.55 * nws_temp + 0.45 * gfs_temp + rng.normal(0, 0.5, rows),
        "observed_precip_24h_in": np.maximum(0, 0.45 * gfs_rain + 0.55 * mrms + rng.normal(0, 0.04, rows)),
    })


def test_source_registry_has_pr_backbone():
    ids = source_ids()
    for expected in {"nws_sju_grid", "nam_pr_nest", "gfs", "gefs", "mrms_caribbean", "goes19", "nhc", "hafs"}:
        assert expected in ids


def test_caribbean_training_and_prediction():
    df = sample_frame()
    bundle, report = train_caribbean_model(df)
    assert bundle.model_name == MODEL_NAME
    assert bundle.model_version == MODEL_VERSION
    assert "observed_temp_f" in bundle.targets
    assert "observed_precip_24h_in" in bundle.targets
    assert report["targets"]["observed_temp_f"]["metrics"]["mae"] >= 0
    pred = predict_caribbean(bundle, df.tail(5))
    assert "forecast_temp_f" in pred.columns
    assert "forecast_precip_24h_in" in pred.columns
    assert (pred["forecast_precip_24h_in"] >= 0).all()


def test_demo_scale_is_not_declared_operational():
    readiness = training_readiness(sample_frame())
    assert readiness["research_ready"] is False
    assert readiness["operational_candidate"] is False
    assert readiness["production_validated"] is False
