from pathlib import Path
import pandas as pd

from prwx.advanced_model import train_advanced_bias_model, save_advanced_model

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    df = pd.read_csv(ROOT / "data" / "sample" / "training_sample.csv")
    model, metrics = train_advanced_bias_model(df)
    out = ROOT / "models" / "prwx_advanced_bias_model.joblib"
    save_advanced_model(model, out)
    print("Advanced model saved:", out)
    print(metrics)
