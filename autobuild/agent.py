import subprocess
from typing import Protocol

from .models import AgentResult, Task, Workspace

MAX_RETRIES = 3


class LlmClient(Protocol):
    def implement(
        self,
        task: Task,
        instruction: str,
        context: str,
        workspace_path,
    ) -> None: ...


def run(
    task: Task,
    workspace: Workspace,
    llm: LlmClient,
    quality_gates: list[str],
) -> AgentResult:
    instruction = _variation_instruction(task, workspace.variation)
    context = _read_context(task, workspace)

    for attempt in range(MAX_RETRIES):
        llm.implement(task, instruction, context, workspace.path)
        gate_result = _run_gates(workspace, quality_gates)
        if gate_result.passed:
            return AgentResult(
                success=True,
                workspace=workspace,
                reason=f"Passed on attempt {attempt + 1}",
            )
        context = _append_failure(context, gate_result.output)

    return AgentResult(
        success=False,
        workspace=workspace,
        reason=f"Gates failed after {MAX_RETRIES} attempts",
    )


def _variation_instruction(task: Task, variation: str) -> str:
    idx = {"a": 0, "b": 1, "c": 2}[variation]
    return task.variation_instructions[idx]


def _read_context(task: Task, workspace: Workspace) -> str:
    parts: list[str] = []
    for rel in task.context_files or []:
        p = workspace.path / rel
        if p.exists():
            parts.append(f"### {rel}\n{p.read_text()}")
    return "\n\n".join(parts)


def _append_failure(context: str, gate_output: str) -> str:
    return context + f"\n\n### Previous attempt failed\n{gate_output}"


class _GateResult:
    def __init__(self, passed: bool, output: str) -> None:
        self.passed = passed
        self.output = output


def _run_gates(workspace: Workspace, quality_gates: list[str]) -> _GateResult:
    for cmd in quality_gates:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=workspace.path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return _GateResult(passed=False, output=result.stdout + result.stderr)
    return _GateResult(passed=True, output="")

