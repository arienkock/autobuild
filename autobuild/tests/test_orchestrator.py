"""Tests for orchestrator.run() task selection and stop-after-one behaviour."""

import json
import subprocess
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autobuild import orchestrator
from autobuild.models import AgentResult, Task, VariationInstruction, Workspace
from autobuild.workspace import ProvisionCtx


# ── shared fixtures ───────────────────────────────────────────────────────────

def _task(task_id: str, title: str = "A Task") -> Task:
    return Task(
        id=task_id,
        title=title,
        description="Do something.",
        variation_instructions=[
            VariationInstruction(prompt="a"),
            VariationInstruction(prompt="b"),
            VariationInstruction(prompt="c"),
        ],
        extensibility_scenario="N/A",
    )


TASKS = [_task("001-alpha"), _task("002-beta"), _task("003-gamma")]


@pytest.fixture
def fake_config():
    cfg = MagicMock()
    cfg.quality_gates = ["pytest"]
    cfg.src_dir = "src"
    return cfg


def _run(tmp_path: Path, tasks, *, run_all=False, force_task_id=None, fake_config):
    """Invoke orchestrator.run() with all heavy I/O patched out.

    Returns the mock that replaced ``_run_task`` so callers can assert
    which tasks were processed.
    """
    with (
        patch("autobuild.orchestrator.load_config", return_value=fake_config),
        patch("autobuild.orchestrator.load_backlog", return_value=tasks),
        patch("autobuild.orchestrator._run_task") as mock_run_task,
    ):
        orchestrator.run(
            repo_root=tmp_path,
            backlog_dir=tmp_path / "backlog",
            results_dir=tmp_path / "results",
            llm=MagicMock(),
            run_all=run_all,
            force_task_id=force_task_id,
        )
    return mock_run_task


def _make_results(results_dir: Path, task_id: str, status: str = "complete") -> None:
    """Write a dummy results.json so the task looks already built (or failed)."""
    out = results_dir / task_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"status": status, "agents": [], "verdict": None}))


# ── stop-after-one (default) ──────────────────────────────────────────────────


def test_stops_after_first_task_by_default(tmp_path, fake_config):
    mock = _run(tmp_path, TASKS, fake_config=fake_config)

    assert mock.call_count == 1
    built_task = mock.call_args[0][0]
    assert built_task.id == "001-alpha"


def test_processes_all_tasks_with_run_all(tmp_path, fake_config):
    mock = _run(tmp_path, TASKS, run_all=True, fake_config=fake_config)

    assert mock.call_count == 3
    built_ids = [call[0][0].id for call in mock.call_args_list]
    assert built_ids == ["001-alpha", "002-beta", "003-gamma"]


# ── skip already-built tasks ──────────────────────────────────────────────────


def test_skips_task_with_existing_results(tmp_path, fake_config):
    _make_results(tmp_path / "results", "001-alpha")

    mock = _run(tmp_path, TASKS, fake_config=fake_config)

    assert mock.call_count == 1
    built_task = mock.call_args[0][0]
    assert built_task.id == "002-beta"


def test_skips_all_built_tasks_with_run_all(tmp_path, fake_config):
    _make_results(tmp_path / "results", "001-alpha")
    _make_results(tmp_path / "results", "003-gamma")

    mock = _run(tmp_path, TASKS, run_all=True, fake_config=fake_config)

    assert mock.call_count == 1
    built_task = mock.call_args[0][0]
    assert built_task.id == "002-beta"


def test_no_tasks_run_when_all_already_built(tmp_path, fake_config):
    for task in TASKS:
        _make_results(tmp_path / "results", task.id)

    mock = _run(tmp_path, TASKS, run_all=True, fake_config=fake_config)

    mock.assert_not_called()


# ── --task <id> force-rebuild ─────────────────────────────────────────────────


def test_force_task_id_builds_only_that_task(tmp_path, fake_config):
    mock = _run(tmp_path, TASKS, force_task_id="002-beta", fake_config=fake_config)

    assert mock.call_count == 1
    built_task = mock.call_args[0][0]
    assert built_task.id == "002-beta"


