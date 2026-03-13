"""Tests for autobuild.cursor_llm.

Unit tests cover pure helpers (prompt builders, JSON parser, source collector)
without spawning any subprocess.

The integration test (marked ``integration``) actually invokes ``cursor-agent``
and requires a valid Cursor session.  Run it with::

    pytest -m integration tests/test_cursor_llm.py
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autobuild.cursor_llm import (
    CursorLlm,
    _build_compare_prompt,
    _build_implement_prompt,
    _collect_sources,
    _find_agent_bin,
    _parse_json_response,
    _run_agent,
)
from autobuild.models import Task

# ── fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_TASK = Task(
    id="001",
    title="Add greeting function",
    description="Create a function that returns a greeting string.",
    context_files=["src/greet.py"],
    variation_instructions=[
        "Use a plain function.",
        "Use a class with a __call__ method.",
        "Use a lambda stored in a module-level variable.",
    ],
    extensibility_scenario="What if we need to support multiple languages?",
)


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    (src / "greet.py").write_text("def greet(name: str) -> str:\n    return f'Hello, {name}'\n")
    (src / "utils.py").write_text("def noop() -> None:\n    pass\n")
    return tmp_path


# ── _build_implement_prompt ───────────────────────────────────────────────────


def test_implement_prompt_contains_title():
    prompt = _build_implement_prompt(SAMPLE_TASK, "Use a plain function.", "")
    assert "Add greeting function" in prompt


def test_implement_prompt_contains_instruction():
    instruction = "Use a plain function."
    prompt = _build_implement_prompt(SAMPLE_TASK, instruction, "")
    assert instruction in prompt


def test_implement_prompt_includes_context_when_present():
    context = "### src/greet.py\ndef greet(): pass"
    prompt = _build_implement_prompt(SAMPLE_TASK, "Do it.", context)
    assert context in prompt


def test_implement_prompt_omits_context_section_when_empty():
    prompt = _build_implement_prompt(SAMPLE_TASK, "Do it.", "")
    assert "Context:" not in prompt


# ── _build_compare_prompt ─────────────────────────────────────────────────────


def test_compare_prompt_contains_criterion(tmp_workspace: Path):
    criterion = "Which implementation has less complexity?"
    prompt = _build_compare_prompt(criterion, tmp_workspace, tmp_workspace)
    assert criterion in prompt


def test_compare_prompt_has_both_sections(tmp_workspace: Path):
    prompt = _build_compare_prompt("criterion", tmp_workspace, tmp_workspace)
    assert "## Implementation A" in prompt
    assert "## Implementation B" in prompt


def test_compare_prompt_requests_json(tmp_workspace: Path):
    prompt = _build_compare_prompt("criterion", tmp_workspace, tmp_workspace)
    assert '"winner"' in prompt


# ── _collect_sources ──────────────────────────────────────────────────────────


def test_collect_sources_finds_python_files(tmp_workspace: Path):
    listing = _collect_sources(tmp_workspace)
    assert "greet.py" in listing
    assert "utils.py" in listing


def test_collect_sources_truncates_large_files(tmp_workspace: Path):
    big_file = tmp_workspace / "src" / "big.py"
    big_file.write_text("x = 1\n" * 20_000)
    listing = _collect_sources(tmp_workspace, max_bytes=100)
    assert "truncated" in listing


def test_collect_sources_no_python_files(tmp_path: Path):
    listing = _collect_sources(tmp_path)
    assert "no Python source files found" in listing


def test_collect_sources_falls_back_to_root_without_src(tmp_path: Path):
    (tmp_path / "module.py").write_text("pass\n")
    listing = _collect_sources(tmp_path)
    assert "module.py" in listing


# ── _parse_json_response ──────────────────────────────────────────────────────


def test_parse_json_extracts_embedded_object():
    text = 'Some preamble.\n{"winner": "A", "reasoning": "A is simpler."}\nSome postamble.'
    result = _parse_json_response(text)
    assert result == {"winner": "A", "reasoning": "A is simpler."}


def test_parse_json_raises_on_missing_object():
    with pytest.raises(ValueError, match="No JSON object"):
        _parse_json_response("No JSON here.")


# ── _run_agent (unit, mocked subprocess) ─────────────────────────────────────


def test_run_agent_calls_correct_command(tmp_path: Path):
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        _run_agent("hello", bin="/usr/bin/agent", workspace=tmp_path)

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/usr/bin/agent"
    assert "--print" in cmd
    assert "--force" in cmd
    assert "--workspace" in cmd
    assert str(tmp_path) in cmd
    assert "hello" in cmd


def test_run_agent_raises_on_nonzero_exit():
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="oops")
        with pytest.raises(RuntimeError, match="cursor-agent failed"):
            _run_agent("prompt", bin="/usr/bin/agent")


def test_run_agent_passes_model_flag():
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_agent("prompt", bin="/usr/bin/agent", model="claude-3-5-sonnet")

    cmd = mock_run.call_args[0][0]
    assert "--model" in cmd
    assert "claude-3-5-sonnet" in cmd


def test_run_agent_no_force_flag_when_disabled():
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_agent("prompt", bin="/usr/bin/agent", force=False)

    cmd = mock_run.call_args[0][0]
    assert "--force" not in cmd


def test_run_agent_passes_api_key():
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_agent("prompt", bin="/usr/bin/agent", api_key="sk-test-key")

    cmd = mock_run.call_args[0][0]
    assert "--api-key" in cmd
    assert "sk-test-key" in cmd


def test_run_agent_omits_api_key_when_not_set():
    with patch("autobuild.cursor_llm.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_agent("prompt", bin="/usr/bin/agent", api_key=None)

    cmd = mock_run.call_args[0][0]
    assert "--api-key" not in cmd


# ── CursorLlm.implement (unit, mocked _run_agent) ────────────────────────────


def test_cursor_llm_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("CURSOR_API_KEY", "env-key-abc")
    with patch("autobuild.cursor_llm._find_agent_bin", return_value="/usr/bin/agent"):
        llm = CursorLlm()
    assert llm._api_key == "env-key-abc"


def test_cursor_llm_explicit_api_key_takes_precedence(monkeypatch):
    monkeypatch.setenv("CURSOR_API_KEY", "env-key")
    with patch("autobuild.cursor_llm._find_agent_bin", return_value="/usr/bin/agent"):
        llm = CursorLlm(api_key="explicit-key")
    assert llm._api_key == "explicit-key"


def test_cursor_llm_implement_invokes_run_agent(tmp_workspace: Path):
    with patch("autobuild.cursor_llm._run_agent") as mock_run:
        llm = CursorLlm(agent_bin="/usr/bin/agent")
        llm.implement(SAMPLE_TASK, "Use a plain function.", "", tmp_workspace)

    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args.kwargs
    assert call_kwargs["workspace"] == tmp_workspace
    assert call_kwargs["force"] is True


def test_cursor_llm_compare_parses_response(tmp_workspace: Path):
    response = '{"winner": "B", "reasoning": "B is cleaner."}'
    with patch("autobuild.cursor_llm._run_agent", return_value=response):
        llm = CursorLlm(agent_bin="/usr/bin/agent")
        result = llm.compare("Which is simpler?", tmp_workspace, tmp_workspace)

    assert result["winner"] == "B"
    assert "cleaner" in result["reasoning"]


# ── integration ───────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_implement_writes_file(tmp_path: Path):
    """Calls the real cursor-agent to create a simple Python file."""
    src = tmp_path / "src"
    src.mkdir()
    task = Task(
        id="test-001",
        title="Hello world module",
        description="Create src/hello.py with a hello() function that returns 'Hello, world!'",
        context_files=[],
        variation_instructions=["Implement it.", "Implement it.", "Implement it."],
        extensibility_scenario="N/A",
    )
    llm = CursorLlm()
    llm.implement(task, "Implement it.", "", tmp_path)

    py_files = list(tmp_path.rglob("*.py"))
    assert py_files, "Expected at least one Python file to be written"
