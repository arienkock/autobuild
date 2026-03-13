## Autobuild

**Autobuild** is an agentic development framework that automates the
implementation and evaluation of software features.

Given a backlog of manually authored tasks, Autobuild:

- **Spins up three parallel agents** — each pursuing a different implementation
  strategy derived from the task.
- **Runs quality gates** (e.g. tests, coverage, lint) inside isolated workspaces.
- **Runs a tournament-style design review** using LLM-judged criteria weighted
  toward simplicity, modularity, and extensibility.
- **Applies the winning implementation** back onto the main repository.

### Repository layout

- `autobuild/` – core library
  - `models.py` – shared dataclasses and types
  - `task_loader.py` – load backlog YAML into `Task`
  - `workspace.py` – workspace provisioning and teardown
  - `agent.py` – implement + gate loop per variation
  - `judge/engine.py` – generic pairwise tournament over criteria
  - `orchestrator.py` – top-level loop across backlog
  - `cli.py` – command-line entry point
- `backlog/` – example backlog YAML files
- `.autobuild/` – configuration and results storage

See `DESIGN.md` for the full design narrative.

### Usage

Install the package in editable mode and run the CLI:

```bash
pip install -e .
autobuild --help
```

To actually run tasks you will need to wire in a real LLM client by replacing
`autobuild.llm.create_default_llm` with your own implementation and ensuring
your repo under test contains the `src/` tree and tests referenced by your
backlog tasks.

