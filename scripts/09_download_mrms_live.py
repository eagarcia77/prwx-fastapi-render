from pathlib import Path
import argparse

from prwx.municipalities import load_municipalities
from prwx.sources.mrms_live import download_mrms_for_locations

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    locs = load_municipalities(ROOT / "data" / "sample" / "pr_municipalities.csv")
    df = download_mrms_for_locations(locs, limit=args.limit)
    out = ROOT / "data" / "processed" / "live_mrms_qpe.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"MRMS file created: {out} rows={len(df)}")
