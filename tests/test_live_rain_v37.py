from __future__ import annotations

from prwx.live_rain_v37 import live_rain_summary, map_layers, model_identity, municipal_risk, status


def test_live_rain_model_identity():
    model = model_identity()
    assert model["model_code"] == "AURORA-RAIN"
    assert model["version"] == "3.7.0"


def test_live_rain_layers_include_radar_and_qpe():
    payload = map_layers()
    ids = {layer["id"] for layer in payload["layers"]}
    assert "radar_live" in ids
    assert "rain_1h" in ids
    assert "rain_24h" in ids
    assert "qpf_forecast" in ids


def test_municipal_risk_has_priority_towns():
    payload = municipal_risk({"rain_flood_alerts": 1, "alerts": [{"rain_priority": "moderado"}]})
    names = {row["name"] for row in payload["municipalities"]}
    assert {"Juana Díaz", "Ponce", "San Juan", "San Germán"}.issubset(names)


def test_live_rain_status_endpoints():
    payload = status()
    assert "/rain/live/summary" in payload["endpoints"]
    assert "/rain/live/municipal-risk" in payload["endpoints"]


def test_live_rain_summary_accepts_source_failures(monkeypatch):
    from prwx import live_rain_v37

    def fake_alerts():
        return {
            "status": "ok",
            "source": "test",
            "total_active_alerts": 1,
            "rain_flood_alerts": 1,
            "alerts": [{"event": "Flood Advisory", "rain_priority": "moderado"}],
            "all_alerts": [],
        }

    monkeypatch.setattr(live_rain_v37, "active_pr_alerts", fake_alerts)
    summary = live_rain_summary()
    assert summary["model"]["model_code"] == "AURORA-RAIN"
    assert summary["alerts"]["rain_flood_alerts"] == 1
