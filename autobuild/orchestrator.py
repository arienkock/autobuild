from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace as _dc_replace
from pathlib import Path
from typing import Iterable

from . import agent, judge, workspace
from .config import load_config
from .llm import create_judge_llm
from .models import Config, Task, VariationInstruction
from .task_loader import load_backlog


def run(
    repo_root: Path,
    backlog_dir: Path,
    results_dir: Path,
    llm,
    run_all: bool = False,
    force_task_id: str | None = None,
    keep_workspaces: bool = False,
    auto_commit: bool = False,
) -> None:
    """Run the autobuild loop over tasks in the backlog.

    By default stops after building the first unbuilt task.  Pass
    ``run_all=True`` to process every unbuilt task in one invocation, or
    ``force_task_id`` to build a specific task regardless of prior results.
    Pass ``auto_commit=True`` (requires ``run_all=True``) to stage and commit
    all repo changes after each successful task.
    """
    config = load_config(repo_root)
    matched = False
    for task in load_backlog(backlog_dir, config.default_variation_instructions, agents=config.agents):
        if force_task_id is not None:
            if task.id != force_task_id:
                continue
            matched = True
        else:
            result_file = results_dir / task.id / "results.json"
            if result_file.exists():
                print(f"\n── Task {task.id}: {task.title} [already built, skipping]")
                continue

        print(f"\n── Task {task.id}: {task.title}")
        winner_info = _run_task(task, repo_root, results_dir, llm, config.quality_gates, config.src_dir, keep_workspaces, config=config)

        if auto_commit and winner_info is not None:
            _git_commit(task, winner_info, repo_root)

        if not run_all:
            break

    if force_task_id is not None and not matched:
        raise ValueError(f"No task with id '{force_task_id}' found in backlog")


_VARIATION_INDEX = {"a": 0, "b": 1, "c": 2}


def _resolve_variation_llm(vi: VariationInstruction, config: Config, default_llm):
    """Return the LLM appropriate for *vi*, falling back to *default_llm* when no override."""
    agent_name = vi.agent
    model_override = vi.model
    if not agent_name and not model_override:
        return default_llm

    from .cli_llm import CliLlm  # noqa: PLC0415

    resolved_agent = agent_name or config.default_agent
    if resolved_agent and resolved_agent in config.agents:
        agent_cfg = config.agents[resolved_agent]
    else:
        return default_llm

    if model_override:
        agent_cfg = _dc_replace(agent_cfg, model=model_override)
    return CliLlm(agent_cfg)


def _run_task(
    task: Task,
    repo_root: Path,
    results_dir: Path,
    llm,
    quality_gates: list[str],
    src_dir: str,
    keep_workspaces: bool = False,
    config: Config | None = None,
) -> tuple[str, str] | None:
    """Run a single task and return ``(winning_variation, instruction_prompt)`` or ``None`` on total failure."""
    with workspace.provision(task, repo_root, src_dir, keep=keep_workspaces) as workspaces:
        for ws in workspaces:
            print(f"  [{ws.variation}] workspace: {ws.path}")
        # implement all variations in parallel, each with its own resolved LLM
        gate_llm = create_judge_llm(config, llm)
        llm_quality_gates = config.llm_quality_gates if config else []
        with ProcessPoolExecutor(max_workers=len(workspaces)) as pool:
            futures = [
                pool.submit(
                    agent.run,
                    task,
                    ws,
                    _resolve_variation_llm(
                        task.variation_instructions[_VARIATION_INDEX[ws.variation]],
                        config,
                        default_llm=llm,
                    ) if config else llm,
                    quality_gates,
                    llm_quality_gates,
                    gate_llm,
                    config.implementation_timeout if config else None,
                    config.retry_timeout if config else None,
                )
                for ws in workspaces
            ]
            results = [f.result() for f in futures]

        survivors = [r.workspace for r in results if r.success]
        if not survivors:
            print("  ✗ All variations failed — skipping")
            _archive(task, results, None, results_dir)
            return None

        verdict = judge.rank(task, survivors, create_judge_llm(config, llm), repo_root=repo_root)
        _apply_winner(verdict.winner, repo_root)
        _archive(task, results, verdict, results_dir)
        print(f"  ✓ Winner: variation-{verdict.winner.variation}")
        print(f"  {verdict.reasoning}")
        winning_vi = task.variation_instructions[_VARIATION_INDEX[verdict.winner.variation]]
        return verdict.winner.variation, winning_vi.prompt or ""


def _git_commit(task: Task, winner_info: tuple[str, str], repo_root: Path) -> None:
    import subprocess

    variation, instruction = winner_info
    message = f"autobuild: task {task.id} [{variation}] - {instruction}" if instruction else f"autobuild: task {task.id} [{variation}]"
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
    print(f"  ↳ Committed: {message}")


def _apply_winner(winner, repo_root: Path) -> None:
    import shutil
    import subprocess

    # Git is rooted at winner.path/src_dir (set up in workspace.provision),
    # so all paths returned by git are relative to src_dir. We copy them
    # explicitly under repo_root/src_dir — never to the repo root.
    git_root = winner.path / winner.src_dir
    dst_root = repo_root / winner.src_dir

    # Modified/deleted tracked files
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=git_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    # New untracked files (recursively, respecting .gitignore)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=git_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    for rel in set(tracked + untracked):
        if not rel:
            continue
        src = git_root / rel
        dst = dst_root / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            dst.unlink(missing_ok=True)


def _archive(task: Task, results: Iterable, verdict, results_dir: Path) -> None:
    import json

    out = results_dir / task.id
    out.mkdir(parents=True, exist_ok=True)

    def _vi_dict(vi: VariationInstruction) -> dict:
        return {k: v for k, v in {"prompt": vi.prompt, "agent": vi.agent, "model": vi.model}.items() if v is not None}

    payload: dict = {
        "agents": [
            {
                "variation": r.workspace.variation,
                "variation_instruction": _vi_dict(task.variation_instructions[_VARIATION_INDEX[r.workspace.variation]]),
                "success": r.success,
                "reason": r.reason,
                "cpu_time_seconds": round(r.cpu_time_seconds, 3),
                "llm_gate_results": r.llm_gate_results,
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
                    "variation_a": c.variation_a,
                    "variation_b": c.variation_b,
                    "winner": (
                        c.variation_a if c.winner == "A"
                        else c.variation_b if c.winner == "B"
                        else "tie"
                    ),
                    "reasoning": c.reasoning,
                }
                for c in verdict.comparisons
            ],
        }

    (out / "results.json").write_text(json.dumps(payload, indent=2))

