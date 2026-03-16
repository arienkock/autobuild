"""Regression tests: error handling in judge/engine.py rank().

These tests guard against regressions where future.result() is called without
error handling, causing a single failing comparison to abort the entire judge
run and leave no winner determined.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from autobuild.judge import engine
from autobuild.models import Task, VariationInstruction, Workspace


# ── shared helpers ────────────────────────────────────────────────────────────


def _task() -> Task:
    return Task(
        id="001",
        title="Test Task",
        description="Do something.",
        variation_instructions=[
            VariationInstruction(prompt="a"),
            VariationInstruction(prompt="b"),
            VariationInstruction(prompt="c"),
        ],
    )


def _workspace(tmp_path: Path, variation: str) -> Workspace:
    p = tmp_path / f"variation-{variation}"
    (p / "src").mkdir(parents=True, exist_ok=True)
    return Workspace(task_id="001", variation=variation, path=p, src_dir="src")


def _single_criterion(name: str = "quality") -> engine._Criterion:
    return engine._Criterion(name=name, prompt="Which is better?", weight=1.0)


# ── judge.rank: comparison failure handling (Gap 4) ──────────────────────────


def test_rank_skips_failed_comparison_and_still_produces_winner(tmp_path):
    """A failing comparison must be skipped; the remaining ones still determine a winner.

    Previously, any exception from _compare() propagated out of future.result()
    and aborted the entire judge run.
    """
    task = _task()
    ws_a = _workspace(tmp_path, "a")
    ws_b = _workspace(tmp_path, "b")

    llm = MagicMock()
    # Two criteria: first comparison crashes, second gives B the win.
    llm.compare.side_effect = [
        RuntimeError("LLM service unavailable"),
        {"winner": "B", "reasoning": "B is more readable"},
    ]

    criteria = [_single_criterion("quality"), _single_criterion("readability")]
    with patch.object(engine, "_load_criteria", return_value=criteria):
        result = engine.rank(task, [ws_a, ws_b], llm)

    assert result.winner in (ws_a, ws_b)


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("LLM call failed"),
        ValueError("extensibility_scenario missing"),
        OSError("I/O error"),
        TimeoutError("compare timed out"),
    ],
)
def test_rank_handles_various_comparison_exceptions(tmp_path, exc):
    """rank() must survive any exception type from _compare(), not just RuntimeError."""
    task = _task()
    ws_a = _workspace(tmp_path, "a")
    ws_b = _workspace(tmp_path, "b")

    llm = MagicMock()
    llm.compare.side_effect = exc

    with patch.object(engine, "_load_criteria", return_value=[_single_criterion()]):
        result = engine.rank(task, [ws_a, ws_b], llm)

    assert result.winner in (ws_a, ws_b)


def test_rank_succeeds_when_all_comparisons_fail(tmp_path):
    """If every comparison fails, rank() must still return a winner (tied at 0 points).

    Without error handling, all comparisons failing would abort the run entirely.
    """
    task = _task()
    ws_a = _workspace(tmp_path, "a")
    ws_b = _workspace(tmp_path, "b")

    llm = MagicMock()
    llm.compare.side_effect = RuntimeError("always crashes")

    with patch.object(engine, "_load_criteria", return_value=[_single_criterion()]):
        result = engine.rank(task, [ws_a, ws_b], llm)

    assert result.winner in (ws_a, ws_b)


def test_rank_scores_reflect_only_successful_comparisons(tmp_path):
    """Skipped comparisons must not affect scores; only successful ones count."""
    task = _task()
    ws_a = _workspace(tmp_path, "a")
    ws_b = _workspace(tmp_path, "b")

    llm = MagicMock()
    # Three criteria: first crashes, second gives A a point, third gives B a point.
    llm.compare.side_effect = [
        RuntimeError("crash"),
        {"winner": "A", "reasoning": "A wins this one"},
        {"winner": "B", "reasoning": "B wins this one"},
    ]

    criteria = [
        _single_criterion("q1"),
        _single_criterion("q2"),
        _single_criterion("q3"),
    ]
    with patch.object(engine, "_load_criteria", return_value=criteria):
        result = engine.rank(task, [ws_a, ws_b], llm)

    # Both A and B have 1 point each; a winner is still determined (tie-breaks to first by key)
    assert result.winner in (ws_a, ws_b)
    # The one crashed comparison must not appear in all_comparisons
    assert len(result.comparisons) == 2
