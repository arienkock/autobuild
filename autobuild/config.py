import warnings
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import AgentConfig, Config, LlmGate, VariationInstruction

_DEFAULT_QUALITY_GATES = ["python -m pytest --tb=short -q"]
_DEFAULT_SRC_DIR = "src"

_KNOWN_KEYS = {
    "src_dir",
    "quality_gates",
    "llm_quality_gates",
    "default_variation_instructions",
    "agents",
    "default_agent",
    "judge",
    "timeouts",
    "backlog-dir",
    "results-dir",
}


_GATES_DIR_NAME = "gates"
_BUILTIN_GATES_DIR = Path(__file__).parent / _GATES_DIR_NAME


def _parse_prompt_from_md(text: str) -> str:
    """Strip YAML frontmatter and return the body of a markdown gate/criterion file."""
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else text.strip()


def _load_llm_gates(names: List[str], repo_root: Path) -> List[LlmGate]:
    project_gates_dir = repo_root / ".autobuild" / _GATES_DIR_NAME
    gates: List[LlmGate] = []
    for name in names:
        project_path = project_gates_dir / f"{name}.md"
        builtin_path = _BUILTIN_GATES_DIR / f"{name}.md"
        if project_path.exists():
            path = project_path
        elif builtin_path.exists():
            path = builtin_path
        else:
            warnings.warn(
                f"llm_quality_gates: gate '{name}' not found in '{project_gates_dir}' or built-in gates — skipping",
                stacklevel=5,
            )
            continue
        prompt = _parse_prompt_from_md(path.read_text())
        gates.append(LlmGate(name=name, prompt=prompt))
    return gates


def _parse_agents(raw: Optional[dict]) -> Dict[str, AgentConfig]:
    if not raw:
        return {}
    result = {}
    for name, agent_data in raw.items():
        if isinstance(agent_data, dict):
            result[name] = AgentConfig(
                implement_command=agent_data.get("implement_command", ""),
                compare_command=agent_data.get("compare_command", ""),
                model=agent_data.get("model", ""),
            )
    return result


def _parse_variation_instructions(raw: Optional[List]) -> List[VariationInstruction]:
    if not raw:
        return []
    return [VariationInstruction.from_raw(item) for item in raw]


def _parse_timeout(value) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _validate_config(config: Config, repo_root: Path, raw_data: dict) -> None:
    errors: list[str] = []

    unknown = set(raw_data.keys()) - _KNOWN_KEYS
    for key in sorted(unknown):
        warnings.warn(
            f"config.yaml: unknown key '{key}' (ignored) — possible typo?",
            stacklevel=4,
        )

    if not config.quality_gates:
        warnings.warn(
            "config.yaml: quality_gates is empty — all agent attempts will pass trivially",
            stacklevel=4,
        )

    src_path = repo_root / config.src_dir
    if not src_path.exists():
        warnings.warn(
            f"config.yaml: src_dir '{config.src_dir}' does not exist under {repo_root}",
            stacklevel=4,
        )

    if config.default_agent and config.default_agent not in config.agents:
        errors.append(
            f"default_agent '{config.default_agent}' is not defined under agents "
            f"(known: {sorted(config.agents)})"
        )

    if config.judge_agent and config.judge_agent not in config.agents:
        errors.append(
            f"judge.agent '{config.judge_agent}' is not defined under agents "
            f"(known: {sorted(config.agents)})"
        )

    for name, agent_cfg in config.agents.items():
        if not agent_cfg.implement_command:
            errors.append(f"agents.{name}: implement_command must not be empty")
        if not agent_cfg.compare_command:
            errors.append(f"agents.{name}: compare_command must not be empty")

    for i, vi in enumerate(config.default_variation_instructions):
        if vi.agent and vi.agent not in config.agents:
            errors.append(
                f"default_variation_instructions[{i}]: agent '{vi.agent}' is not defined under agents "
                f"(known: {sorted(config.agents)})"
            )

    if config.implementation_timeout is not None and config.implementation_timeout <= 0:
        errors.append(
            f"timeouts.implementation must be a positive number, got {config.implementation_timeout}"
        )

    if config.retry_timeout is not None and config.retry_timeout <= 0:
        errors.append(
            f"timeouts.retry must be a positive number, got {config.retry_timeout}"
        )

    if errors:
        raise ValueError("Invalid autobuild configuration:\n" + "\n".join(f"  • {e}" for e in errors))


def load_config(repo_root: Path) -> Config:
    path = repo_root / ".autobuild" / "config.yaml"
    data: dict = yaml.safe_load(path.read_text()) if path.exists() else {}
    agents_raw = data.get("agents")
    judge_raw = data.get("judge") or {}
    timeouts_raw = data.get("timeouts") or {}
    llm_gates_names: List[str] = data.get("llm_quality_gates") or []
    config = Config(
        quality_gates=data.get("quality_gates", _DEFAULT_QUALITY_GATES),
        src_dir=data.get("src_dir", _DEFAULT_SRC_DIR),
        default_variation_instructions=_parse_variation_instructions(
            data.get("default_variation_instructions")
        ),
        agents=_parse_agents(agents_raw),
        default_agent=data.get("default_agent"),
        judge_agent=judge_raw.get("agent") if isinstance(judge_raw, dict) else None,
        judge_model=judge_raw.get("model") if isinstance(judge_raw, dict) else None,
        implementation_timeout=_parse_timeout(timeouts_raw.get("implementation") if isinstance(timeouts_raw, dict) else None),
        retry_timeout=_parse_timeout(timeouts_raw.get("retry") if isinstance(timeouts_raw, dict) else None),
        llm_quality_gates=_load_llm_gates(llm_gates_names, repo_root),
    )
    _validate_config(config, repo_root, data)
    return config
