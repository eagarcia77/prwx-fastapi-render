from __future__ import annotations

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MUNICIPALITIES_PATH = PROJECT_ROOT / "data" / "sample" / "pr_municipalities.csv"


def load_municipalities(path: str | Path | None = None) -> pd.DataFrame:
    """Load approximate municipality centroid metadata for Puerto Rico.

    The included coordinates are practical centroids for prototyping and mapping.
    For production-grade hydrology, replace these with official GIS centroids or
    municipality polygons from authoritative GIS sources.
    """
    data_path = Path(path) if path else DEFAULT_MUNICIPALITIES_PATH
    df = pd.read_csv(data_path)
    required = {"municipality", "lat", "lon", "region", "elevation_m", "coastal"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Municipality file is missing required columns: {sorted(missing)}")
    return df


def get_municipality(name: str, path: str | Path | None = None) -> pd.Series:
    df = load_municipalities(path)
    mask = df["municipality"].str.lower() == name.lower()
    if not mask.any():
        raise KeyError(f"Municipality not found: {name}")
    return df.loc[mask].iloc[0]


def filter_municipalities(region: str | None = None, coastal: int | None = None) -> pd.DataFrame:
    df = load_municipalities()
    if region:
        df = df[df["region"] == region]
    if coastal is not None:
        df = df[df["coastal"] == int(coastal)]
    return df.reset_index(drop=True)
