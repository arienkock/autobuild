import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List

from .models import Task, Workspace

_VARIATIONS: Iterable[str] = ("a", "b", "c")

# Minimal git identity for the throwaway initial commit.
_GIT_ENV_ARGS = ["-c", "user.email=autobuild", "-c", "user.name=autobuild"]


@contextmanager
def provision(
    task: Task,
    repo_root: Path,
    src_dir: str,
    tmp_root: Path = Path("/tmp/autobuild"),
    keep: bool = False,
) -> List[Workspace]:
    """Yield three isolated workspaces for a task and clean them up on exit.

    Each workspace contains only *src_dir* from *repo_root*, placed at the
    same relative path inside a fresh git repository.  The initial commit
    records the baseline so that ``git diff HEAD`` inside the workspace shows
    exactly what the LLM changed.

    Pass ``keep=True`` to skip cleanup so the workspaces can be inspected
    after the run completes.
    """
    base = tmp_root / task.id
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True, exist_ok=True)
    workspaces: List[Workspace] = []
    try:
        for v in _VARIATIONS:
            dest = base / f"variation-{v}"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(repo_root / src_dir, dest / src_dir, dirs_exist_ok=True)
            _init_git(dest)
            workspaces.append(
                Workspace(task_id=task.id, variation=v, path=dest, src_dir=src_dir),
            )
        yield workspaces
    finally:
        if keep:
            print(f"  Workspaces kept at: {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)


def _init_git(path: Path) -> None:
    """Initialise a throw-away git repo and commit the seed state."""
    subprocess.run(["git", *_GIT_ENV_ARGS, "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", *_GIT_ENV_ARGS, "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", *_GIT_ENV_ARGS, "commit", "--allow-empty", "-m", "seed"],
        cwd=path,
        check=True,
        capture_output=True,
    )
