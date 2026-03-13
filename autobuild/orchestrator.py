from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable

from . import agent, judge, workspace
from .config import load_config
from .models import Task
from .task_loader import load_backlog


def run(
    repo_root: Path,
    backlog_dir: Path,
    results_dir: Path,
    llm,
    run_all: bool = False,
    force_task_id: str | None = None,
    keep_workspaces: bool = False,
) -> None:
    """Run the autobuild loop over tasks in the backlog.

    By default stops after building the first unbuilt task.  Pass
    ``run_all=True`` to process every unbuilt task in one invocation, or
    ``force_task_id`` to build a specific task regardless of prior results.
    """
    config = load_config(repo_root)
    for task in load_backlog(backlog_dir):
        if force_task_id is not None:
            if task.id != force_task_id:
                continue
        else:
            result_file = results_dir / task.id / "results.json"
            if result_file.exists():
                print(f"\n── Task {task.id}: {task.title} [already built, skipping]")
                continue

        print(f"\n── Task {task.id}: {task.title}")
        _run_task(task, repo_root, results_dir, llm, config.quality_gates, config.src_dir, keep_workspaces)

        if not run_all:
            break


def _run_task(
    task: Task,
    repo_root: Path,
    results_dir: Path,
    llm,
    quality_gates: list[str],
    src_dir: str,
    keep_workspaces: bool = False,
) -> None:
    with workspace.provision(task, repo_root, src_dir, keep=keep_workspaces) as workspaces:
        for ws in workspaces:
            print(f"  [{ws.variation}] workspace: {ws.path}")
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
                "cpu_time_seconds": round(r.cpu_time_seconds, 3),
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

