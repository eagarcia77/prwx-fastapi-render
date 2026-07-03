from pathlib import Path

from prwx.municipalities import load_municipalities


def test_load_municipalities_has_78_rows():
    root = Path(__file__).resolve().parents[1]
    df = load_municipalities(root / "data" / "sample" / "pr_municipalities.csv")
    assert len(df) == 78


def test_municipalities_required_columns():
    root = Path(__file__).resolve().parents[1]
    df = load_municipalities(root / "data" / "sample" / "pr_municipalities.csv")
    assert {"municipality", "lat", "lon", "region", "elevation_m", "coastal"}.issubset(df.columns)
