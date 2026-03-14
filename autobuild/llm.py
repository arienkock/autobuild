"""LLM interface definitions and default factory.

The ``Llm`` protocol defines the two methods the rest of the system calls.
``create_default_llm(config)`` returns a ``CliLlm`` when config defines
agents and default_agent, otherwise a ``CursorLlm`` if ``cursor-agent`` is
available, else ``NotConfiguredLlm``.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .models import Task

if TYPE_CHECKING:
    from .models import Config


class Llm(Protocol):
    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path) -> None: ...

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict: ...


class NotConfiguredLlm:
    """Placeholder LLM that raises a descriptive error on every call."""

    def __init__(self, reason: str | None = None) -> None:
        self._reason = reason or "No LLM has been configured for Autobuild."

    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path) -> None:
        raise RuntimeError(self._reason)

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict:
        raise RuntimeError(self._reason)


def create_default_llm(config: "Config | None" = None) -> Llm:
    """Return a ``CliLlm`` for config.default_agent when configured, else ``CursorLlm`` or stub."""
    if config and config.agents and config.default_agent and config.default_agent in config.agents:
        from .cli_llm import CliLlm  # noqa: PLC0415
        return CliLlm(config.agents[config.default_agent])
    try:
        from .cursor_llm import CursorLlm  # noqa: PLC0415
        return CursorLlm()
    except FileNotFoundError as exc:
        return NotConfiguredLlm(str(exc))

