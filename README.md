# Autobuild

Runs multiple AI agents on each backlog task in parallel, tests results against your quality gates, and applies the best implementation to your repository.

---

## Prerequisites

**Python 3.11+** — check with:

```bash
python3 --version
```

If you don't have it, install via [python.org](https://www.python.org/downloads/) or Homebrew:

```bash
brew install python@3.11
```

**pip** — comes with Python. Verify:

```bash
pip3 --version
```

---

## Install

```bash
git clone https://github.com/your-org/autobuild.git
cd autobuild
pip3 install .
```

This installs the `autobuild` command on your PATH.

---

## Getting Started

**1. Initialize a project** inside your repository:

```bash
cd /path/to/your-repo
autobuild init
```

This creates `.autobuild/` with a config file, example task, gates, and criteria, and a `src/` directory for your project source.

**2. Edit the config** at `.autobuild/config.yaml` — set your agent, quality gates, and LLM settings.

**3. Write a task** in `.autobuild/backlog/`. Use the generated `001-example.md` as a starting point.

**4. Run the next task:**

```bash
autobuild run
```

Or run all unbuilt tasks at once:

```bash
autobuild run --all
```

---

## Commands

### `autobuild init`

Initializes autobuild in the current directory (or `--repo-root PATH`).

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
| `--repo-root PATH` | Repository root (default: current directory). |
