# Autobuild

Runs multiple AI agents on each backlog task in parallel, tests results against your quality gates, and applies the best implementation to your repository.

Instead of asking one agent to implement a feature and hoping for the best, Autobuild runs up to three agents simultaneously — each guided by a different strategy — then objectively selects the winner. Shell-based quality gates (tests, lint, build) determine which implementations are valid. An LLM-judged tournament across weighted criteria — simplicity, extensibility, faithfulness to the task — determines which valid implementation wins. The winner is applied to your repository, and the cycle repeats for the next backlog item.

The result: you describe what you want, Autobuild builds it, checks it, and commits the best version.

---

## Why Autobuild?

- **Parallel exploration** — multiple agents try different approaches at the same time, so you get the benefit of diversity without the wait.
- **Automated quality control** — your own test suite and linter are the gatekeepers; no implementation ships unless it passes.
- **Principled selection** — a configurable set of LLM-judged criteria (simplicity, modularity, extensibility) pick the winner, not guesswork.
- **Bring your own agent** — works with Claude Code, Cursor Agent, Aider, or any CLI agent you can describe with a command template.
- **Fully auditable** — every run archives all variations and the full judge reasoning so you can review what happened and why.

---

## Quickstart

```bash
# 1. Install
pip3.11 install git+https://github.com/arienkock/autobuild.git

# 2. Initialize in your repository
cd /path/to/your-repo
autobuild init

# 3. Edit .autobuild/config.yaml — set your agent and quality gates

# 4. Write a task in .autobuild/backlog/ (use the generated 001-example.md)

# 5. Run
autobuild run
```

That's it. Autobuild picks up the first unbuilt task, spins up variations, runs your gates, and applies the best result to your source tree.

See [INSTALLATION.md](INSTALLATION.md) for full setup details (including virtual environments) and [USAGE.md](USAGE.md) for a deep dive into agents, gates, criteria, and task authoring.

---

## Commands

### Global flag

| Flag | Description |
|------|-------------|
| `--repo-root PATH` | Repository root (default: current directory). Placed **before** the subcommand: `autobuild --repo-root PATH run`. |

### `autobuild init`

Initializes Autobuild in the current directory. Creates `.autobuild/` with a config file, an example task, and starter gate and criteria files.

| Flag | Description |
|------|-------------|
| `--force` | Overwrite an existing `.autobuild/` directory. |

### `autobuild run`

Runs the next unbuilt task from the backlog.

| Flag | Description |
|------|-------------|
| `--all` | Run all unbuilt tasks, not just the first. |
| `--task TASK_ID` | Run a specific task by ID, ignoring existing results. |
| `--auto-commit` | Commit changes after each successful task (requires `--all`). |
| `--keep-workspaces` | Keep temporary workspaces after the run for inspection. |
