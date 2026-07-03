from pathlib import Path

from prwx.life_safety_v18 import build_life_safety_actions, build_municipal_life_safety

def test_life_safety_actions():
    df = build_life_safety_actions("2026-07-01T00:00:00+00:00")
    assert {"inundacion", "tsunami", "huracan"}.issubset(set(df["hazard"]))

def test_municipal_life_safety(tmp_path: Path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    df = build_municipal_life_safety(tmp_path, "2026-07-01T00:00:00+00:00")
    assert len(df) == 4
