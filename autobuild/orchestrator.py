import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace as _dc_replace
from pathlib import Path
from typing import Iterable

from . import agent, judge, workspace
from .config import load_config
from .llm import create_judge_llm
from .models import AgentResult, Config, Task, VariationInstruction
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
        partial = _load_partial(task, results_dir)
        if force_task_id is not None:
            if task.id != force_task_id:
                continue
            matched = True
        else:
            result_file = results_dir / task.id / "results.json"
            if partial is None and result_file.exists():
                print(f"\n── Task {task.id}: {task.title} [already built, skipping]")
                continue

        if partial and partial.get("status") == "failed":
            print(f"\n── Task {task.id}: {task.title} [retrying after previous failure]")
        else:
            print(f"\n── Task {task.id}: {task.title}")
        winner_info = _run_task(task, repo_root, results_dir, llm, config.quality_gates, config.src_dir, keep_workspaces, config=config, partial_result=partial)

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
    partial_result: dict | None = None,
) -> tuple[str, VariationInstruction] | None:
    """Run a single task and return ``(winning_variation, winning_vi)`` or ``None`` on total failure."""
    # Don't resume into a dirty workspace when the prior run fully failed — start fresh.
    resume = partial_result is not None and partial_result.get("status") != "failed"
    with workspace.provision(task, repo_root, src_dir, keep=keep_workspaces, resume=resume) as ctx:
        workspaces = ctx.workspaces
        for ws in workspaces:
            print(f"  [{ws.variation}] workspace: {ws.path}")
        ws_by_variation = {ws.variation: ws for ws in workspaces}
        gate_llm = create_judge_llm(config, llm)
        llm_quality_gates = config.llm_quality_gates if config else []

        if partial_result and partial_result.get("status") == "judging":
            # All variations are done; skip straight to judging.
            completed_results = _reconstruct_results(partial_result["agents"], ws_by_variation)
            survivors = [r.workspace for r in completed_results if r.success]
            if not survivors:
                ctx.keep = True
                print("  ✗ All variations failed — skipping")
                _write_results(task, completed_results, None, results_dir, status="failed")
                return None
            verdict = judge.rank(task, survivors, create_judge_llm(config, llm), repo_root=repo_root)
            _apply_winner(verdict.winner, repo_root)
            _write_results(task, completed_results, verdict, results_dir)
            print(f"  ✓ Winner: variation-{verdict.winner.variation}")
            print(f"  {verdict.reasoning}")
            winning_vi = task.variation_instructions[_VARIATION_INDEX[verdict.winner.variation]]
            return verdict.winner.variation, winning_vi

        # Determine which variations to carry from a prior partial run vs re-run.
        carried_results: list[AgentResult] = []
        workspaces_to_run = list(workspaces)
        if partial_result:
            succeeded = {a["variation"] for a in partial_result.get("agents", []) if a.get("success")}
            carried_results = _reconstruct_results(
                [a for a in partial_result.get("agents", []) if a.get("success")],
                ws_by_variation,
            )
            workspaces_to_run = [ws for ws in workspaces if ws.variation not in succeeded]

        completed_results: list[AgentResult] = list(carried_results)

        if workspaces_to_run:
            with ProcessPoolExecutor(max_workers=len(workspaces_to_run)) as pool:
                futures = {
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
                    ): ws
                    for ws in workspaces_to_run
                }
                for future in as_completed(futures):
                    ws = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        print(f"  [{ws.variation}] worker crashed: {exc}", flush=True)
                        result = AgentResult(success=False, workspace=ws, reason=repr(exc))
                    completed_results.append(result)
                    _write_results(task, completed_results, None, results_dir, status="in_progress")

        survivors = [r.workspace for r in completed_results if r.success]
        if not survivors:
            ctx.keep = True
            print("  ✗ All variations failed — skipping")
            _write_results(task, completed_results, None, results_dir, status="failed")
            return None

        _write_results(task, completed_results, None, results_dir, status="judging")
        verdict = judge.rank(task, survivors, create_judge_llm(config, llm), repo_root=repo_root)
        _apply_winner(verdict.winner, repo_root)
        _write_results(task, completed_results, verdict, results_dir)
        print(f"  ✓ Winner: variation-{verdict.winner.variation}")
        print(f"  {verdict.reasoning}")
        winning_vi = task.variation_instructions[_VARIATION_INDEX[verdict.winner.variation]]
        return verdict.winner.variation, winning_vi


def _git_commit(task: Task, winner_info: tuple[str, VariationInstruction], repo_root: Path) -> None:
    import subprocess

    variation, vi = winner_info
    subject = f"{task.id} [{variation}]"
    body_parts = []
    if vi.prompt:
        body_parts.append(f"prompt: {vi.prompt}")
    if vi.agent:
        body_parts.append(f"agent: {vi.agent}")
    if vi.model:
        body_parts.append(f"model: {vi.model}")
    message = subject + ("\n\n" + "\n".join(body_parts) if body_parts else "")
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
    print(f"  ↳ Committed: {subject}")


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


def _load_partial(task: Task, results_dir: Path) -> dict | None:
    """Return parsed results.json if the task is not yet successfully complete.

    Returns data for statuses ``"in_progress"``, ``"judging"``, and ``"failed"``
    so that interrupted and totally-failed tasks are re-run rather than silently
    skipped.  Returns None when the file does not exist or when status is
    ``"complete"`` (task succeeded and should be skipped).
    """
    result_file = results_dir / task.id / "results.json"
    if not result_file.exists():
        return None
    data = json.loads(result_file.read_text())
    if data.get("status") not in ("in_progress", "judging", "failed"):
        return None
    return data


def _reconstruct_results(agents_data: list[dict], ws_by_variation: dict) -> list[AgentResult]:
    """Reconstruct AgentResult objects from partial JSON using live Workspace objects."""
    return [
        AgentResult(
            success=a.get("success", False),
            workspace=ws_by_variation[a["variation"]],
            reason=a.get("reason", ""),
            cpu_time_seconds=a.get("cpu_time_seconds", 0.0),
            llm_gate_results=a.get("llm_gate_results", []),
        )
        for a in agents_data
    ]


def _write_results(task: Task, results: Iterable, verdict, results_dir: Path, status: str = "complete") -> None:
    out = results_dir / task.id
    out.mkdir(parents=True, exist_ok=True)

    def _vi_dict(vi: VariationInstruction) -> dict:
        return {k: v for k, v in {"prompt": vi.prompt, "agent": vi.agent, "model": vi.model}.items() if v is not None}

    payload: dict = {
        "status": status,
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

