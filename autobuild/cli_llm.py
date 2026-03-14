"""CliLlm: runs any CLI coding agent via configurable command templates.

Templates in config use placeholders {prompt}, {workspace}, {model} and
optional [...] groups that are dropped when their env vars are unset.
"""

import os
import re
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from .models import AgentConfig, Task
from .prompts import build_compare_prompt, build_implement_prompt, parse_json_response

_OPTIONAL_RE = re.compile(r"\[([^\]]*)\]")
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
_HEARTBEAT_INTERVAL = 5
_MAX_RETRIES = 5


def _interpolate(
    template: str,
    workspace: Path,
    prompt: str,
    model: str,
    **extra: Any,
) -> list[str]:
    """Two-pass: strip optional [...] groups with missing env vars, then substitute placeholders."""
    builtins = {"workspace": str(workspace), "prompt": prompt, "model": model,
                **{k: str(v) for k, v in extra.items()}}

    def _resolve(key: str) -> str:
        if key in builtins:
            return builtins[key]
        return os.environ.get(key, "")

    def _expand_optional(m: re.Match[str]) -> str:
        group = m.group(1)
        for key in _PLACEHOLDER_RE.findall(group):
            if key not in builtins and not os.environ.get(key):
                return ""
        return group

    stripped = _OPTIONAL_RE.sub(_expand_optional, template)
    tokens = shlex.split(stripped)
    return [_PLACEHOLDER_RE.sub(lambda m: _resolve(m.group(1)), t) for t in tokens]


class CliLlm:
    """LLM backed by an arbitrary CLI agent, configured via command templates."""

    def __init__(self, agent_config: AgentConfig) -> None:
        self._config = agent_config

    def implement(
        self,
        task: Task,
        instruction: str,
        context: str,
        workspace_path: Path,
    ) -> None:
        """Run the implement command template in *workspace_path*."""
        prompt = build_implement_prompt(task, instruction, context)
        cmd = _interpolate(
            self._config.implement_command,
            workspace=workspace_path,
            prompt=prompt,
            model=self._config.model,
        )
        if not cmd:
            raise RuntimeError("implement_command produced an empty command")
        label = workspace_path.parent.name
        _run_with_heartbeat(cmd, label, cwd=workspace_path)

    def compare(
        self,
        prompt: str,
        path_a: Path,
        path_b: Path,
        workspace: Path | None = None,
    ) -> dict[str, Any]:
        """Run the compare command template and return parsed JSON."""
        full_prompt = build_compare_prompt(prompt, path_a, path_b, include_content=False)
        work = workspace if workspace is not None else path_a
        cmd = _interpolate(
            self._config.compare_command,
            workspace=work,
            prompt=full_prompt,
            model=self._config.model,
            path_a=path_a,
            path_b=path_b,
        )
        if not cmd:
            raise RuntimeError("compare_command produced an empty command")
        output = _run(cmd, cwd=work)
        return parse_json_response(output)


def _agent_not_found_hint(prog: str) -> str:
    if prog == "agent":
        return " Install cursor-agent: curl -sS https://cursor.com/install | bash (then ensure ~/.local/bin is on PATH)."
    return ""


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    """Run *cmd*, return stdout. Retries on failure up to _MAX_RETRIES times."""
    try:
        for attempt in range(_MAX_RETRIES):
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
            if result.returncode == 0:
                return result.stdout
            output = result.stderr or result.stdout
            if attempt < _MAX_RETRIES - 1:
                time.sleep(1 + attempt)
                continue
            raise RuntimeError(f"Agent failed (exit {result.returncode}):\n{output}")
        raise RuntimeError("Agent failed after max retries")
    except FileNotFoundError as e:
        prog = cmd[0] if cmd else "?"
        hint = _agent_not_found_hint(prog)
        raise FileNotFoundError(
            e.errno,
            f"Agent binary {prog!r} not found.{hint}",
            prog,
        ) from e


def _run_with_heartbeat(cmd: list[str], label: str, cwd: Path | None = None) -> str:
    """Run *cmd*, print heartbeat every few seconds, retry on failure."""
    for attempt in range(_MAX_RETRIES):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd
            )
        except FileNotFoundError as e:
            prog = cmd[0] if cmd else "?"
            hint = _agent_not_found_hint(prog)
            raise FileNotFoundError(
                e.errno,
                f"Agent binary {prog!r} not found.{hint}",
                prog,
            ) from e
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

        if proc.returncode == 0:
            return stdout
        if attempt < _MAX_RETRIES - 1:
            time.sleep(1 + attempt)
            continue
        raise RuntimeError(f"Agent failed (exit {proc.returncode}):\n{stdout}")
    raise RuntimeError("Agent failed after max retries")
