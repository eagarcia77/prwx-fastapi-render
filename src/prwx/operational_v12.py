from __future__ import annotations

from .operational_v11 import run_operational_update_v11


def run_operational_update_v12(*, limit=None, user_agent=None, include_mrms=True, include_usgs=True, include_alerts=True, include_seismic=True, append_to_history=True, force_retrain=False):
    """Wrapper for PR-WX v1.2 Alert Display.

    v1.2 keeps the validated operational pipeline and adds an alert UX layer:
    optional sound cue, local browser notifications, light/dark/high-contrast modes,
    and large-screen emergency layout.
    """
    return run_operational_update_v11(
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        include_seismic=include_seismic,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
    )
