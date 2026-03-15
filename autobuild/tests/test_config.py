"""Tests for config loading, focusing on default_variation_instructions."""

import pytest
import yaml

from autobuild.config import load_config
from autobuild.models import VariationInstruction


_AGENT = {
    "implement_command": "agent --run {prompt}",
    "compare_command": "agent --compare {prompt}",
    "model": "gpt-4",
}


_THREE_YAML = ["instruction a", "instruction b", "instruction c"]
_THREE = [VariationInstruction(prompt=s) for s in _THREE_YAML]


def _write_config(tmp_path, data: dict):
    cfg = tmp_path / ".autobuild" / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(yaml.dump(data))
    return tmp_path


# ── default_variation_instructions absent ─────────────────────────────────────


def test_default_variation_instructions_empty_when_absent(tmp_path):
    _write_config(tmp_path, {"quality_gates": ["pytest"]})
    config = load_config(tmp_path)
    assert config.default_variation_instructions == []


def test_default_variation_instructions_empty_when_no_config_file(tmp_path):
    config = load_config(tmp_path)
    assert config.default_variation_instructions == []


# ── default_variation_instructions present ────────────────────────────────────


def test_default_variation_instructions_loaded(tmp_path):
    _write_config(tmp_path, {"default_variation_instructions": _THREE_YAML})
    config = load_config(tmp_path)
    assert config.default_variation_instructions == _THREE


def test_default_variation_instructions_as_dicts(tmp_path):
    raw = [
        {"prompt": "inside-out"},
        {"prompt": "outside-in", "model": "gpt-4"},
        {"model": "opus"},
    ]
    _write_config(tmp_path, {"default_variation_instructions": raw})
    config = load_config(tmp_path)
    assert config.default_variation_instructions == [
        VariationInstruction(prompt="inside-out"),
        VariationInstruction(prompt="outside-in", model="gpt-4"),
        VariationInstruction(model="opus"),
    ]


def test_other_fields_unaffected(tmp_path):
    _write_config(tmp_path, {
        "quality_gates": ["npm test"],
        "src_dir": "frontend",
        "default_variation_instructions": _THREE_YAML,
    })
    config = load_config(tmp_path)
    assert config.quality_gates == ["npm test"]
    assert config.src_dir == "frontend"


# ── validate_config: agent name checks ───────────────────────────────────────


def test_error_when_default_agent_not_in_agents(tmp_path):
    _write_config(tmp_path, {"default_agent": "ghost", "agents": {"real": _AGENT}})
    with pytest.raises(ValueError, match="default_agent.*ghost"):
        load_config(tmp_path)


def test_error_when_judge_agent_not_in_agents(tmp_path):
    _write_config(tmp_path, {
        "agents": {"real": _AGENT},
        "judge": {"agent": "phantom"},
    })
    with pytest.raises(ValueError, match="judge.agent.*phantom"):
        load_config(tmp_path)


def test_error_when_variation_instruction_agent_not_in_agents(tmp_path):
    _write_config(tmp_path, {
        "agents": {"real": _AGENT},
        "default_variation_instructions": [
            {"agent": "real"},
            {"agent": "missing"},
            {"prompt": "plain"},
        ],
    })
    with pytest.raises(ValueError, match="missing"):
        load_config(tmp_path)


# ── validate_config: agent command checks ────────────────────────────────────


def test_error_when_implement_command_is_empty(tmp_path):
    bad = {**_AGENT, "implement_command": ""}
    _write_config(tmp_path, {"agents": {"bad": bad}})
    with pytest.raises(ValueError, match="implement_command"):
        load_config(tmp_path)


def test_error_when_compare_command_is_empty(tmp_path):
    bad = {**_AGENT, "compare_command": ""}
    _write_config(tmp_path, {"agents": {"bad": bad}})
    with pytest.raises(ValueError, match="compare_command"):
        load_config(tmp_path)


# ── validate_config: timeout checks ──────────────────────────────────────────


def test_error_when_implementation_timeout_is_zero(tmp_path):
    _write_config(tmp_path, {"timeouts": {"implementation": 0}})
    with pytest.raises(ValueError, match="timeouts.implementation"):
        load_config(tmp_path)


def test_error_when_retry_timeout_is_negative(tmp_path):
    _write_config(tmp_path, {"timeouts": {"retry": -5}})
    with pytest.raises(ValueError, match="timeouts.retry"):
        load_config(tmp_path)


# ── validate_config: unknown top-level keys ───────────────────────────────────


def test_warning_for_unknown_top_level_key(tmp_path, recwarn):
    _write_config(tmp_path, {"quality_gate": ["npm test"]})  # typo — missing 's'
    load_config(tmp_path)
    messages = [str(w.message) for w in recwarn.list]
    assert any("quality_gate" in m for m in messages)


# ── validate_config: empty quality_gates warning ─────────────────────────────


def test_warning_when_quality_gates_is_empty(tmp_path, recwarn):
    _write_config(tmp_path, {"quality_gates": []})
    load_config(tmp_path)
    messages = [str(w.message) for w in recwarn.list]
    assert any("quality_gates" in m for m in messages)


# ── validate_config: missing src_dir warning ─────────────────────────────────


def test_warning_when_src_dir_does_not_exist(tmp_path, recwarn):
    _write_config(tmp_path, {"src_dir": "nonexistent"})
    load_config(tmp_path)
    messages = [str(w.message) for w in recwarn.list]
    assert any("src_dir" in m for m in messages)


def test_no_warning_when_src_dir_exists(tmp_path, recwarn):
    (tmp_path / "mysrc").mkdir()
    _write_config(tmp_path, {"src_dir": "mysrc"})
    load_config(tmp_path)
    messages = [str(w.message) for w in recwarn.list]
    assert not any("src_dir" in m for m in messages)


# ── validate_config: valid config passes without error ───────────────────────


def test_valid_full_config_loads_without_error(tmp_path):
    (tmp_path / "src").mkdir()
    _write_config(tmp_path, {
        "src_dir": "src",
        "quality_gates": ["pytest"],
        "agents": {"myagent": _AGENT},
        "default_agent": "myagent",
        "default_variation_instructions": [
            {"agent": "myagent"},
            {"agent": "myagent", "model": "gpt-3"},
            {"prompt": "use TDD"},
        ],
        "timeouts": {"implementation": 300, "retry": 120},
    })
    config = load_config(tmp_path)
    assert config.default_agent == "myagent"
