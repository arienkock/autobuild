import warnings
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter

from .models import Task, VariationInstruction

_REQUIRED = {
    "id",
    "title",
}


def load(
    path: Path,
    default_variation_instructions: Optional[List[VariationInstruction]] = None,
    agents: Optional[Dict] = None,
) -> Task:
    post = frontmatter.load(str(path))
    raw = dict(post.metadata)
    raw["description"] = post.content.strip()
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"Task {path} missing fields: {missing}")
    if not raw["description"]:
        warnings.warn(f"Task {path} has an empty description", stacklevel=2)
    task_raw = raw.get("variation_instructions") or []
    if task_raw:
        instructions = [VariationInstruction.from_raw(i) for i in task_raw]
        if agents is not None:
            for vi in instructions:
                if vi.agent and vi.agent not in agents:
                    raise ValueError(
                        f"Task {path}: variation_instructions references unknown agent '{vi.agent}' "
                        f"(known: {sorted(agents)})"
                    )
    else:
        instructions = list(default_variation_instructions or [])
    if not (1 <= len(instructions) <= 3):
        raise ValueError(
            f"Task {path} must have 1 to 3 variation_instructions "
            "(set them on the task or via default_variation_instructions in config.yaml)",
        )
    raw["variation_instructions"] = instructions
    data = {k: raw[k] for k in Task.__dataclass_fields__ if k in raw}
    return Task(**data)


def load_backlog(
    backlog_dir: Path,
    default_variation_instructions: Optional[List[VariationInstruction]] = None,
    agents: Optional[Dict] = None,
) -> List[Task]:
    if not backlog_dir.exists():
        raise FileNotFoundError(
            f"Backlog directory not found: {backlog_dir}"
        )
    files = sorted(backlog_dir.glob("*.md"))
    if not files:
        warnings.warn(f"No task files found in backlog directory: {backlog_dir}", stacklevel=2)
        return []
    tasks = [load(f, default_variation_instructions, agents=agents) for f in files]
    seen: dict[str, Path] = {}
    duplicates: list[str] = []
    for task, path in zip(tasks, files):
        if task.id in seen:
            duplicates.append(
                f"'{task.id}' appears in both {seen[task.id]} and {path}"
            )
        else:
            seen[task.id] = path
    if duplicates:
        raise ValueError(
            "Duplicate task IDs found in backlog:\n" + "\n".join(f"  • {d}" for d in duplicates)
        )
    return tasks

