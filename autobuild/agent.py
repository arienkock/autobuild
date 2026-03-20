import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Protocol

from .models import AgentResult, LlmGate, Task, VariationInstruction, Workspace

MAX_RETRIES = 3


class LlmClient(Protocol):
    def implement(
        self,
        task: Task,
        instruction: str,
        context: str,
        workspace_path,
        timeout: Optional[float] = None,
    ) -> None: ...


class EvaluateLlm(Protocol):
    def evaluate(self, prompt: str, workspace_path: Path) -> dict: ...


def run(
    task: Task,
    workspace: Workspace,
    llm: LlmClient,
    quality_gates: list[str],
    llm_quality_gates: list[LlmGate] | None = None,
    gate_llm: EvaluateLlm | None = None,
    implementation_timeout: Optional[float] = None,
    retry_timeout: Optional[float] = None,
) -> AgentResult:
    tag = f"[{workspace.variation}]"
    vi = _variation_instruction(task, workspace.variation)
    context = ""
    cpu_start = time.process_time()

    for attempt in range(MAX_RETRIES):
        timeout = implementation_timeout if attempt == 0 else retry_timeout
        timeout_note = f" (timeout: {timeout}s)" if timeout is not None else ""
        print(f"  {tag} attempt {attempt + 1}/{MAX_RETRIES}: implementing…{timeout_note}", flush=True)
        try:
            llm.implement(task, vi.prompt or "", context, workspace.path / workspace.src_dir, timeout=timeout)
        except TimeoutError:
            print(f"  {tag} timed out after {timeout}s — {'retrying' if attempt < MAX_RETRIES - 1 else 'giving up'}", flush=True)
            context = _append_failure(context, f"Implementation timed out after {timeout}s")
            continue
        except Exception as exc:
            print(f"  {tag} implement failed: {exc} — {'retrying' if attempt < MAX_RETRIES - 1 else 'giving up'}", flush=True)
            context = _append_failure(context, str(exc))
            continue
        print(f"  {tag} running quality gates…", flush=True)
        gate_result = _run_gates(workspace, quality_gates)
        if gate_result.passed and llm_quality_gates and gate_llm is not None:
            print(f"  {tag} running LLM quality gates…", flush=True)
            gate_result = _run_llm_gates(task, workspace, llm_quality_gates, gate_llm, tag)
        if gate_result.passed:
            print(f"  {tag} gates passed ✓", flush=True)
            return AgentResult(
                success=True,
                workspace=workspace,
                reason=f"Passed on attempt {attempt + 1}",
                cpu_time_seconds=time.process_time() - cpu_start,
                llm_gate_results=gate_result.outcomes,
            )
        print(f"  {tag} gates failed — retrying", flush=True)
        context = _append_failure(context, gate_result.output)

    print(f"  {tag} all {MAX_RETRIES} attempts exhausted ✗", flush=True)
    return AgentResult(
        success=False,
        workspace=workspace,
        reason=f"Gates failed after {MAX_RETRIES} attempts",
        cpu_time_seconds=time.process_time() - cpu_start,
    )


def _variation_instruction(task: Task, variation: str) -> VariationInstruction:
    idx = {"a": 0, "b": 1, "c": 2}[variation]
    return task.variation_instructions[idx]


def _append_failure(context: str, gate_output: str) -> str:
    return context + f"\n\n### Previous attempt failed\n{gate_output}"


class _GateResult:
    def __init__(self, passed: bool, output: str, outcomes: list | None = None) -> None:
        self.passed = passed
        self.output = output
        self.outcomes: list[dict] = outcomes or []


def _run_gates(workspace: Workspace, quality_gates: list[str]) -> _GateResult:
    for cmd in quality_gates:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=workspace.path / workspace.src_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return _GateResult(passed=False, output=result.stdout + result.stderr)
    return _GateResult(passed=True, output="")


def _run_llm_gates(
    task: Task,
    workspace: Workspace,
    gates: list[LlmGate],
    gate_llm: "EvaluateLlm",
    tag: str = "",
) -> _GateResult:
    def _run_one(gate: LlmGate) -> tuple[LlmGate, dict]:
        prompt = gate.prompt.replace("{{task_description}}", task.description)
        try:
            result = gate_llm.evaluate(prompt, workspace.path / workspace.src_dir)
        except Exception as exc:
            return gate, {"gate": gate.name, "grade": "ERROR", "reasoning": str(exc)}
        return gate, {
            "gate": gate.name,
            "grade": str(result.get("grade", "")).upper(),
            "reasoning": result.get("reasoning", ""),
        }

    outcomes: list[dict] = []
    failures: list[str] = []

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_run_one, gate): gate for gate in gates}
        for future in as_completed(futures):
            gate, outcome = future.result()
            grade, reasoning = outcome["grade"], outcome["reasoning"]
            outcomes.append(outcome)
            label = "PASS ✓" if grade == "PASS" else "FAIL ✗" if grade == "FAIL" else "ERROR ✗"
            print(f"  {tag} gate '{gate.name}': {label}", flush=True)
            if grade != "PASS" and reasoning:
                print(f"  {tag}   → {reasoning}", flush=True)
            if grade != "PASS":
                verb = "errored" if grade == "ERROR" else "FAILED"
                failures.append(f"LLM quality gate '{gate.name}' {verb}:\n{reasoning}")

    if failures:
        return _GateResult(passed=False, output="\n\n".join(failures), outcomes=outcomes)
    return _GateResult(passed=True, output="", outcomes=outcomes)

