from __future__ import annotations

import numpy as np
import pandas as pd


def clip_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply conservative physical limits for PR operational data."""
    out = df.copy()
    limits = {
        "base_precip_24h_in": (0, 25),
        "corrected_precip_24h_in": (0, 30),
        "mrms_qpe_24h_in": (0, 30),
        "base_temp_f": (55, 110),
        "relative_humidity": (5, 100),
        "wind_speed_mph": (0, 120),
        "wind_dir_deg": (0, 360),
        "pw_in": (0, 4),
        "dust_index": (0, 1),
    }
    for col, (lo, hi) in limits.items():
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").clip(lo, hi)
    return out


def add_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = clip_columns(df)
    flags: list[str] = []
    for _, row in out.iterrows():
        f = []
        if pd.isna(row.get("base_precip_24h_in")):
            f.append("missing_base_precip")
        if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
            f.append("missing_location")
        if row.get("source_status") not in (None, "ok") and not pd.isna(row.get("source_status")):
            f.append(str(row.get("source_status")))
        if pd.notna(row.get("ensemble_spread_in")) and row.get("ensemble_spread_in") >= 1.0:
            f.append("high_ensemble_spread")
        if pd.notna(row.get("mrms_qpe_24h_in")) and pd.notna(row.get("corrected_precip_24h_in")):
            if abs(float(row.get("mrms_qpe_24h_in")) - float(row.get("corrected_precip_24h_in"))) >= 2.0:
                f.append("mrms_forecast_gap")
        flags.append(";".join(f) if f else "ok")
    out["quality_flag"] = flags
    out["data_completeness_pct"] = out.notna().mean(axis=1) * 100
    return out


def summarize_quality(df: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "mean_completeness_pct": float(df.notna().mean(axis=1).mean() * 100) if len(df) else 0.0,
        "quality_flags": df.get("quality_flag", pd.Series(dtype=str)).value_counts(dropna=False).to_dict(),
    }
