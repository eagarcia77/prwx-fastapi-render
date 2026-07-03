from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "data" / "processed" / "live_predictions_v5.csv",
    ROOT / "data" / "processed" / "latest_run.json",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(f"Missing required outputs: {missing}")

df = pd.read_csv(required[0])
if df.empty:
    raise SystemExit("live_predictions_v5.csv is empty")
for col in ["municipality", "corrected_precip_24h_in", "operational_risk_score", "impact_level", "quality_flag"]:
    if col not in df.columns:
        raise SystemExit(f"Missing required column: {col}")
meta = json.loads(required[1].read_text(encoding="utf-8"))
if meta.get("status") != "ok":
    raise SystemExit(f"latest_run.json status is not ok: {meta.get('status')}")
print(f"v0.5 outputs valid. rows={len(df)} max_risk={df['operational_risk_score'].max():.1f}")
