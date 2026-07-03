from __future__ import annotations

import pandas as pd
import requests

NWS_ALERTS_ACTIVE = "https://api.weather.gov/alerts/active"

ALERT_COLUMNS = [
    "id", "event", "severity", "urgency", "certainty", "effective",
    "expires", "areaDesc", "headline", "alert_status", "error"
]


def download_pr_alerts(timeout: int = 20, user_agent: str | None = None) -> pd.DataFrame:
    headers = {"User-Agent": user_agent or "prwx-hybrid-model/0.5 (educational prototype)"}
    params = {"area": "PR"}
    try:
        r = requests.get(NWS_ALERTS_ACTIVE, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return pd.DataFrame([{"alert_status": f"alerts_error:{type(exc).__name__}", "error": str(exc)}], columns=ALERT_COLUMNS)

    rows = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        rows.append({
            "id": p.get("id"),
            "event": p.get("event"),
            "severity": p.get("severity"),
            "urgency": p.get("urgency"),
            "certainty": p.get("certainty"),
            "effective": p.get("effective"),
            "expires": p.get("expires"),
            "areaDesc": p.get("areaDesc"),
            "headline": p.get("headline"),
            "alert_status": "ok",
        })
    return pd.DataFrame(rows, columns=ALERT_COLUMNS)


def count_alerts_for_region(alerts: pd.DataFrame, region: str | None = None) -> int:
    if alerts.empty or "alert_status" not in alerts.columns:
        return 0
    if alerts["alert_status"].astype(str).str.contains("error").all():
        return 0
    return int(len(alerts[alerts["alert_status"] == "ok"]))
