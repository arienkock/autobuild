"""Regression tests: error handling in agent.run() and _run_llm_gates().

These tests guard against regressions where exception catches are narrowed
or removed, causing child process/thread failures to propagate instead of
being converted to graceful AgentResult(success=False) outcomes.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from autobuild import agent
from autobuild.models import AgentResult, LlmGate, Task, VariationInstruction, Workspace


# ── shared helpers ────────────────────────────────────────────────────────────


def _task() -> Task:
    return Task(
        id="001",
        title="Test Task",
        description="Do something.",
        variation_instructions=[
            VariationInstruction(prompt="try A"),
            VariationInstruction(prompt="try B"),
            VariationInstruction(prompt="try C"),
        ],
    )


def _workspace(tmp_path: Path) -> Workspace:
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    return Workspace(task_id="001", variation="a", path=tmp_path, src_dir="src")


# ── agent.run: llm.implement() exception handling (Gap 1) ────────────────────


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("agent binary failed after retries"),
        FileNotFoundError(2, "agent binary 'my-agent' not found", "my-agent"),
        OSError("unexpected OS error"),
        PermissionError("permission denied"),
    ],
)
def test_run_returns_failed_result_when_implement_raises(tmp_path, exc):
    """agent.run() must return AgentResult(success=False) for any exception from llm.implement(),
    not propagate it to the caller (which would crash the ProcessPoolExecutor worker)."""
    task = _task()
    workspace = _workspace(tmp_path)
    llm = MagicMock()
    llm.implement.side_effect = exc

    result = agent.run(task, workspace, llm, quality_gates=[])

    assert isinstance(result, AgentResult)
    assert result.success is False


def test_run_exhausts_all_retries_on_repeated_implement_failure(tmp_path):
    """Each implement() exception consumes one retry; exactly MAX_RETRIES calls must be made."""
    task = _task()
    workspace = _workspace(tmp_path)
    llm = MagicMock()
    llm.implement.side_effect = RuntimeError("always fails")

    result = agent.run(task, workspace, llm, quality_gates=[])

    assert result.success is False
    assert llm.implement.call_count == agent.MAX_RETRIES


def test_run_succeeds_after_initial_implement_failure(tmp_path):
    """agent.run() must retry and succeed if implement() fails then passes."""
    task = _task()
    workspace = _workspace(tmp_path)
    llm = MagicMock()
    llm.implement.side_effect = [RuntimeError("first attempt fails"), None]

    result = agent.run(task, workspace, llm, quality_gates=[])

    assert result.success is True
    assert llm.implement.call_count == 2


# ── _run_llm_gates: _run_one exception handling (Gap 3) ──────────────────────


@pytest.mark.parametrize(
    "exc",
    [
        ValueError("bad JSON response"),
        RuntimeError("runtime failure in evaluate"),
        FileNotFoundError(2, "agent binary not found", "agent"),
        OSError("I/O error"),
        TimeoutError("evaluate timed out"),
        PermissionError("permission denied"),
    ],
)
def test_run_llm_gates_converts_any_exception_to_error_grade(tmp_path, exc):
    """_run_one must convert *any* exception from gate_llm.evaluate() into grade='ERROR'.

    Previously only ValueError and RuntimeError were caught; other types escaped
    and crashed the worker process.
    """
    task = _task()
    workspace = _workspace(tmp_path)
    gate = LlmGate(name="my-gate", prompt="Is the code good?")
    gate_llm = MagicMock()
    gate_llm.evaluate.side_effect = exc

    result = agent._run_llm_gates(task, workspace, [gate], gate_llm)

    assert result.passed is False
    assert len(result.outcomes) == 1
    assert result.outcomes[0]["grade"] == "ERROR"


def test_run_llm_gates_one_error_does_not_prevent_other_gates_running(tmp_path):
    """An error in one gate must not prevent the remaining gates from being evaluated."""
    task = _task()
    workspace = _workspace(tmp_path)
    gates = [
        LlmGate(name="crashing-gate", prompt="crash"),
        LlmGate(name="passing-gate", prompt="pass"),
    ]
    gate_llm = MagicMock()
    gate_llm.evaluate.side_effect = [
        OSError("something went wrong"),
        {"grade": "PASS", "reasoning": "looks good"},
    ]

    result = agent._run_llm_gates(task, workspace, gates, gate_llm)

    grades = {o["gate"]: o["grade"] for o in result.outcomes}
    assert grades["crashing-gate"] == "ERROR"
    assert grades["passing-gate"] == "PASS"
