from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TRAIN_ROOT = ROOT / "data" / "training"
MANIFEST_ROOT = TRAIN_ROOT / "manifests"
STATE_PATH = TRAIN_ROOT / "backfill_state.json"


@dataclass(frozen=True)
class BackfillTask:
    source: str
    day: str
    cycle: int
    forecast_hours: str
    member: str | None = None

    @property
    def key(self) -> str:
        member = f"-{self.member}" if self.member else ""
        return f"{self.source}{member}-{self.day}-{self.cycle:02d}"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_days(start: date, end: date, stride_days: int = 1) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=max(1, stride_days))


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"completed": {}, "failed": {}, "updated_at_utc": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"completed": {}, "failed": {}, "updated_at_utc": None}


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def manifest_path(task: BackfillTask) -> Path:
    day = task.day.replace("-", "")
    return MANIFEST_ROOT / f"{task.source}_{day}_{task.cycle:02d}.json"


def manifest_completed(task: BackfillTask) -> bool:
    path = manifest_path(task)
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return int(payload.get("rows", 0) or 0) > 0 and not payload.get("failures")
    except Exception:
        return False


def build_plan(
    start: date,
    end: date,
    *,
    sources: list[str],
    cycles: list[int],
    forecast_hours: str,
    stride_days: int,
    gefs_members: list[str],
) -> list[BackfillTask]:
    plan: list[BackfillTask] = []
    for day in iter_days(start, end, stride_days=stride_days):
        day_text = day.isoformat()
        for cycle in cycles:
            for source in sources:
                if source == "gefs_member":
                    for member in gefs_members:
                        plan.append(BackfillTask(source, day_text, cycle, forecast_hours, member))
                else:
                    plan.append(BackfillTask(source, day_text, cycle, forecast_hours))
    return plan


def command_for(task: BackfillTask, locations: Path) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "24_collect_model_archive_pr.py"),
        "--source",
        task.source,
        "--date",
        task.day,
        "--cycle",
        str(task.cycle),
        "--forecast-hours",
        task.forecast_hours,
        "--locations",
        str(locations),
    ]
    if task.member:
        command += ["--member", task.member]
    return command


def ensure_observations(start: date, end: date, observations: Path, execute: bool) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "23_collect_ncei_pr.py"),
        "--start",
        start.isoformat(),
        "--end",
        end.isoformat(),
        "--output",
        str(observations),
        "--continue-on-error",
    ]
    if execute and not observations.exists():
        subprocess.run(command, cwd=ROOT, check=True)
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or execute a resumable NOAA backfill for PR-CARIBE WX.")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--sources", default="gfs,nam_pr,gefs_mean,gefs_spread")
    parser.add_argument("--cycles", default="0,12", help="Comma-separated UTC cycles; 0/6/12/18")
    parser.add_argument("--forecast-hours", default="0,3,6,9,12,18,24")
    parser.add_argument("--stride-days", type=int, default=1)
    parser.add_argument("--gefs-members", default="p01,p02,p03,p04,p05")
    parser.add_argument("--observations", type=Path, default=TRAIN_ROOT / "observations_ncei_pr.parquet")
    parser.add_argument("--execute", action="store_true", help="Execute tasks. Without this flag the command is a dry-run plan.")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--max-tasks", type=int, default=0, help="Safety limit; 0 means no task-count limit.")
    parser.add_argument("--assemble", action="store_true", help="Build the canonical training table after collection.")
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise SystemExit("--end must not be before --start")
    sources = [value.strip() for value in args.sources.split(",") if value.strip()]
    allowed_sources = {"gfs", "nam_pr", "gefs_mean", "gefs_spread", "gefs_member"}
    invalid = sorted(set(sources) - allowed_sources)
    if invalid:
        raise SystemExit(f"Unsupported sources: {invalid}")
    cycles = sorted({int(value.strip()) for value in args.cycles.split(",") if value.strip()})
    if any(cycle not in {0, 6, 12, 18} for cycle in cycles):
        raise SystemExit("Cycles must be 0, 6, 12 or 18")
    members = [value.strip() for value in args.gefs_members.split(",") if value.strip()]

    observation_command = ensure_observations(start, end, args.observations, args.execute)
    plan = build_plan(
        start,
        end,
        sources=sources,
        cycles=cycles,
        forecast_hours=args.forecast_hours,
        stride_days=args.stride_days,
        gefs_members=members,
    )
    state = load_state()
    pending: list[BackfillTask] = []
    skipped = 0
    for task in plan:
        if manifest_completed(task) or task.key in state.get("completed", {}):
            skipped += 1
            continue
        if not args.retry_failed and task.key in state.get("failed", {}):
            skipped += 1
            continue
        pending.append(task)

    if args.max_tasks > 0:
        pending = pending[: args.max_tasks]

    summary = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "sources": sources,
        "cycles": cycles,
        "forecast_hours": args.forecast_hours,
        "planned_tasks": len(plan),
        "pending_tasks": len(pending),
        "skipped_tasks": skipped,
        "execute": args.execute,
        "observation_command": observation_command,
        "sample_commands": [command_for(task, args.observations) for task in pending[:5]],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not args.execute:
        return 0

    for index, task in enumerate(pending, start=1):
        print(f"[{index}/{len(pending)}] {task.key}", flush=True)
        command = command_for(task, args.observations)
        try:
            subprocess.run(command, cwd=ROOT, check=True)
            state.setdefault("completed", {})[task.key] = {
                "task": asdict(task),
                "finished_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            }
            state.setdefault("failed", {}).pop(task.key, None)
        except subprocess.CalledProcessError as exc:
            state.setdefault("failed", {})[task.key] = {
                "task": asdict(task),
                "returncode": exc.returncode,
                "failed_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            }
        finally:
            save_state(state)

    if args.assemble:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "25_build_pr_caribbean_training.py")], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
