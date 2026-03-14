# Autobuild

Autobuild automates feature implementation by running multiple AI agents in parallel, testing each result against your quality gates, and applying the best implementation back to your repository.

For each task in your backlog, Autobuild:

1. Spins up three isolated workspaces, each containing a copy of your source directory.
2. Runs a separate AI agent in each workspace, optionally with different agents, models, or prompts per variation.
3. Verifies each result against your quality gates (e.g. test suites, linters).
4. Runs a tournament-style judge that scores surviving variations against each other on your chosen criteria.
5. Copies the winning implementation back into your source directory.

Results for every task are written to `.autobuild/results/<task-id>/results.json`, including per-variation success/failure, CPU time, and the full tournament transcript.

---

## Installation

```bash
pip install -e .
```

This installs the `autobuild` CLI entry point.

---

## Running Autobuild

```
autobuild [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--repo-root PATH` | current directory | Root of the repository Autobuild will operate on. |
| `--backlog-dir PATH` | `.autobuild/backlog` | Directory containing task files (`.md`). |
| `--results-dir PATH` | `.autobuild/results` | Where per-task `results.json` files are written. |
| `--all` | off | Process every unbuilt task. Without this flag, Autobuild stops after the first unbuilt task. |
| `--task TASK_ID` | — | Build a specific task by ID, ignoring any existing result for it. |
| `--keep-workspaces` | off | Preserve temporary workspaces after the run for inspection. |

Tasks that already have a `results.json` are skipped unless `--task` targets them explicitly.

---

## Writing Tasks

Tasks live as Markdown files in `.autobuild/backlog/`. File names determine sort order; a numeric prefix like `001-my-task.md` is the recommended convention.

Each file uses YAML front matter for metadata and the body for the implementation description:

```markdown
---
id: "001"
title: My feature
extensibility_scenario: |
  Describe a plausible future change. The judge uses this to evaluate how
  well each variation supports extension without modifying existing code.
---
Write a plain prose description of what should be implemented.
Be specific about constraints, stack, and acceptance criteria.
```

**Required front-matter fields:**

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (used to name the results directory and for `--task`). |
| `title` | Human-readable name shown in CLI output. |
| `extensibility_scenario` | A future-change scenario the judge uses to score extensibility. |

**Optional front-matter field — `variation_instructions`:**

Override which agent, model, or additional prompt is used for each of the three variations. If omitted, the `default_variation_instructions` from `config.yaml` are used.

```yaml
variation_instructions:
  - agent: cursor
  - agent: aider
    model: "openrouter/some/model"
  - prompt: "Prefer a functional style. Avoid classes."
```

Each entry is an object with at most three keys — `agent`, `model`, `prompt` — and must specify at least one. A plain string is shorthand for `{ prompt: "..." }`.

---

## Configuration

All configuration lives in `.autobuild/config.yaml`. The file is optional; sensible defaults apply when it is absent.

### Source directory

```yaml
src_dir: "src"
```

Only this subdirectory of the repository is copied into each workspace. The winner is merged back here. Default: `src`.

### Quality gates

```yaml
quality_gates:
  - "npm run test"
  - "npm run lint"
```

A list of shell commands run inside the workspace after each implementation attempt. All commands must exit `0` for the attempt to count as a pass. A failing attempt is retried (up to three times total) with the gate output fed back to the agent as context. Default: `["python -m pytest --tb=short -q"]`.

### Timeouts

```yaml
timeouts:
  implementation: 360   # cap on the first attempt (seconds)
  retry: 180            # cap on each retry attempt (seconds)
```

Omit a key or set it to `null` for no time limit on that step.

### Agents

Define one or more named agents. Each agent specifies commands for the implementation and comparison phases, and an optional default model.

```yaml
agents:
  cursor:
    implement_command: "agent --print --trust --force [--api-key {CURSOR_API_KEY}] --workspace {workspace} --model {model} {prompt}"
    compare_command:   "agent --print --trust --mode ask [--api-key {CURSOR_API_KEY}] --workspace {workspace} --model {model} {prompt}"
    model: "auto"

  claude:
    implement_command: "claude --print --dangerously-skip-permissions --no-session-persistence --model {model} {prompt}"
    compare_command:   "claude --print --permission-mode plan --no-session-persistence --model {model} {prompt}"
    model: "sonnet"

  aider:
    implement_command: "aider --yes --no-git --model {model} --message {prompt}"
    compare_command:   "aider --yes --no-git --model {model} --read {path_a} --read {path_b} --message {prompt}"
    model: "openrouter/z-ai/glm-5"
```

**Placeholder tokens** available in commands:

| Token | Expands to |
|-------|-----------|
| `{prompt}` | The full implementation prompt. |
| `{workspace}` | Absolute path to the workspace directory. |
| `{model}` | Resolved model name (agent default, or variation override). |
| `{NAME}` | Value of the environment variable `NAME`. |
| `[...{NAME}...]` | The bracketed segment is omitted entirely when `NAME` is unset. |

`default_agent` sets which agent is used when a variation instruction specifies no agent:

```yaml
default_agent: cursor
```

### Default variation instructions

Applied to every task whose file does not specify its own `variation_instructions`. Exactly three entries are required.

```yaml
default_variation_instructions:
  - agent: cursor
  - agent: aider
    model: "openrouter/z-ai/glm-5"
  - agent: claude
    model: "claude-opus-4-5"
```

### Judge

By default the judge uses `default_agent`. Override it to get an independent judge, which is useful when the implementation variations already use that agent.

```yaml
judge:
  agent: claude
  model: "claude-opus-4-5"
```

---

## Results

After each task run, `.autobuild/results/<task-id>/results.json` contains:

- **`agents`** — one entry per variation with the variation label, the instruction used, success/failure, failure reason, and CPU time.
- **`verdict`** — the winning variation, a brief summary, and a full breakdown of every pairwise comparison (criterion, both variation labels, winner, and the judge's reasoning).

---

## Repository layout

```
autobuild/          core library
  cli.py            CLI entry point
  orchestrator.py   top-level loop across the backlog
  agent.py          implement + quality-gate loop per variation
  judge/            pairwise tournament engine
  workspace.py      workspace provisioning and teardown
  task_loader.py    load backlog Markdown files into Task objects
  models.py         shared dataclasses
  config.py         load and parse .autobuild/config.yaml
  llm.py            LLM client factory (replace to wire in your own)
.autobuild/
  config.yaml       project configuration
  backlog/          task Markdown files
  results/          per-task results.json files
```

To wire in a real LLM client without using a CLI agent, replace `autobuild.llm.create_default_llm` with your own implementation of the `LlmClient` protocol defined in `autobuild/agent.py`.
