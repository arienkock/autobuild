import argparse
from pathlib import Path

from . import orchestrator
from .llm import create_default_llm


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Autobuild agentic development runner.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the repository root (default: current working directory).",
    )
    parser.add_argument(
        "--backlog-dir",
        type=Path,
        default=Path("backlog"),
        help="Path to the backlog directory of task YAML files.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(".autobuild") / "results",
        help="Directory where per-task results will be written.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all unbuilt tasks instead of stopping after the first one.",
    )
    parser.add_argument(
        "--task",
        metavar="TASK_ID",
        help="Build a specific task by ID, ignoring any existing results.",
    )

    args = parser.parse_args(argv)
    llm = create_default_llm()

    orchestrator.run(
        repo_root=args.repo_root,
        backlog_dir=args.backlog_dir,
        results_dir=args.results_dir,
        llm=llm,
        run_all=args.all,
        force_task_id=args.task,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry convenience
    main()

