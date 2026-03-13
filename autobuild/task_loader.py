from pathlib import Path
from typing import List, Optional

import yaml

from .models import Task

_REQUIRED = {
    "id",
    "title",
    "description",
    "context_files",
    "extensibility_scenario",
}


def load(path: Path, default_variation_instructions: Optional[List[str]] = None) -> Task:
    raw = yaml.safe_load(path.read_text())
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"Task {path} missing fields: {missing}")
    instructions = raw.get("variation_instructions") or default_variation_instructions or []
    if len(instructions) != 3:
        raise ValueError(
            f"Task {path} must have exactly 3 variation_instructions "
            "(set them on the task or via default_variation_instructions in config.yaml)",
        )
    raw["variation_instructions"] = instructions
    # Only pass fields that exist on Task (allows optional fields like min_coverage)
    data = {k: raw[k] for k in Task.__dataclass_fields__ if k in raw}
    return Task(**data)


def load_backlog(backlog_dir: Path, default_variation_instructions: Optional[List[str]] = None) -> List[Task]:
    files = sorted(backlog_dir.glob("*.yaml"))
    return [load(f, default_variation_instructions) for f in files]

