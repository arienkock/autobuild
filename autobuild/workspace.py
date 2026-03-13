import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List

from .models import Task, Workspace

_VARIATIONS: Iterable[str] = ("a", "b", "c")


@contextmanager
def provision(
    task: Task,
    repo_root: Path,
    tmp_root: Path = Path("/tmp/autobuild"),
) -> List[Workspace]:
    """Yield three workspaces for a task and clean them up on exit."""
    base = tmp_root / task.id
    base.mkdir(parents=True, exist_ok=True)
    workspaces: List[Workspace] = []
    try:
        for v in _VARIATIONS:
            dest = base / f"variation-{v}"
            shutil.copytree(repo_root, dest, dirs_exist_ok=True)
            workspaces.append(
                Workspace(task_id=task.id, variation=v, path=dest),
            )
        yield workspaces
    finally:
        shutil.rmtree(base, ignore_errors=True)

