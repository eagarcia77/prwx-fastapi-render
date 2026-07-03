from prwx.risk import classify_rain_risk


def test_rain_risk_low():
    assert classify_rain_risk(0.2) == "bajo"


def test_rain_risk_high():
    assert classify_rain_risk(5.0) == "alto"