def test_force_task_id_ignores_existing_results(tmp_path, fake_config):
    _make_results(tmp_path / "results", "002-beta")

    mock = _run(tmp_path, TASKS, force_task_id="002-beta", fake_config=fake_config)

    assert mock.call_count == 1
    built_task = mock.call_args[0][0]
    assert built_task.id == "002-beta"


def test_force_task_id_unknown_raises(tmp_path, fake_config):
    with pytest.raises(ValueError, match="999-missing"):
        _run(tmp_path, TASKS, force_task_id="999-missing", fake_config=fake_config)


# ── _apply_winner copies to src_dir, never to repo root ───────────────────────

_GIT_ID = ["-c", "user.email=test", "-c", "user.name=test"]


def _make_workspace(tmp_path: Path, src_dir: str = "src") -> Workspace:
    """Set up a minimal workspace with git rooted inside src_dir (as provision does)."""
    workspace_path = tmp_path / "variation-a"
    git_root = workspace_path / src_dir
    git_root.mkdir(parents=True)
    subprocess.run(["git", *_GIT_ID, "init"], cwd=git_root, check=True, capture_output=True)
    subprocess.run(["git", *_GIT_ID, "commit", "--allow-empty", "-m", "seed"],
                   cwd=git_root, check=True, capture_output=True)
    return Workspace(task_id="001", variation="a", path=workspace_path, src_dir=src_dir)


def test_apply_winner_copies_new_file_into_src_dir(tmp_path):
    """New files written inside the workspace src_dir land under repo_root/src_dir."""
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)

    workspace = _make_workspace(tmp_path / "workspaces")
    git_root = workspace.path / workspace.src_dir
    (git_root / "monteCarlo" / "index.js").parent.mkdir(parents=True)
    (git_root / "monteCarlo" / "index.js").write_text("export default {};")

    orchestrator._apply_winner(workspace, repo_root)

    expected = repo_root / "src" / "monteCarlo" / "index.js"
    assert expected.exists(), f"Expected file at {expected}"
    assert not (repo_root / "monteCarlo").exists(), \
        "File must not be copied to repo root — must land inside src_dir"


def test_apply_winner_modified_file_stays_in_src_dir(tmp_path):
    """Modified tracked files are also written under repo_root/src_dir, not repo root."""
    repo_root = tmp_path / "repo"
    (repo_root / "src" / "utils").mkdir(parents=True)
    (repo_root / "src" / "utils" / "helper.js").write_text("// original")

    workspace = _make_workspace(tmp_path / "workspaces")
    git_root = workspace.path / workspace.src_dir

    # Seed an existing file and commit it so git tracks it, then modify it
    (git_root / "utils").mkdir()
    (git_root / "utils" / "helper.js").write_text("// original")
    subprocess.run(["git", *_GIT_ID, "add", "."], cwd=git_root, check=True, capture_output=True)
    subprocess.run(["git", *_GIT_ID, "commit", "-m", "add helper"],
                   cwd=git_root, check=True, capture_output=True)
    (git_root / "utils" / "helper.js").write_text("// modified by LLM")

    orchestrator._apply_winner(workspace, repo_root)

    expected = repo_root / "src" / "utils" / "helper.js"
    assert expected.read_text() == "// modified by LLM"
    assert not (repo_root / "utils").exists(), \
        "Modified file must not appear at repo root — must stay inside src_dir"


def test_apply_winner_ignores_node_modules(tmp_path):
    """node_modules/ created in the workspace must never be copied to the repo."""
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)

    workspace = _make_workspace(tmp_path / "workspaces")
    git_root = workspace.path / workspace.src_dir

    # Simulate the LLM (or npm install) creating node_modules inside the workspace
    (git_root / "node_modules" / "some-pkg").mkdir(parents=True)
    (git_root / "node_modules" / "some-pkg" / "index.js").write_text("module.exports={};")
    (git_root / "index.js").write_text("const x = require('some-pkg');")

    # node_modules must be gitignored — as _ensure_gitignore guarantees
    (git_root / ".gitignore").write_text("node_modules/\n")

    orchestrator._apply_winner(workspace, repo_root)

    assert not (repo_root / "src" / "node_modules").exists(), \
        "node_modules must not be copied into the repo"
    assert (repo_root / "src" / "index.js").exists(), \
        "Legitimate source files must still be copied"


