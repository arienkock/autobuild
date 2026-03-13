"""Tests for CLI argument parsing and forwarding to orchestrator.run()."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autobuild.cli import main


@pytest.fixture(autouse=True)
def _patch_llm():
    """Prevent real LLM construction in every test."""
    with patch("autobuild.cli.create_default_llm", return_value=MagicMock()):
        yield


@pytest.fixture
def mock_run():
    with patch("autobuild.cli.orchestrator.run") as m:
        yield m


# ── default behaviour ─────────────────────────────────────────────────────────


def test_defaults_run_all_false(mock_run):
    main([])
    assert mock_run.call_args.kwargs["run_all"] is False


def test_defaults_force_task_id_none(mock_run):
    main([])
    assert mock_run.call_args.kwargs["force_task_id"] is None


# ── --all ─────────────────────────────────────────────────────────────────────


def test_all_flag_sets_run_all_true(mock_run):
    main(["--all"])
    assert mock_run.call_args.kwargs["run_all"] is True


def test_without_all_flag_run_all_false(mock_run):
    main([])
    assert mock_run.call_args.kwargs["run_all"] is False


# ── --task ────────────────────────────────────────────────────────────────────


def test_task_flag_sets_force_task_id(mock_run):
    main(["--task", "002-beta"])
    assert mock_run.call_args.kwargs["force_task_id"] == "002-beta"


def test_task_flag_not_given_leaves_none(mock_run):
    main([])
    assert mock_run.call_args.kwargs["force_task_id"] is None


# ── path arguments forwarded unchanged ───────────────────────────────────────


def test_repo_root_forwarded(mock_run, tmp_path):
    main(["--repo-root", str(tmp_path)])
    assert mock_run.call_args.kwargs["repo_root"] == tmp_path


def test_results_dir_forwarded(mock_run, tmp_path):
    main(["--results-dir", str(tmp_path)])
    assert mock_run.call_args.kwargs["results_dir"] == tmp_path
