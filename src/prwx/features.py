from __future__ import annotations

import math
import numpy as np
import pandas as pd

REGION_ORDER = ["north_coast", "south_coast", "west", "east", "central_mountains"]


def heat_index_f(temp_f: float, relative_humidity: float) -> float:
    """NOAA/NWS style heat index approximation in Fahrenheit.

    Valid mainly for warm and humid conditions. For lower temperatures, returns temp_f.
    """
    if temp_f < 80 or relative_humidity < 40:
        return float(temp_f)

    t = temp_f
    rh = relative_humidity
    hi = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * rh
        - 0.22475541 * t * rh
        - 0.00683783 * t * t
        - 0.05481717 * rh * rh
        + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh
        - 0.00000199 * t * t * rh * rh
    )
    return float(hi)


def add_time_features(df: pd.DataFrame, date_col: str | None = None) -> pd.DataFrame:
    """Add cyclical time features for month and hour."""
    out = df.copy()
    if date_col and date_col in out.columns:
        dt = pd.to_datetime(out[date_col])
        out["month"] = dt.dt.month
        out["hour"] = dt.dt.hour

    if "month" in out.columns:
        out["month_sin"] = np.sin(2 * math.pi * out["month"] / 12)
        out["month_cos"] = np.cos(2 * math.pi * out["month"] / 12)

    if "hour" in out.columns:
        out["hour_sin"] = np.sin(2 * math.pi * out["hour"] / 24)
        out["hour_cos"] = np.cos(2 * math.pi * out["hour"] / 24)

    return out


def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived weather features relevant to Puerto Rico."""
    out = df.copy()

    if {"base_temp_f", "relative_humidity"}.issubset(out.columns):
        out["base_heat_index_f"] = [
            heat_index_f(t, rh) for t, rh in zip(out["base_temp_f"], out["relative_humidity"])
        ]

    if "wind_dir_deg" in out.columns:
        radians = np.deg2rad(out["wind_dir_deg"])
        out["wind_u_proxy"] = np.cos(radians)
        out["wind_v_proxy"] = np.sin(radians)

    if {"lat", "lon"}.issubset(out.columns):
        # Coarse geographic features. Better version should use GIS rasters and coastline distance.
        out["northness"] = out["lat"] - 18.2
        out["westness"] = -66.3 - out["lon"]

    return out


def encode_region(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode Puerto Rico climate regions."""
    out = df.copy()
    if "region" not in out.columns:
        return out
    for region in REGION_ORDER:
        out[f"region_{region}"] = (out["region"] == region).astype(int)
    return out


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps."""
    out = add_time_features(df)
    out = add_weather_features(out)
    out = encode_region(out)
    return out


def model_feature_columns(df: pd.DataFrame) -> list[str]:
    """Select numeric model features available in a dataframe."""
    candidates = [
        "lat", "lon", "elevation_m", "coastal", "month_sin", "month_cos", "hour_sin", "hour_cos",
        "base_temp_f", "base_heat_index_f", "base_precip_24h_in", "relative_humidity",
        "wind_speed_mph", "wind_u_proxy", "wind_v_proxy", "pw_in", "dust_index",
        "mrms_qpe_1h_in", "mrms_qpe_3h_in", "mrms_qpe_6h_in", "mrms_qpe_24h_in",
        "nearby_gage_stage_ft", "nearby_gage_flow_cfs", "soil_proxy_7d_in",
        "northness", "westness",
        "region_north_coast", "region_south_coast", "region_west", "region_east", "region_central_mountains",
    ]
    return [c for c in candidates if c in df.columns]
