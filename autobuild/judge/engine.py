from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path
from typing import Dict, List

from ..models import Comparison, JudgeResult, Task, Workspace

_CRITERIA_DIR = Path(__file__).parent / "criteria"


def rank(task: Task, workspaces: List[Workspace], llm) -> JudgeResult:
    criteria = _load_criteria()
    all_comparisons: List[Comparison] = []
    pairs = list(combinations(workspaces, 2))
    jobs = [(a, b, criterion) for a, b in pairs for criterion in criteria]
    total = len(jobs)

    print(
        f"  Judging {len(workspaces)} variations across {len(criteria)} criteria"
        f" ({total} comparisons)…",
        flush=True,
    )

    # pairwise tournament across all criteria
    scores: Dict[str, float] = {w.variation: 0.0 for w in workspaces}
    with ThreadPoolExecutor() as executor:
        future_to_job = {
            executor.submit(_compare, task, a, b, criterion, llm): (a, b, criterion)
            for a, b, criterion in jobs
        }

        for step, future in enumerate(as_completed(future_to_job), start=1):
            a, b, criterion = future_to_job[future]
            print(
                f"  [{step}/{total}] {criterion.name}: {a.variation} vs {b.variation}…",
                flush=True,
            )
            comparison = future.result()
            all_comparisons.append(comparison)
            winner_label = (
                a.variation if comparison.winner == "A"
                else b.variation if comparison.winner == "B"
                else "tie"
            )
            print(f"    → {winner_label}: {comparison.reasoning[:120]}…", flush=True)
            if comparison.winner == "A":
                scores[a.variation] += criterion.weight
            elif comparison.winner == "B":
                scores[b.variation] += criterion.weight

    winner_variation = max(scores, key=lambda v: scores[v])
    winner = next(w for w in workspaces if w.variation == winner_variation)

    return JudgeResult(
        winner=winner,
        comparisons=all_comparisons,
        reasoning=_summarise(scores, all_comparisons),
    )


class _Criterion:
    def __init__(self, name: str, prompt: str, weight: float) -> None:
        self.name = name
        self.prompt = prompt
        self.weight = weight


def _load_criteria() -> List["_Criterion"]:
    criteria: List[_Criterion] = []
    for path in sorted(_CRITERIA_DIR.glob("*.md")):
        text = path.read_text()
        weight = _parse_weight(text)
        if weight == 0:
            continue
        prompt = _parse_prompt(text)
        criteria.append(_Criterion(name=path.stem, prompt=prompt, weight=weight))
    return criteria


def _parse_weight(text: str) -> float:
    for line in text.splitlines():
        if line.startswith("weight:"):
            return float(line.split(":", 1)[1].strip())
    return 1.0


def _parse_prompt(text: str) -> str:
    # everything after the frontmatter block
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else text.strip()


def _compare(task: Task, a: Workspace, b: Workspace, criterion: _Criterion, llm) -> Comparison:
    prompt = criterion.prompt
    if "{{extensibility_scenario}}" in prompt:
        prompt = prompt.replace("{{extensibility_scenario}}", task.extensibility_scenario)
    if "{{task_description}}" in prompt:
        prompt = prompt.replace("{{task_description}}", task.description)
    result = llm.compare(prompt, a.path, b.path)
    return Comparison(
        criterion=criterion.name,
        winner=result["winner"],
        reasoning=result["reasoning"],
    )


def _summarise(scores: Dict[str, float], comparisons: List[Comparison]) -> str:
    lines = [
        f"  {v}: {s:.1f} points" for v, s in sorted(scores.items(), key=lambda x: -x[1])
    ]
    return "Tournament scores:\n" + "\n".join(lines)

