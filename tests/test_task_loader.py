"""Tests for task_loader.load() and load_backlog() default_variation_instructions."""

import pytest
import yaml

from autobuild.models import VariationInstruction
from autobuild.task_loader import load, load_backlog


def _vi(prompt: str) -> VariationInstruction:
    return VariationInstruction(prompt=prompt)


# Plain strings written into YAML frontmatter; the loader converts them to VariationInstruction.
_THREE_YAML = ["instruction a", "instruction b", "instruction c"]
_OTHER_THREE_YAML = ["x", "y", "z"]

# Expected VariationInstruction objects after loading.
_THREE = [_vi(s) for s in _THREE_YAML]
_OTHER_THREE = [_vi(s) for s in _OTHER_THREE_YAML]

_BASE = {
    "id": "001",
    "title": "T",
    "description": "D",
    "extensibility_scenario": "E",
}


def _write_task(path, data: dict):
    """Write a task file as markdown with YAML frontmatter (task_loader expects this)."""
    metadata = {k: v for k, v in data.items() if k != "description"}
    body = data.get("description", "")
    text = "---\n" + yaml.dump(metadata, default_flow_style=False, allow_unicode=True).strip() + "\n---\n" + body
    path.write_text(text)


# ── task has its own variation_instructions ───────────────────────────────────


def test_task_instructions_used_when_present(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": _THREE_YAML})
    task = load(f)
    assert task.variation_instructions == _THREE


def test_task_instructions_take_precedence_over_defaults(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": _THREE_YAML})
    task = load(f, default_variation_instructions=_OTHER_THREE)
    assert task.variation_instructions == _THREE


# ── task omits variation_instructions, defaults used ─────────────────────────


def test_defaults_used_when_task_omits_instructions(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, _BASE)
    task = load(f, default_variation_instructions=_THREE)
    assert task.variation_instructions == _THREE


def test_defaults_used_when_task_has_null_instructions(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": None})
    task = load(f, default_variation_instructions=_THREE)
    assert task.variation_instructions == _THREE


def test_defaults_used_when_task_has_empty_list(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": []})
    task = load(f, default_variation_instructions=_THREE)
    assert task.variation_instructions == _THREE


def test_dict_variation_instruction_parsed(tmp_path):
    f = tmp_path / "task.md"
    raw = [
        {"prompt": "do it inside-out"},
        {"agent": "claude", "model": "opus"},
        {"prompt": "TDD", "agent": "aider"},
    ]
    _write_task(f, {**_BASE, "variation_instructions": raw})
    task = load(f)
    assert task.variation_instructions == [
        VariationInstruction(prompt="do it inside-out"),
        VariationInstruction(agent="claude", model="opus"),
        VariationInstruction(prompt="TDD", agent="aider"),
    ]


def test_variation_instruction_requires_at_least_one_field(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": [{}, "b", "c"]})
    with pytest.raises(ValueError, match="at least one"):
        load(f)


# ── validation errors ─────────────────────────────────────────────────────────


def test_error_when_no_instructions_anywhere(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, _BASE)
    with pytest.raises(ValueError, match="variation_instructions"):
        load(f)


def test_error_when_wrong_count_in_task(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, {**_BASE, "variation_instructions": ["only one"]})
    with pytest.raises(ValueError, match="exactly 3"):
        load(f)


def test_error_hints_at_config_when_no_instructions(tmp_path):
    f = tmp_path / "task.md"
    _write_task(f, _BASE)
    with pytest.raises(ValueError, match="config.yaml"):
        load(f)


# ── load_backlog passes defaults to every task ────────────────────────────────


def test_load_backlog_applies_defaults_to_all_tasks(tmp_path):
    for i in range(1, 4):
        _write_task(tmp_path / f"00{i}.md", {**_BASE, "id": f"00{i}"})
    tasks = load_backlog(tmp_path, default_variation_instructions=_THREE)
    assert all(t.variation_instructions == _THREE for t in tasks)


def test_load_backlog_task_overrides_default(tmp_path):
    _write_task(tmp_path / "001.md", {**_BASE, "id": "001", "variation_instructions": _THREE_YAML})
    _write_task(tmp_path / "002.md", {**_BASE, "id": "002"})
    tasks = load_backlog(tmp_path, default_variation_instructions=_OTHER_THREE)
    assert tasks[0].variation_instructions == _THREE
    assert tasks[1].variation_instructions == _OTHER_THREE
