from pathlib import Path
from typing import List

import yaml

from .models import Task

_REQUIRED = {
    "id",
    "title",
    "description",
    "context_files",
    "variation_instructions",
    "extensibility_scenario",
}


def load(path: Path) -> Task:
    raw = yaml.safe_load(path.read_text())
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"Task {path} missing fields: {missing}")
    if len(raw["variation_instructions"]) != 3:
        raise ValueError(
            f"Task {path} must have exactly 3 variation_instructions",
        )
    # Only pass fields that exist on Task (allows optional fields like min_coverage)
    data = {k: raw[k] for k in Task.__dataclass_fields__ if k in raw}
    return Task(**data)


def load_backlog(backlog_dir: Path) -> List[Task]:
    files = sorted(backlog_dir.glob("*.yaml"))
    return [load(f) for f in files]

