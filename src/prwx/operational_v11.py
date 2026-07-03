from __future__ import annotations

from .operational_v10 import run_operational_update_v10


def run_operational_update_v11(*, limit=None, user_agent=None, include_mrms=True, include_usgs=True, include_alerts=True, include_seismic=True, append_to_history=True, force_retrain=False):
    """Wrapper for the v1.1 emergency display release.

    v1.1 keeps the validated v1.0 operational pipeline and adds a new
    emergency-display UX layer in the dashboard.
    """
    result = run_operational_update_v10(
        limit=limit,
        user_agent=user_agent,
        include_mrms=include_mrms,
        include_usgs=include_usgs,
        include_alerts=include_alerts,
        include_seismic=include_seismic,
        append_to_history=append_to_history,
        force_retrain=force_retrain,
    )
    return result
