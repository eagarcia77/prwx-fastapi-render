from __future__ import annotations

import pandas as pd


def classify_rain_risk(precip_24h_in: float, region: str | None = None) -> str:
    """Classify rainfall risk with PR-specific conservative thresholds."""
    multiplier = 0.85 if region in {"central_mountains", "east"} else 1.0
    value = float(precip_24h_in or 0) / multiplier
    if value >= 4.0:
        return "alto"
    if value >= 2.0:
        return "moderado"
    if value >= 1.0:
        return "bajo-moderado"
    return "bajo"


def calculate_operational_risk_score(row: pd.Series) -> float:
    """0-100 impact-oriented risk score for Puerto Rico.

    It combines corrected rainfall, probability thresholds, MRMS QPE, stream gauge
    hints, heat index and active alerts when available. It is intentionally
    conservative for central mountains and the east where orographic rain can
    escalate quickly.
    """
    precip = float(row.get("corrected_precip_24h_in", row.get("base_precip_24h_in", 0)) or 0)
    region = row.get("region")
    score = min(45.0, precip * 11.0)
    if region in {"central_mountains", "east"}:
        score *= 1.12
    score += float(row.get("prob_ge_2in", 0) or 0) * 18
    score += float(row.get("prob_ge_4in", 0) or 0) * 24
    score += min(14.0, float(row.get("mrms_qpe_24h_in", 0) or 0) * 4.0)
    score += min(10.0, float(row.get("nearby_gage_stage_ft", 0) or 0) * 0.5)
    if str(row.get("active_nws_alerts", "0")) not in {"0", "", "nan", "None"}:
        score += 12
    heat = float(row.get("base_heat_index_f", 0) or 0)
    if heat >= 108:
        score += 10
    elif heat >= 102:
        score += 6
    elif heat >= 95:
        score += 3
    if float(row.get("ensemble_spread_in", 0) or 0) >= 1.2:
        score += 5
    return max(0.0, min(100.0, score))


def classify_impact(score: float) -> str:
    score = float(score)
    if score >= 75:
        return "crítico"
    if score >= 55:
        return "alto"
    if score >= 35:
        return "moderado"
    if score >= 18:
        return "vigilancia"
    return "bajo"


def add_risk_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    precip_col = "corrected_precip_24h_in" if "corrected_precip_24h_in" in out.columns else "base_precip_24h_in"
    out["rain_risk"] = [classify_rain_risk(p, r) for p, r in zip(out[precip_col], out.get("region", [None] * len(out)))]
    out["operational_risk_score"] = out.apply(calculate_operational_risk_score, axis=1)
    out["impact_level"] = out["operational_risk_score"].apply(classify_impact)
    if "base_heat_index_f" in out.columns:
        out["heat_risk"] = out["base_heat_index_f"].apply(lambda x: "alto" if x >= 102 else "moderado" if x >= 95 else "bajo")
    return out
