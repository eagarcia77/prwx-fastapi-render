from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


def load_settings(path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    """Load YAML settings for the PR-WX project."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
