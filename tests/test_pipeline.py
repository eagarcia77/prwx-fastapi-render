from __future__ import annotations

import pandas as pd

from prwx.pipeline import append_history, load_metadata, write_metadata


def test_metadata_round_trip(tmp_path):
    path = tmp_path / "latest_run.json"
    payload = {"status": "ok", "rows_predicted": 3}
    write_metadata(path, payload)
    assert load_metadata(path) == payload


def test_append_history_keeps_run_timestamp(tmp_path):
    history = tmp_path / "history" / "live_predictions_history.csv"
    df = pd.DataFrame({"municipality": ["San Juan"], "corrected_precip_24h_in": [1.2]})
    append_history(df, history, "2026-06-26T00:00:00+00:00")
    out = pd.read_csv(history)
    assert len(out) == 1
    assert out.loc[0, "run_generated_at_utc"] == "2026-06-26T00:00:00+00:00"
