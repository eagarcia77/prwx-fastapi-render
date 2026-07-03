from pathlib import Path

from prwx.sources.nws_alerts import download_pr_alerts

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    df = download_pr_alerts()
    out = ROOT / "data" / "processed" / "live_nws_alerts.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"NWS alerts file created: {out} rows={len(df)}")
