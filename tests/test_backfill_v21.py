from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "26_backfill_pr_caribbean.py"
spec = importlib.util.spec_from_file_location("pr_caribe_backfill_v21", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_backfill_plan_is_deterministic_and_bounded():
    plan = module.build_plan(
        date(2026, 8, 11),
        date(2026, 8, 12),
        sources=["gfs", "nam_pr"],
        cycles=[0, 12],
        forecast_hours="0,6,12,24",
        stride_days=1,
        gefs_members=[],
    )
    assert len(plan) == 8
    assert plan[0].key == "gfs-2026-08-11-00"
    assert plan[-1].key == "nam_pr-2026-08-12-12"


def test_gefs_members_expand_into_separate_tasks():
    plan = module.build_plan(
        date(2026, 8, 12),
        date(2026, 8, 12),
        sources=["gefs_member"],
        cycles=[0],
        forecast_hours="6",
        stride_days=1,
        gefs_members=["p01", "p02", "p03"],
    )
    assert [task.member for task in plan] == ["p01", "p02", "p03"]
    assert len({task.key for task in plan}) == 3


def test_backfill_command_uses_collection_script_without_execution():
    task = module.BackfillTask("gfs", "2026-08-12", 0, "0,6,12,24")
    command = module.command_for(task, Path("observations.parquet"))
    text = " ".join(command)
    assert "24_collect_model_archive_pr.py" in text
    assert "--source gfs" in text
    assert "--forecast-hours 0,6,12,24" in text