def test_apply_winner_works_when_repo_root_is_a_git_repo(tmp_path):
    """_apply_winner must work correctly even when repo_root is itself a git repo.

    The workspace git (in /tmp) and the outer repo git are completely separate;
    git commands in _apply_winner must operate only on the workspace git.
    """
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)

    # Make repo_root a git repo
    subprocess.run(["git", *_GIT_ID, "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", *_GIT_ID, "commit", "--allow-empty", "-m", "init"],
                   cwd=repo_root, check=True, capture_output=True)

    workspace = _make_workspace(tmp_path / "workspaces")
    git_root = workspace.path / workspace.src_dir
    (git_root / "app.js").write_text("console.log('hello');")

    orchestrator._apply_winner(workspace, repo_root)

    assert (repo_root / "src" / "app.js").exists(), \
        "Winner files must be copied even when repo_root is a git repo"


# ── _run_task: worker crash recovery (Gap 2) ──────────────────────────────────


def _make_future(result=None, exception=None) -> Future:
    f: Future = Future()
    if exception is not None:
        f.set_exception(exception)
    else:
        f.set_result(result)
    return f


def test_crashed_worker_does_not_abort_surviving_variations(tmp_path):
    """A worker process that raises must produce AgentResult(success=False) without
    aborting the other workers' results — the task should still find a winner.

    Previously, [f.result() for f in futures] would stop at the first exception,
    discarding all remaining results.
    """
    task = _task("001-alpha")
    ws_a = Workspace(task_id="001-alpha", variation="a", path=tmp_path / "a", src_dir="src")
    ws_b = Workspace(task_id="001-alpha", variation="b", path=tmp_path / "b", src_dir="src")
    ws_c = Workspace(task_id="001-alpha", variation="c", path=tmp_path / "c", src_dir="src")

    good_result = AgentResult(success=True, workspace=ws_b, reason="passed")
    fail_result = AgentResult(success=False, workspace=ws_c, reason="gates failed")

    mock_pool = MagicMock()
    mock_pool.__enter__ = MagicMock(return_value=mock_pool)
    mock_pool.__exit__ = MagicMock(return_value=False)
    mock_pool.submit.side_effect = [
        _make_future(exception=RuntimeError("worker process crashed")),
        _make_future(result=good_result),
        _make_future(result=fail_result),
    ]

    mock_rank = MagicMock()
    mock_rank.return_value = MagicMock(winner=ws_b, reasoning="b wins", comparisons=[])

    with (
        patch("autobuild.orchestrator.ProcessPoolExecutor", return_value=mock_pool),
        patch("autobuild.orchestrator.workspace.provision") as mock_provision,
        patch("autobuild.orchestrator.judge.rank", mock_rank),
        patch("autobuild.orchestrator._apply_winner"),
        patch("autobuild.orchestrator._write_results"),
        patch("autobuild.orchestrator.create_judge_llm", return_value=MagicMock()),
    ):
        mock_ctx = ProvisionCtx(workspaces=[ws_a, ws_b, ws_c], keep=False)
        mock_provision.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_provision.return_value.__exit__ = MagicMock(return_value=False)

        result = orchestrator._run_task(
            task, tmp_path, tmp_path / "results", MagicMock(), [], "src"
        )

    assert result is not None, "Task must produce a winner despite one crashed worker"
    assert result[0] == "b"


