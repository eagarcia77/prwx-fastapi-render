from pathlib import Path

from prwx.sources.usgs_live import download_usgs_pr_gages

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    df = download_usgs_pr_gages()
    out = ROOT / "data" / "processed" / "live_usgs_gages.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"USGS file created: {out} rows={len(df)}")
