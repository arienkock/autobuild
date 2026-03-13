# Autobuild

Autobuild is an agentic development framework that automates the implementation and evaluation of software features. Given a backlog of manually authored tasks, it spins up three parallel agents — each pursuing a different implementation strategy — and selects the best result through a tournament-style design review. Quality gates (tests, coverage, lint) determine whether an implementation is valid; a configurable set of LLM-judged criteria — weighted toward simplicity, modularity, and extensibility — determine which valid implementation wins. The winning implementation is committed back to the repository, and the loop continues.

## Project Structure

```
autobuild/
  __init__.py
  models.py          ← all dataclasses/types (shared, no deps)
  task_loader.py     ← reads backlog YAML into Task
  workspace.py       ← filesystem copy lifecycle
  agent.py           ← implement + gate loop
  judge/
    __init__.py
    engine.py        ← generic pairwise tournament
    criteria/        ← .md files, each a criterion
      simplicity.md
      modularity.md
      extensibility.md
  orchestrator.py    ← top-level loop
  cli.py             ← entry point

backlog/             ← your task YAML files
  001-example.yaml
.autobuild/
  results/           ← archived per task
  config.yaml
```

---

## `models.py` — all shared types

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class Task:
    id: str
    title: str
    description: str
    variation_instructions: list[str]
    extensibility_scenario: str

@dataclass(frozen=True)
class Workspace:
    task_id: str
    variation: str          # "a", "b", "c"
    path: Path

@dataclass(frozen=True)
class AgentResult:
    success: bool
    workspace: Workspace
    reason: str             # failure cause or completion summary

@dataclass(frozen=True)
class Comparison:
    criterion: str
    winner: str             # "A", "B", or "tie"
    reasoning: str

@dataclass(frozen=True)
class JudgeResult:
    winner: Workspace
    comparisons: list[Comparison]
    reasoning: str          # human-readable summary of tournament
```

---

## `task_loader.py`

```python
from pathlib import Path
import yaml
from .models import Task

_REQUIRED = {"id", "title", "description",
             "variation_instructions", "extensibility_scenario"}

def load(path: Path) -> Task:
    raw = yaml.safe_load(path.read_text())
    missing = _REQUIRED - raw.keys()
    if missing:
        raise ValueError(f"Task {path} missing fields: {missing}")
    if len(raw["variation_instructions"]) != 3:
        raise ValueError(f"Task {path} must have exactly 3 variation_instructions")
    return Task(**{k: raw[k] for k in Task.__dataclass_fields__ if k in raw})

def load_backlog(backlog_dir: Path) -> list[Task]:
    files = sorted(backlog_dir.glob("*.yaml"))
    return [load(f) for f in files]
```

---

## `workspace.py`

```python
import shutil
from contextlib import contextmanager
from pathlib import Path
from .models import Task, Workspace

_VARIATIONS = ["a", "b", "c"]

@contextmanager
def provision(task: Task, repo_root: Path, tmp_root: Path = Path("/tmp/autobuild")):
    """Yields three Workspaces, cleans up on exit."""
    base = tmp_root / task.id
    base.mkdir(parents=True, exist_ok=True)
    workspaces = []
    try:
        for v in _VARIATIONS:
            dest = base / f"variation-{v}"
            shutil.copytree(repo_root, dest, dirs_exist_ok=True)
            workspaces.append(Workspace(task_id=task.id, variation=v, path=dest))
        yield workspaces
    finally:
        shutil.rmtree(base, ignore_errors=True)
```

---

## `agent.py`

```python
import subprocess
from .models import Task, Workspace, AgentResult

MAX_RETRIES = 3

def run(task: Task, workspace: Workspace, llm) -> AgentResult:
    instruction = _variation_instruction(task, workspace.variation)
    context = _read_context(task, workspace)
    
    for attempt in range(MAX_RETRIES):
        code = llm.implement(task, instruction, context, workspace.path)
        gate_result = _run_gates(workspace)
        if gate_result.passed:
            return AgentResult(success=True, workspace=workspace,
                               reason=f"Passed on attempt {attempt + 1}")
        context = _append_failure(context, gate_result.output)

    return AgentResult(success=False, workspace=workspace,
                       reason=f"Gates failed after {MAX_RETRIES} attempts")

# ── private ──────────────────────────────────────────────────────────────────

def _variation_instruction(task: Task, variation: str) -> str:
    idx = {"a": 0, "b": 1, "c": 2}[variation]
    return task.variation_instructions[idx]

def _append_failure(context: str, gate_output: str) -> str:
    return context + f"\n\n### Previous attempt failed\n{gate_output}"

class _GateResult:
    def __init__(self, passed: bool, output: str):
        self.passed = passed
        self.output = output

def _run_gates(workspace: Workspace) -> _GateResult:
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q"],
        cwd=workspace.path,
        capture_output=True, text=True
    )
    return _GateResult(passed=result.returncode == 0,
                       output=result.stdout + result.stderr)
```

---

## `judge/engine.py`

```python
from pathlib import Path
from itertools import combinations
from .models import Workspace, Task, Comparison, JudgeResult

_CRITERIA_DIR = Path(__file__).parent / "criteria"