def test_all_workers_crashing_returns_none(tmp_path):
    """When every worker crashes, _run_task must return None gracefully (no winner)."""
    task = _task("001-alpha")
    ws_a = Workspace(task_id="001-alpha", variation="a", path=tmp_path / "a", src_dir="src")
    ws_b = Workspace(task_id="001-alpha", variation="b", path=tmp_path / "b", src_dir="src")
    ws_c = Workspace(task_id="001-alpha", variation="c", path=tmp_path / "c", src_dir="src")

    mock_pool = MagicMock()
    mock_pool.__enter__ = MagicMock(return_value=mock_pool)
    mock_pool.__exit__ = MagicMock(return_value=False)
    mock_pool.submit.side_effect = [
        _make_future(exception=RuntimeError("crash a")),
        _make_future(exception=RuntimeError("crash b")),
        _make_future(exception=RuntimeError("crash c")),
    ]

    with (
        patch("autobuild.orchestrator.ProcessPoolExecutor", return_value=mock_pool),
        patch("autobuild.orchestrator.workspace.provision") as mock_provision,
        patch("autobuild.orchestrator._write_results"),
        patch("autobuild.orchestrator.create_judge_llm", return_value=MagicMock()),
    ):
        mock_ctx = ProvisionCtx(workspaces=[ws_a, ws_b, ws_c], keep=False)
        mock_provision.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_provision.return_value.__exit__ = MagicMock(return_value=False)

        result = orchestrator._run_task(
            task, tmp_path, tmp_path / "results", MagicMock(), [], "src"
        )

    assert result is None


# ── failed-task retry behaviour ───────────────────────────────────────────────


def test_failed_task_is_not_skipped_on_next_run(tmp_path, fake_config):
    """A task whose results.json has status='failed' must be re-run, not skipped."""
    _make_results(tmp_path / "results", "001-alpha", status="failed")

    mock = _run(tmp_path, TASKS, run_all=True, fake_config=fake_config)

    built_ids = [call[0][0].id for call in mock.call_args_list]
    assert "001-alpha" in built_ids, "Failed task must be retried"


def test_complete_task_is_skipped_failed_task_is_not(tmp_path, fake_config):
    """status='complete' skips; status='failed' does not."""
    _make_results(tmp_path / "results", "001-alpha", status="complete")
    _make_results(tmp_path / "results", "002-beta", status="failed")

    mock = _run(tmp_path, TASKS, run_all=True, fake_config=fake_config)

    built_ids = [call[0][0].id for call in mock.call_args_list]
    assert "001-alpha" not in built_ids, "Completed task must be skipped"
    assert "002-beta" in built_ids, "Failed task must be retried"
    assert "003-gamma" in built_ids, "Unbuilt task must be run"


def test_all_workers_crashing_sets_ctx_keep_and_writes_failed_status(tmp_path):
    """Total failure must mark ctx.keep=True and write status='failed' so the
    workspace is preserved and the task is re-queued on the next run."""
    task = _task("001-alpha")
    ws_a = Workspace(task_id="001-alpha", variation="a", path=tmp_path / "a", src_dir="src")
    ws_b = Workspace(task_id="001-alpha", variation="b", path=tmp_path / "b", src_dir="src")
    ws_c = Workspace(task_id="001-alpha", variation="c", path=tmp_path / "c", src_dir="src")

    mock_pool = MagicMock()
    mock_pool.__enter__ = MagicMock(return_value=mock_pool)
    mock_pool.__exit__ = MagicMock(return_value=False)
    mock_pool.submit.side_effect = [
        _make_future(exception=RuntimeError("crash a")),
        _make_future(exception=RuntimeError("crash b")),
        _make_future(exception=RuntimeError("crash c")),
    ]

    mock_write = MagicMock()

    with (
        patch("autobuild.orchestrator.ProcessPoolExecutor", return_value=mock_pool),
        patch("autobuild.orchestrator.workspace.provision") as mock_provision,
        patch("autobuild.orchestrator._write_results", mock_write),
        patch("autobuild.orchestrator.create_judge_llm", return_value=MagicMock()),
    ):
        mock_ctx = ProvisionCtx(workspaces=[ws_a, ws_b, ws_c], keep=False)
        mock_provision.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_provision.return_value.__exit__ = MagicMock(return_value=False)

        result = orchestrator._run_task(
            task, tmp_path, tmp_path / "results", MagicMock(), [], "src"
        )

    assert result is None
    assert mock_ctx.keep is True, "ctx.keep must be True so the workspace is preserved"
    final_call_kwargs = mock_write.call_args_list[-1].kwargs
    assert final_call_kwargs.get("status") == "failed", (
        "_write_results must be called with status='failed' on total failure"
    )
