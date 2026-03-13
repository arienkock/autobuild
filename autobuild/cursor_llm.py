"""CursorLlm: wraps the `cursor-agent` CLI for LLM operations.

The `agent` binary (installed by https://cursor.com/install) is run in
non-interactive (--print) mode with --force so that it auto-approves all tool
uses without any human prompts.  The model defaults to ``"auto"`` so Cursor
selects the cheapest capable model automatically.
"""

import json
import os
import re
import shutil
import subprocess
import textwrap
import threading
import time
from pathlib import Path
from typing import Any

from .models import Task

_MAX_FILE_BYTES = 50_000  # per-file cap to avoid oversized prompts


class CursorLlm:
    """LLM backed by the ``cursor-agent`` CLI.

    Runs with ``--print --force`` by default so that all tool calls are
    auto-approved (no interactive confirmation required).

    Args:
        api_key: Cursor API key forwarded via ``--api-key``.  Falls back to
            the ``CURSOR_API_KEY`` environment variable when not provided.
        model: Model name forwarded via ``--model``.  Defaults to ``"auto"``
            so Cursor picks the cheapest capable model automatically.
        extra_args: Additional CLI arguments inserted before the prompt.
        agent_bin: Path to the ``agent`` binary.  Defaults to discovering it
            via PATH then ``~/.local/bin/agent``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        extra_args: list[str] | None = None,
        agent_bin: str | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("CURSOR_API_KEY")
        self._model = model if model is not None else "auto"
        self._extra_args = extra_args or []
        self._agent_bin = agent_bin or _find_agent_bin()

    def implement(
        self,
        task: Task,
        instruction: str,
        context: str,
        workspace_path: Path,
    ) -> None:
        """Ask the agent to implement *task* inside *workspace_path*."""
        prompt = _build_implement_prompt(task, instruction, context)
        label = workspace_path.name  # e.g. "variation-a"
        _run_agent(
            prompt=prompt,
            bin=self._agent_bin,
            api_key=self._api_key,
            workspace=workspace_path,
            model=self._model,
            extra_args=self._extra_args,
            force=True,
            heartbeat_label=label,
        )

    def compare(self, prompt: str, path_a: Path, path_b: Path) -> dict[str, Any]:
        """Ask the agent to compare two implementations and return a winner."""
        full_prompt = _build_compare_prompt(prompt, path_a, path_b)
        output = _run_agent(
            prompt=full_prompt,
            bin=self._agent_bin,
            api_key=self._api_key,
            model=self._model,
            extra_args=["--mode", "ask"] + self._extra_args,
            force=False,
        )
        return _parse_json_response(output)


# ── private helpers ───────────────────────────────────────────────────────────


def _find_agent_bin() -> str:
    """Return the path to the ``agent`` binary or raise if not found."""
    if found := shutil.which("agent"):
        return found
    fallback = Path.home() / ".local" / "bin" / "agent"
    if fallback.exists():
        return str(fallback)
    raise FileNotFoundError(
        "cursor-agent not found. Install it with:\n"
        "  curl -sS https://cursor.com/install | bash\n"
        "then ensure ~/.local/bin is on your PATH."
    )


_HEARTBEAT_INTERVAL = 5  # seconds between heartbeat prints


def _run_agent(
    prompt: str,
    bin: str,
    api_key: str | None = None,
    workspace: Path | None = None,
    model: str | None = None,
    extra_args: list[str] | None = None,
    force: bool = True,
    heartbeat_label: str | None = None,
) -> str:
    cmd = [bin, "--print", "--trust"]
    if force:
        cmd.append("--force")
    if api_key:
        cmd.extend(["--api-key", api_key])
    if workspace:
        cmd.extend(["--workspace", str(workspace)])
    if model:
        cmd.extend(["--model", model])
    cmd.extend(extra_args or [])
    cmd.append(prompt)

    if heartbeat_label is not None:
        return _run_agent_with_heartbeat(cmd, heartbeat_label)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"cursor-agent failed (exit {result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )
    return result.stdout


def _run_agent_with_heartbeat(cmd: list[str], label: str) -> str:
    """Run *cmd*, printing a heartbeat line every few seconds while it runs."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    start = time.monotonic()
    stop_event = threading.Event()

    def _heartbeat() -> None:
        while not stop_event.wait(timeout=_HEARTBEAT_INTERVAL):
            elapsed = int(time.monotonic() - start)
            print(f"  [{label}] ⟳ still running ({elapsed}s)…", flush=True)

    hb_thread = threading.Thread(target=_heartbeat, daemon=True)
    hb_thread.start()
    try:
        stdout, _ = proc.communicate()
    finally:
        stop_event.set()
        hb_thread.join()

    if proc.returncode != 0:
        raise RuntimeError(
            f"cursor-agent failed (exit {proc.returncode}):\n{stdout}"
        )
    return stdout


def _build_implement_prompt(task: Task, instruction: str, context: str) -> str:
    parts = [
        f"Task: {task.title}",
        f"Description: {task.description}",
        "",
        f"Instruction: {instruction}",
    ]
    if context.strip():
        parts += ["", "Context:", context]
    parts += [
        "",
        "Implement the feature described above.",
        "Write all necessary code files in the workspace.",
    ]
    return "\n".join(parts)


def _build_compare_prompt(criterion_prompt: str, path_a: Path, path_b: Path) -> str:
    a_listing = _collect_sources(path_a)
    b_listing = _collect_sources(path_b)
    return textwrap.dedent(f"""\
        {criterion_prompt}

        ## Implementation A

        {a_listing}

        ## Implementation B

        {b_listing}

        Respond with JSON only: {{"winner": "A" | "B" | "tie", "reasoning": "..."}}
    """)


_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".go", ".rs", ".rb", ".c", ".cpp", ".h", ".hpp",
}

_IGNORE_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}


def _collect_sources(root: Path, max_bytes: int = _MAX_FILE_BYTES) -> str:
    """Return a concatenated markdown listing of source files under *root*/src."""
    src = root / "src"
    search_root = src if src.exists() else root
    parts: list[str] = []
    for p in sorted(search_root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in _IGNORE_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in _SOURCE_EXTENSIONS:
            continue
        rel = p.relative_to(root)
        content = p.read_text(errors="replace")
        if len(content) > max_bytes:
            content = content[:max_bytes] + "\n... (truncated)"
        lang = p.suffix.lstrip(".")
        parts.append(f"### {rel}\n```{lang}\n{content}\n```")
    return "\n\n".join(parts) if parts else "(no source files found)"


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract the first ``{...}`` JSON object from *text*."""
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in agent response:\n{text}")
    return json.loads(match.group())
