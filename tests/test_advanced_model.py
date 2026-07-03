import pandas as pd
from prwx.advanced_model import train_advanced_bias_model, predict_advanced_corrected


def test_advanced_model_predicts_intervals():
    df = pd.read_csv("data/sample/training_sample.csv")
    model, metrics = train_advanced_bias_model(df)
    out = predict_advanced_corrected(model, df)
    assert "corrected_precip_24h_in" in out.columns
    assert "precip_p10_in" in out.columns
    assert "precip_p90_in" in out.columns
    assert (out["precip_p90_in"] >= out["precip_p10_in"]).all()
