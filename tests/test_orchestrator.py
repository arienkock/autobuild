"""Tests for orchestrator.run() task selection and stop-after-one behaviour."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autobuild import orchestrator
from autobuild.models import Task


# ── shared fixtures ───────────────────────────────────────────────────────────

def _task(task_id: str, title: str = "A Task") -> Task:
    return Task(
        id=task_id,
        title=title,
        description="Do something.",
        context_files=[],
        variation_instructions=["a", "b", "c"],
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


def _make_results(results_dir: Path, task_id: str) -> None:
    """Write a dummy results.json so the task looks already built."""
    out = results_dir / task_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"agents": [], "verdict": None}))


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


def test_force_task_id_unknown_runs_nothing(tmp_path, fake_config):
    mock = _run(tmp_path, TASKS, force_task_id="999-missing", fake_config=fake_config)

    mock.assert_not_called()
