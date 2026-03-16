# Installation

## Prerequisites

**Python 3.11 or later** is required. Check your version:

```bash
python3 --version
```

If you don't have it, install via [python.org](https://www.python.org/downloads/) or Homebrew:

```bash
brew install python@3.11
```

**pip** ships with Python. Verify it's available:

```bash
pip3.11 --version
```

---

## Option A: Install globally (simplest)

If you're happy to install Autobuild into your system or user Python environment, this is the fastest path:

```bash
pip3.11 install git+https://github.com/arienkock/autobuild.git
```

Or, if you've cloned the repository:

```bash
git clone https://github.com/arienkock/autobuild.git
cd autobuild
pip3.11 install .
```

This places the `autobuild` command on your `PATH` and you can run it from any directory.

---

## Option B: Install inside a virtual environment (recommended)

Using a virtual environment keeps Autobuild's dependencies isolated from the rest of your Python installation and prevents version conflicts.

### Create and activate the environment

```bash
# Create a venv in the autobuild repo directory (or anywhere you like)
python3.11 -m venv .venv

# Activate it — macOS / Linux
source .venv/bin/activate

# Activate it — Windows
.venv\Scripts\activate
```

Your shell prompt will show `(.venv)` when the environment is active.

### Install Autobuild into the venv

```bash
pip install git+https://github.com/arienkock/autobuild.git
```

Or from a local clone:

```bash
pip install .
```

### Verify the installation

```bash
autobuild --version
```

### Deactivating

```bash
deactivate
```

> **Tip:** If you use a venv, remember to activate it each time before calling `autobuild`. Alternatively, you can reference the executable directly: `.venv/bin/autobuild`.

---

## Development install (editable mode)

If you're contributing to or experimenting with Autobuild itself, install in editable mode so that changes to the source take effect immediately:

```bash
pip install -e ".[dev]"
```

The `[dev]` extra pulls in `pytest` so you can run the test suite:

```bash
pytest
```

---

## Initializing a project

Once installed, go to the repository you want Autobuild to work on and run:

```bash
cd /path/to/your-repo
autobuild init
```

This creates a `.autobuild/` directory containing:

| Path | Purpose |
|------|---------|
| `config.yaml` | Main configuration: agent, gates, criteria, timeouts |
| `backlog/001-example.md` | Starter task — edit or delete |
| `gates/` | LLM quality gate prompts (`.md` files) |
| `criteria/` | Judge criteria prompts (`.md` files) |

From here, see [USAGE.md](USAGE.md) for how to configure agents, write tasks, and run the tool.
