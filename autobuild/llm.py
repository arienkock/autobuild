"""LLM interface definitions and a simple stub implementation.

This module deliberately leaves the actual LLM wiring to the user of the
library; the rest of the system depends only on the interface here.
"""

from pathlib import Path
from typing import Protocol

from .models import Task


class Llm(Protocol):
    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path) -> None: ...

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict: ...


class NotConfiguredLlm:
    """Placeholder LLM that fails with a helpful error message."""

    def __init__(self, reason: str | None = None) -> None:
        self._reason = reason or "No LLM has been configured for Autobuild."

    def implement(self, task: Task, instruction: str, context: str, workspace_path: Path) -> None:
        raise RuntimeError(self._reason)

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict:
        raise RuntimeError(self._reason)


def create_default_llm() -> Llm:
    """Factory hook for wiring in a real LLM client.

    Replace this function in your own project or provide your own LLM instance
    to `orchestrator.run`.
    """

    return NotConfiguredLlm()

