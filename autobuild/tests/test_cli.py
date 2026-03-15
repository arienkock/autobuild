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
    main(["run"])
    assert mock_run.call_args.kwargs["run_all"] is False


def test_defaults_force_task_id_none(mock_run):
    main(["run"])
    assert mock_run.call_args.kwargs["force_task_id"] is None


# ── --all ─────────────────────────────────────────────────────────────────────


def test_all_flag_sets_run_all_true(mock_run):
    main(["run", "--all"])
    assert mock_run.call_args.kwargs["run_all"] is True


def test_without_all_flag_run_all_false(mock_run):
    main(["run"])
    assert mock_run.call_args.kwargs["run_all"] is False


# ── --task ────────────────────────────────────────────────────────────────────


def test_task_flag_sets_force_task_id(mock_run):
    main(["run", "--task", "002-beta"])
    assert mock_run.call_args.kwargs["force_task_id"] == "002-beta"


def test_task_flag_not_given_leaves_none(mock_run):
    main(["run"])
    assert mock_run.call_args.kwargs["force_task_id"] is None


# ── path arguments forwarded unchanged ───────────────────────────────────────


def test_repo_root_forwarded(mock_run, tmp_path):
    main(["--repo-root", str(tmp_path), "run"])
    assert mock_run.call_args.kwargs["repo_root"] == tmp_path


def test_results_dir_forwarded(mock_run, tmp_path):
    main(["run", "--results-dir", str(tmp_path)])
    assert mock_run.call_args.kwargs["results_dir"] == tmp_path


# ── init subcommand ───────────────────────────────────────────────────────────


def test_init_creates_autobuild_structure(tmp_path):
    main(["--repo-root", str(tmp_path), "init"])

    assert (tmp_path / ".autobuild").is_dir()
    assert (tmp_path / ".autobuild" / "config.yaml").is_file()
    assert (tmp_path / ".autobuild" / "backlog" / "001-example.md").is_file()
    assert (tmp_path / ".autobuild" / "gates").is_dir()
    assert (tmp_path / ".autobuild" / "criteria").is_dir()
    assert (tmp_path / ".autobuild" / "results").is_dir()
    assert (tmp_path / "src").is_dir()


def test_init_fails_if_already_initialized(tmp_path):
    main(["--repo-root", str(tmp_path), "init"])
    with pytest.raises(SystemExit):
        main(["--repo-root", str(tmp_path), "init"])


def test_init_force_overwrites_existing(tmp_path):
    main(["--repo-root", str(tmp_path), "init"])
    main(["--repo-root", str(tmp_path), "init", "--force"])
    assert (tmp_path / ".autobuild" / "config.yaml").is_file()
