"""LLM interface definitions and default factory.

The ``Llm`` protocol defines the two methods the rest of the system calls.
``create_default_llm`` returns a ``CursorLlm`` if ``cursor-agent`` is
available, falling back to ``NotConfiguredLlm`` with a helpful error.
"""

from pathlib import Path
from typing import Protocol

from .models import Task


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


def create_default_llm() -> Llm:
    """Return a ``CursorLlm`` if ``cursor-agent`` is available, else a stub."""
    try:
        from .cursor_llm import CursorLlm  # noqa: PLC0415
        return CursorLlm()
    except FileNotFoundError as exc:
        return NotConfiguredLlm(str(exc))