def rank(task: Task, workspaces: list[Workspace], llm) -> JudgeResult:
    criteria = _load_criteria()
    all_comparisons = []

    # pairwise tournament across all criteria
    scores = {w.variation: 0 for w in workspaces}
    for a, b in combinations(workspaces, 2):
        for criterion in criteria:
            comparison = _compare(task, a, b, criterion, llm)
            all_comparisons.append(comparison)
            if comparison.winner == "A":
                scores[a.variation] += criterion.weight
            elif comparison.winner == "B":
                scores[b.variation] += criterion.weight

    winner_variation = max(scores, key=lambda v: scores[v])
    winner = next(w for w in workspaces if w.variation == winner_variation)

    return JudgeResult(
        winner=winner,
        comparisons=all_comparisons,
        reasoning=_summarise(scores, all_comparisons)
    )

# ── private ──────────────────────────────────────────────────────────────────

class _Criterion:
    def __init__(self, name: str, prompt: str, weight: float):
        self.name = name
        self.prompt = prompt
        self.weight = weight

def _load_criteria() -> list[_Criterion]:
    criteria = []
    for path in sorted(_CRITERIA_DIR.glob("*.md")):
        text = path.read_text()
        weight = _parse_weight(text)
        prompt = _parse_prompt(text)
        criteria.append(_Criterion(name=path.stem, prompt=prompt, weight=weight))
    return criteria

def _parse_weight(text: str) -> float:
    for line in text.splitlines():
        if line.startswith("weight:"):
            return float(line.split(":")[1].strip())
    return 1.0

def _parse_prompt(text: str) -> str:
    # everything after the frontmatter block
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else text.strip()

def _compare(task: Task, a: Workspace, b: Workspace,
             criterion: _Criterion, llm) -> Comparison:
    prompt = criterion.prompt
    if "{{extensibility_scenario}}" in prompt:
        prompt = prompt.replace("{{extensibility_scenario}}",
                                task.extensibility_scenario)
    result = llm.compare(prompt, a.path, b.path)
    return Comparison(criterion=criterion.name,
                      winner=result["winner"],
                      reasoning=result["reasoning"])

def _summarise(scores: dict, comparisons: list[Comparison]) -> str:
    lines = [f"  {v}: {s:.1f} points" for v, s in sorted(
        scores.items(), key=lambda x: -x[1])]
    return "Tournament scores:\n" + "\n".join(lines)
```

---

## A sample criterion file

```markdown
---
weight: 1.0
---

Given two implementations of the same feature (A and B), which has less
incidental complexity?

Consider:
- Lines of code and number of abstractions introduced
- Cognitive load to understand the core logic
- Whether any construct exists only to support another introduced construct

Respond with JSON only: {"winner": "A" | "B" | "tie", "reasoning": "..."}
```

The `extensibility.md` criterion uses `{{extensibility_scenario}}` where the task-specific hypothetical gets injected.

---

## `orchestrator.py`

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .models import Task
from .task_loader import load_backlog
from . import workspace, agent, judge

def run(repo_root: Path, backlog_dir: Path, results_dir: Path, llm):
    for task in load_backlog(backlog_dir):
        print(f"\n── Task {task.id}: {task.title}")
        _run_task(task, repo_root, results_dir, llm)

def _run_task(task: Task, repo_root: Path, results_dir: Path, llm):
    with workspace.provision(task, repo_root) as workspaces:
        # implement all 3 variations in parallel
        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(agent.run, task, ws, llm) for ws in workspaces]
            results = [f.result() for f in futures]

        survivors = [r.workspace for r in results if r.success]
        if not survivors:
            print(f"  ✗ All variations failed — skipping")
            _archive(task, results, None, results_dir)
            return

        verdict = judge.rank(task, survivors, llm)
        _apply_winner(verdict.winner, repo_root)
        _archive(task, results, verdict, results_dir)
        print(f"  ✓ Winner: variation-{verdict.winner.variation}")
        print(f"  {verdict.reasoning}")

def _apply_winner(winner, repo_root: Path):
    import shutil
    # copy winner's src/ back over repo's src/
    shutil.copytree(winner.path / "src", repo_root / "src", dirs_exist_ok=True)

def _archive(task, results, verdict, results_dir: Path):
    import json
    out = results_dir / task.id
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({
        "agents": [{"variation": r.workspace.variation,
                    "success": r.success, "reason": r.reason}
                   for r in results],
        "verdict": {
            "winner": verdict.winner.variation,
            "reasoning": verdict.reasoning,
            "comparisons": [{"criterion": c.criterion, "winner": c.winner,
                             "reasoning": c.reasoning}
                            for c in verdict.comparisons]
        } if verdict else None
    }, indent=2))
```

---

## What's left unimplemented

The `llm` object passed everywhere has three methods that need implementing against your LLM of choice:

```python
llm.implement(task, instruction, context, workspace_path) → None  # writes files
llm.compare(prompt, path_a, path_b) → {"winner": ..., "reasoning": ...}
```

That's the only seam to the outside world. Everything else is pure logic you can test without an LLM.

Want to tackle the `llm` interface next, or the backlog task schema and a worked example task?