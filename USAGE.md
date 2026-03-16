# Usage Guide

This guide covers Autobuild in depth. Start with [INSTALLATION.md](INSTALLATION.md) if you haven't set it up yet.

---

## Table of Contents

1. [Authenticating your agents](#1-authenticating-your-agents)
2. [Writing tasks](#2-writing-tasks)
3. [Variation prompts](#3-variation-prompts)
4. [Shell quality gates](#4-shell-quality-gates)
5. [LLM quality gates](#5-llm-quality-gates)
6. [Judge criteria](#6-judge-criteria)
7. [Running Autobuild](#7-running-autobuild)
8. [Extending to support more agent CLIs](#8-extending-to-support-more-agent-clis)

---

## 1. Authenticating your agents

Autobuild invokes AI agents as CLI subprocesses. Authentication is the responsibility of each agent's own tooling — Autobuild simply calls the command you configure.

### Claude Code

Claude Code authenticates via `claude login` (OAuth) or an API key in the environment:

```bash
# Interactive login (persists credentials locally)
claude login

# Or set an environment variable
export ANTHROPIC_API_KEY=sk-ant-...
```

Once logged in, the `claude` CLI works without further flags. The default agent definition in `config.yaml` uses `--dangerously-skip-permissions` and `--no-session-persistence` so that it runs non-interactively:

```yaml
agents:
  claude:
    implement_command: "claude --print --dangerously-skip-permissions --no-session-persistence --model {model} {prompt}"
    compare_command:   "claude --print --permission-mode plan --no-session-persistence --model {model} {prompt}"
    model: "sonnet"
```

### Cursor Agent

The Cursor agent (`agent` CLI) can be authenticated via an API key passed as a flag, or by relying on your active Cursor session. The command template supports an *optional argument* syntax so the flag is omitted when the variable isn't set:

```yaml
agents:
  cursor:
    implement_command: "agent --print --trust --force --approve-mcps [--api-key {CURSOR_API_KEY}] --workspace {workspace} --model {model} {prompt}"
    compare_command:   "agent --print --trust --mode ask --approve-mcps [--api-key {CURSOR_API_KEY}] --workspace {workspace} --model {model} {prompt}"
    model: "auto"
```

`[--api-key {CURSOR_API_KEY}]` means: if the environment variable `CURSOR_API_KEY` is set, include `--api-key <value>`; otherwise omit the whole block.

```bash
export CURSOR_API_KEY=your-key-here
```

### Aider

Aider reads API keys from the environment for whichever provider you're using:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
# OpenRouter and others are also supported
```

No special Autobuild configuration is needed beyond setting the environment variables before running `autobuild run`.

### General pattern

For any agent, the rule is:

1. Make sure `agent --help` (or equivalent) works in your shell.
2. Confirm the agent can complete a simple task non-interactively.
3. Configure the command template in `config.yaml` (see [§8](#8-extending-to-support-more-agent-clis)).

---

## 2. Writing tasks

Tasks live in `.autobuild/backlog/` as Markdown files with a YAML front-matter block. Files are processed in alphabetical order, so use numeric prefixes to control sequencing.

### Task file format

```markdown
---
id: "002"
title: Add user authentication
extensibility_scenario: |
  In the future we may want to support OAuth providers in addition to email/password.
  How well does the design accommodate adding a new provider without touching existing auth logic?
variation_instructions:
  - "Prioritise simplicity. Use the minimal viable approach."
  - "You are a security engineer. Harden the implementation against common vulnerabilities."
  - "You are a TDD practitioner. Write failing tests first, then make them pass."
---

Implement email/password authentication with session cookies.

Requirements:
- POST /auth/register — create an account
- POST /auth/login — return a session cookie
- POST /auth/logout — invalidate the session
- Protect any route that requires a logged-in user

Use the existing database module for persistence.
```

### Front-matter fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier, used for result archiving and `--task` targeting. |
| `title` | Yes | Short human-readable label shown in run output. |
| `extensibility_scenario` | Yes | A hypothetical future change used by the extensibility judge criterion. |
| `variation_instructions` | No | Per-variation strategy prompts (1–3). Falls back to `default_variation_instructions` in `config.yaml`. |

### Task body

The body (everything after the front-matter `---`) is the task description. Write it as you would a detailed ticket or user story. The full text is passed to each agent along with its variation instruction.

### Tracking progress

Autobuild marks a task as built by writing a result file to `.autobuild/results/<id>/`. Running `autobuild run` without `--all` skips tasks that already have results. Use `--task <id>` to re-run a specific task regardless.

---

## 3. Variation prompts

Variations are what make Autobuild different from running a single agent. Each variation is a separate agent invocation using a different strategy prompt, encouraging genuinely different implementation approaches.

### Default variation instructions

Set in `config.yaml` and applied to every task that doesn't define its own:

```yaml
default_variation_instructions:
  - "You are a ATDD expert. Write the tests first at a functional level, then the code."
  - "You are a world-class software engineer."
  - "You are an expert developer, but you also have a PhD in statistics and machine learning."
```

Up to three entries are supported. If you only provide one or two, Autobuild runs that many variations.

### Per-task variation instructions

Override the defaults for a specific task inside its front-matter:

```yaml
variation_instructions:
  - "Prioritise simplicity above all else. Fewer abstractions are better."
  - "You are a security engineer. Think about attack surface and input validation."
  - "Focus on observability: add structured logging and metrics from the start."
```

### Variation instruction format

Each entry can be a plain string or an object:

```yaml
# Plain string — uses the default agent and model
variation_instructions:
  - "Think step by step and explain your reasoning."

# Object form — override agent or model per variation
variation_instructions:
  - agent: claude
    model: "claude-opus-4-5"
    prompt: "You are a senior engineer. Prioritise long-term maintainability."
  - agent: aider
    model: "openrouter/z-ai/glm-5"
  - prompt: "You are a performance engineer. Profile first, optimise second."
```

Fields in the object form:

| Field | Description |
|-------|-------------|
| `prompt` | Strategy text passed to the agent. |
| `agent` | Name of an agent defined under `agents` in `config.yaml`. |
| `model` | Model override, replaces the agent's default model for this variation. |

---

## 4. Shell quality gates

Shell quality gates are commands that run inside each workspace after the agent completes its implementation. Every command must exit with code `0` for the attempt to pass. If any gate fails, the failure output is fed back to the agent as context and it retries (up to the configured timeout).

### Configuration

```yaml
quality_gates:
  - "npm run test"
  - "npm run lint"
  - "npm run build"
```

Gates run in the order listed. The first failure stops execution for that attempt.

### What makes a good shell gate

- **Fast feedback** — gates run on every attempt, so keep them quick. Full integration test suites are better placed in LLM gates or post-run CI.
- **Clear exit codes** — make sure your commands exit non-zero on failure. Most test runners and linters do this by default.
- **Self-contained** — gates run inside a temporary workspace copy, so they must work relative to the workspace root. Avoid hardcoded absolute paths.

### Retries and timeouts

The agent retries after each gate failure, with gate output appended to its context so it can learn from the error. Configure how long each attempt may take:

```yaml
timeouts:
  implementation: 360   # seconds for the first attempt
  retry: 180            # seconds for each subsequent attempt
```

Set a value to `null` to disable the timeout for that phase.

---

## 5. LLM quality gates

LLM quality gates run after the shell gates pass. Each gate is a Markdown prompt file in `.autobuild/gates/` that asks an LLM to evaluate the implementation and respond with `PASS` or `FAIL`. On `FAIL`, the reasoning is appended to the agent's context for the next retry — the same feedback loop as shell gates.

### Configuration

```yaml
llm_quality_gates:
  - faithfulness
  - testing_quality
  - ui_quality
```

Each name maps to `.autobuild/gates/<name>.md`.

### Gate prompt format

```markdown
---
---

Does the implementation maintain honest and meaningful test quality?

Consider:
- Did the implementation cheat or take shortcuts? e.g. useless tests without assertions
- Are new tests actually verifying the intended behavior?
- Were existing passing tests removed or weakened?

Respond with JSON only: {"grade": "PASS" | "FAIL", "reasoning": "..."}
```

The front-matter block (between the `---` delimiters) is reserved for future metadata. Keep it empty for now.

### Built-in gates

`autobuild init` copies three starter gates:

| Gate | What it checks |
|------|---------------|
| `faithfulness` | Whether the implementation matches the task description and intent |
| `testing_quality` | Whether tests are genuine and not written to trivially pass |
| `ui_quality` | Visual QA — launches the app in a browser and inspects for layout defects |

### Skipping LLM gates for a task

To skip LLM gates entirely, omit `llm_quality_gates` from `config.yaml` or set it to an empty list:

```yaml
llm_quality_gates: []
```

### Configuring a dedicated judge for gates

By default, LLM gates use the `default_agent`. To use a different model for evaluation (e.g., to separate the builder from the evaluator):

```yaml
judge:
  agent: claude
  model: "claude-opus-4-5"
```

---

## 6. Judge criteria

After all variations pass the quality gates, the judge ranks them using a pairwise tournament. Each criterion is a Markdown prompt file in `.autobuild/criteria/` that asks an LLM to compare two implementations and pick a winner.

### Configuration

Criteria are loaded automatically from `.autobuild/criteria/`. There is no list to configure; add or remove `.md` files to change which criteria are used.

### Criterion file format

```markdown
---
weight: 1.5
---

Given two implementations of the same feature (A and B), which is easier to
extend in the following scenario?

{{extensibility_scenario}}

Consider:
- Whether likely future changes have clear extension points
- How often existing code would need to be modified versus new code added

Respond with JSON only: {"winner": "A" | "B" | "tie", "reasoning": "..."}
```

Front-matter fields:

| Field | Default | Description |
|-------|---------|-------------|
| `weight` | `1.0` | How much this criterion counts toward the tournament score. Set to `0` to include the criterion in the output without it affecting the winner. |

### Available template variables

| Variable | Replaced with |
|----------|--------------|
| `{{extensibility_scenario}}` | The `extensibility_scenario` from the task front-matter |
| `{{task_description}}` | The full body of the task file |

### Built-in criteria

`autobuild init` copies four starter criteria:

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `extensibility` | 1.5 | How well the design accommodates the task's extensibility scenario |
| `simplicity` | 1.0 | Absence of incidental complexity |
| `faithfulness` | 0 | Coverage of the task's requirements (informational, zero weight by default) |
| `modularity` | 0 | Separation of concerns (informational, zero weight by default) |

`faithfulness` and `modularity` are weighted at `0` by default because faithfulness is better enforced as an LLM gate (blocking), and modularity is often context-dependent. Raise their weights in your own project if you want them to influence the winner.

### Tournament mechanics

The judge runs every pair of surviving variations against every criterion. Each criterion comparison yields a winner (`A`, `B`, or `tie`). Scores accumulate based on criterion weight, and the variation with the highest total score wins. Full comparison reasoning is archived in `.autobuild/results/<id>/results.json`.

### Configuring the judge agent

By default the judge uses `default_agent`. Override with:

```yaml
judge:
  agent: claude
  model: "claude-opus-4-5"
```

This is useful when your implementation variations use the same agent and you want an independent, unbiased evaluator.

---

## 7. Running Autobuild

### Run the next task

```bash
autobuild run
```

Picks the first task in `.autobuild/backlog/` that either has no result yet, or has an incomplete result (status `in_progress` or `judging`). Incomplete tasks are automatically resumed: variations that already succeeded are carried forward and only the remaining ones are re-run.

### Run all tasks

```bash
autobuild run --all
```

### Run a specific task

```bash
autobuild run --task 002
```

Re-runs task `002` even if results already exist.

### Auto-commit winners

```bash
autobuild run --all --auto-commit
```

After each successful task, commits the winning changes with an auto-generated message. Requires `--all`.

### Keep workspaces for inspection

```bash
autobuild run --keep-workspaces
```

Normally Autobuild deletes the temporary workspace directories after a run. This flag keeps them so you can diff variations, inspect intermediate states, or debug gate failures.

### Specify a different repository root

`--repo-root` is a global flag that must appear **before** the subcommand:

```bash
autobuild --repo-root /path/to/repo run
autobuild --repo-root /path/to/repo run --all
```

Default is the current working directory.

### What happens during a run

1. Autobuild loads the next task that is unbuilt or incomplete from the backlog.
2. Up to three workspace copies of your `src_dir` are created in a temp directory (one per variation instruction). If resuming an interrupted run, workspaces for already-successful variations are reused as-is.
3. Each variation's agent runs in its workspace with the task description and its variation prompt, in parallel. As each variation finishes, its result is written to `.autobuild/results/<id>/results.json` with status `in_progress`, enabling resume if the process is interrupted.
4. Shell quality gates run inside each workspace after the agent finishes. Failures are fed back to the agent as context for a retry.
5. LLM quality gates evaluate each workspace that passed the shell gates.
6. Surviving workspaces enter the judge tournament. The result file is updated to status `judging` before the tournament starts, so a crash here resumes at the judging step without re-running agents.
7. The files the winning agent changed or created (identified via `git diff` inside the workspace) are applied back into your repository's `src_dir`. Files the agent deleted are removed. Files it never touched are left alone.
8. Results are archived with status `complete` in `.autobuild/results/<id>/results.json`.

---

## 8. Extending to support more agent CLIs

Autobuild's agent system is driven entirely by command templates in `config.yaml`. Any CLI tool that can accept a prompt, work in a directory, and exit with a non-zero code on failure can be plugged in.

### Agent configuration schema

```yaml
agents:
  my-agent:
    implement_command: "<command template for implementation>"
    compare_command:   "<command template for judge comparisons>"
    model: "<default model name>"
```

### Placeholder reference

| Placeholder | Replaced with |
|-------------|--------------|
| `{prompt}` | The full prompt string (task + variation instruction) |
| `{workspace}` | Absolute path to the workspace directory |
| `{model}` | The model name from the agent config or variation override |
| `{VARNAME}` | The value of any environment variable named `VARNAME` |
| `[--flag {VARNAME}]` | The whole block is omitted if `VARNAME` is unset |

### Adding a new agent

**Step 1**: Verify the CLI works non-interactively in a directory:

```bash
my-agent --non-interactive --dir /tmp/test "Create a hello.txt file"
```

**Step 2**: Add an entry to `config.yaml`:

```yaml
agents:
  my-agent:
    implement_command: "my-agent --non-interactive --dir {workspace} --model {model} {prompt}"
    compare_command:   "my-agent --non-interactive --read-only --dir {workspace} --model {model} {prompt}"
    model: "my-agent-default-model"
```

**Step 3**: Set it as the default or use it in specific variations:

```yaml
# Use as default for all variations
default_agent: my-agent

# Or use for specific variations only
default_variation_instructions:
  - agent: my-agent
    prompt: "You are a minimalist."
  - agent: claude
    prompt: "You are an architect."
```

### Notes on `implement_command` vs `compare_command`

- `implement_command` is invoked during implementation. The agent has full write access to `{workspace}`.
- `compare_command` is invoked by the judge when comparing two workspaces. The agent should operate in read-only or plan mode, inspecting `{workspace}` to evaluate rather than modify code.

For agents that don't have a distinct read-only mode, you can point both to the same command, but results may be less reliable if the agent modifies files during comparison.

### Mixing agents across variations

You can run different agent CLIs for different variations of the same task:

```yaml
default_variation_instructions:
  - agent: claude
    model: "claude-sonnet-4-5"
    prompt: "Think carefully about edge cases."
  - agent: aider
    model: "openrouter/anthropic/claude-3.5-sonnet"
    prompt: "Prioritise code reuse."
  - agent: cursor
    prompt: "Follow the existing patterns in the codebase closely."
```

Each variation runs its own agent in its own workspace, fully in parallel.
