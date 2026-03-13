from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable

from . import agent, judge, workspace
from .config import load_config
from .models import Task
from .task_loader import load_backlog


def run(repo_root: Path, backlog_dir: Path, results_dir: Path, llm) -> None:
    """Run the autobuild loop over all tasks in the backlog."""
    config = load_config(repo_root)
    for task in load_backlog(backlog_dir):
        print(f"\n── Task {task.id}: {task.title}")
        _run_task(task, repo_root, results_dir, llm, config.quality_gates, config.src_dir)


def _run_task(
    task: Task,
    repo_root: Path,
    results_dir: Path,
    llm,
    quality_gates: list[str],
    src_dir: str,
) -> None:
    with workspace.provision(task, repo_root, src_dir) as workspaces:
        # implement all 3 variations in parallel
        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(agent.run, task, ws, llm, quality_gates)
                for ws in workspaces
            ]
            results = [f.result() for f in futures]

        survivors = [r.workspace for r in results if r.success]
        if not survivors:
            print("  ✗ All variations failed — skipping")
            _archive(task, results, None, results_dir)
            return

        verdict = judge.rank(task, survivors, llm)
        _apply_winner(verdict.winner, repo_root)
        _archive(task, results, verdict, results_dir)
        print(f"  ✓ Winner: variation-{verdict.winner.variation}")
        print(f"  {verdict.reasoning}")


def _apply_winner(winner, repo_root: Path) -> None:
    import shutil

    shutil.copytree(
        winner.path / winner.src_dir,
        repo_root / winner.src_dir,
        dirs_exist_ok=True,
    )


def _archive(task: Task, results: Iterable, verdict, results_dir: Path) -> None:
    import json

    out = results_dir / task.id
    out.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "agents": [
            {
                "variation": r.workspace.variation,
                "success": r.success,
                "reason": r.reason,
            }
            for r in results
        ],
        "verdict": None,
    }
    if verdict is not None:
        payload["verdict"] = {
            "winner": verdict.winner.variation,
            "reasoning": verdict.reasoning,
            "comparisons": [
                {
                    "criterion": c.criterion,
                    "winner": c.winner,
                    "reasoning": c.reasoning,
                }
                for c in verdict.comparisons
            ],
        }

    (out / "results.json").write_text(json.dumps(payload, indent=2))

