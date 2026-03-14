"""Tests for config loading, focusing on default_variation_instructions."""

import pytest
import yaml

from autobuild.config import load_config
from autobuild.models import VariationInstruction


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
        {"agent": "claude"},
        {"model": "opus"},
    ]
    _write_config(tmp_path, {"default_variation_instructions": raw})
    config = load_config(tmp_path)
    assert config.default_variation_instructions == [
        VariationInstruction(prompt="inside-out"),
        VariationInstruction(agent="claude"),
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
