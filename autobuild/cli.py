import argparse
import shutil
import sys
from pathlib import Path

from . import orchestrator
from .config import load_config
from .llm import create_default_llm

_TEMPLATE_DIR = Path(__file__).parent / "template"


def _cmd_run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.auto_commit and not args.all:
        parser.error("--auto-commit requires --all")

    if args.backlog_dir is None:
        args.backlog_dir = args.repo_root / ".autobuild" / "backlog"
    if args.results_dir is None:
        args.results_dir = args.repo_root / ".autobuild" / "results"

    config = load_config(args.repo_root)
    llm = create_default_llm(config)

    orchestrator.run(
        repo_root=args.repo_root,
        backlog_dir=args.backlog_dir,
        results_dir=args.results_dir,
        llm=llm,
        run_all=args.all,
        force_task_id=args.task,
        keep_workspaces=args.keep_workspaces,
        auto_commit=args.auto_commit,
    )


def _cmd_init(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    autobuild_dir = args.repo_root / ".autobuild"

    if autobuild_dir.exists() and not args.force:
        parser.error(
            f"'{autobuild_dir}' already exists. Use --force to overwrite."
        )

    dirs_to_create = [
        autobuild_dir / "backlog",
        autobuild_dir / "gates",
        autobuild_dir / "criteria",
        autobuild_dir / "results",
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    template_items = [
        ("config.yaml", autobuild_dir / "config.yaml"),
        ("backlog/001-example.md", autobuild_dir / "backlog" / "001-example.md"),
        ("gates", autobuild_dir / "gates"),
        ("criteria", autobuild_dir / "criteria"),
    ]
    for src_rel, dest in template_items:
        src = _TEMPLATE_DIR / src_rel
        if src.is_dir():
            for f in src.iterdir():
                shutil.copy2(f, dest / f.name)
        else:
            shutil.copy2(src, dest)

    src_dir = args.repo_root / "src"
    src_dir.mkdir(exist_ok=True)

    print(f"Initialized autobuild project at '{args.repo_root}'.")
    print(f"  {autobuild_dir.relative_to(args.repo_root)}/")
    print(f"    backlog/001-example.md  ← replace with your first task")
    print(f"    config.yaml             ← configure agents, gates, and more")
    print(f"  src/                      ← put your project source here")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Autobuild agentic development runner.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the repository root (default: current working directory).",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- run subcommand ---
    run_parser = subparsers.add_parser(
        "run",
        help="Run the next unbuilt task (or all tasks) from the backlog.",
    )
    run_parser.add_argument(
        "--backlog-dir",
        type=Path,
        default=None,
        help="Path to the backlog directory of task YAML files (default: <repo-root>/.autobuild/backlog).",
    )
    run_parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Directory where per-task results will be written (default: <repo-root>/.autobuild/results).",
    )
    run_parser.add_argument(
        "--all",
        action="store_true",
        help="Run all unbuilt tasks instead of stopping after the first one.",
    )
    run_parser.add_argument(
        "--task",
        metavar="TASK_ID",
        help="Build a specific task by ID, ignoring any existing results.",
    )
    run_parser.add_argument(
        "--keep-workspaces",
        action="store_true",
        help="Keep temporary workspaces after the run for post-run inspection.",
    )
    run_parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Stage and commit all changes after each successful task (requires --all).",
    )

    # --- init subcommand ---
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new autobuild project in the repo root.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing .autobuild directory.",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        _cmd_run(args, run_parser)
    elif args.command == "init":
        _cmd_init(args, init_parser)
    else:  # pragma: no cover
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entry convenience
    main()
