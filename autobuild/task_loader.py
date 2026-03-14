from pathlib import Path
from typing import List, Optional

import frontmatter

from .models import Task, VariationInstruction

_REQUIRED = {
    "id",
    "title",
    "extensibility_scenario",
}


def load(
    path: Path,
    default_variation_instructions: Optional[List[VariationInstruction]] = None,
) -> Task:
    post = frontmatter.load(str(path))
    raw = dict(post.metadata)
    raw["description"] = post.content.strip()
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"Task {path} missing fields: {missing}")
    task_raw = raw.get("variation_instructions") or []
    if task_raw:
        instructions = [VariationInstruction.from_raw(i) for i in task_raw]
    else:
        instructions = list(default_variation_instructions or [])
    if len(instructions) != 3:
        raise ValueError(
            f"Task {path} must have exactly 3 variation_instructions "
            "(set them on the task or via default_variation_instructions in config.yaml)",
        )
    raw["variation_instructions"] = instructions
    data = {k: raw[k] for k in Task.__dataclass_fields__ if k in raw}
    return Task(**data)


def load_backlog(backlog_dir: Path, default_variation_instructions: Optional[List[VariationInstruction]] = None) -> List[Task]:
    files = sorted(backlog_dir.glob("*.md"))
    return [load(f, default_variation_instructions) for f in files]

