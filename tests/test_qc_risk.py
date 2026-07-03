import pandas as pd
from prwx.qc import add_quality_flags
from prwx.risk import add_risk_columns


def test_quality_and_operational_risk_columns():
    df = pd.DataFrame([{
        "municipality": "Adjuntas", "region": "central_mountains", "corrected_precip_24h_in": 2.5,
        "base_precip_24h_in": 1.5, "lat": 18.16, "lon": -66.72, "prob_ge_2in": 0.8,
        "prob_ge_4in": 0.2, "mrms_qpe_24h_in": 1.0, "base_heat_index_f": 96,
    }])
    out = add_quality_flags(add_risk_columns(df))
    assert out.loc[0, "impact_level"] in {"moderado", "alto", "crítico", "vigilancia", "bajo"}
    assert "quality_flag" in out.columns
