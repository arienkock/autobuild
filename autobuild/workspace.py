import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List

from .models import Task, Workspace

_VARIATIONS: Iterable[str] = ("a", "b", "c")

# Minimal git identity for the throwaway initial commit.
_GIT_ENV_ARGS = ["-c", "user.email=autobuild", "-c", "user.name=autobuild"]

# Patterns that must never be copied back into the real repo.
# node_modules: only excluded when a .gitignore in the git root says so;
# we guarantee one is always present rather than relying on the project's
# repo-root .gitignore (which is not copied into the workspace).
_WORKSPACE_GITIGNORE_ENTRIES = ["node_modules/"]


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
            # Git is rooted inside src_dir so that all tracked paths are
            # relative to src_dir. _apply_winner then copies them under
            # repo_root/src_dir, making it structurally impossible for
            # the winner's files to land outside src_dir in the real repo.
            _ensure_gitignore(dest / src_dir)
            _init_git(dest / src_dir)
            workspaces.append(
                Workspace(task_id=task.id, variation=v, path=dest, src_dir=src_dir),
            )
        yield workspaces
    finally:
        if keep:
            print(f"  Workspaces kept at: {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)


def _ensure_gitignore(path: Path) -> None:
    """Guarantee that the workspace .gitignore contains all required entries.

    Appends any missing entries to an existing .gitignore rather than
    overwriting it, so project-level ignore rules are preserved.
    """
    gitignore = path / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    missing = [e for e in _WORKSPACE_GITIGNORE_ENTRIES if e not in existing]
    if missing:
        with gitignore.open("a") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("\n".join(missing) + "\n")


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
