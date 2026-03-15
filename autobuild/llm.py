"""LLM interface definitions and default factory.

The ``Llm`` protocol defines the two methods the rest of the system calls.
``create_default_llm(config)`` returns a ``CliLlm`` when config defines
agents and default_agent, otherwise ``NotConfiguredLlm``.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .models import Task

if TYPE_CHECKING:
    from .models import Config


class Llm(Protocol):
    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path, timeout: float | None = None) -> None: ...

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict: ...


class NotConfiguredLlm:
    """Placeholder LLM that raises a descriptive error on every call."""

    def __init__(self, reason: str | None = None) -> None:
        self._reason = reason or "No LLM has been configured for Autobuild."

    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path, timeout: float | None = None) -> None:
        raise RuntimeError(self._reason)

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict:
        raise RuntimeError(self._reason)


def create_default_llm(config: "Config | None" = None) -> Llm:
    """Return a ``CliLlm`` for config.default_agent when configured, else a stub."""
    if config and config.agents and config.default_agent and config.default_agent in config.agents:
        from .cli_llm import CliLlm  # noqa: PLC0415
        return CliLlm(config.agents[config.default_agent])
    return NotConfiguredLlm()


def create_judge_llm(config: "Config | None", default_llm: Llm) -> Llm:
    """Return the LLM to use for judging.

    If ``config`` specifies a ``judge_agent`` and/or ``judge_model`` those are
    resolved against the ``agents`` map (falling back to ``default_agent`` when
    only a model override is given).  When no judge-specific config is present
    ``default_llm`` is returned unchanged.
    """
    if not config:
        return default_llm

    agent_name = config.judge_agent
    model_override = config.judge_model

    if not agent_name and not model_override:
        return default_llm

    from dataclasses import replace as _dc_replace  # noqa: PLC0415

    from .cli_llm import CliLlm  # noqa: PLC0415

    resolved_agent = agent_name or config.default_agent
    if not resolved_agent or resolved_agent not in config.agents:
        return default_llm

    agent_cfg = config.agents[resolved_agent]
    if model_override:
        agent_cfg = _dc_replace(agent_cfg, model=model_override)
    return CliLlm(agent_cfg)

