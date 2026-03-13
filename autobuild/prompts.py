"""Shared prompt construction and response parsing for all LLM implementations.

Any LLM backend should use these helpers so that prompts and response
parsing remain consistent regardless of the underlying provider.
"""

import json
import textwrap
from pathlib import Path

from json_repair import repair_json

from .models import Task

_MAX_FILE_BYTES = 50_000  # per-file cap to avoid oversized prompts

_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".go", ".rs", ".rb", ".c", ".cpp", ".h", ".hpp",
}

_IGNORE_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}


def build_implement_prompt(task: Task, instruction: str, context: str) -> str:
    """Return the prompt used to ask an LLM to implement *task*."""
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
        "The code will be judged based on simplicity, modularity, and extensibility.",
    ]
    return "\n".join(parts)


def build_compare_prompt(
    criterion_prompt: str,
    path_a: Path,
    path_b: Path,
    include_content: bool = True,
) -> str:
    """Return the prompt used to ask an LLM to compare two implementations.

    When *include_content* is False the file contents are omitted and the agent
    is expected to read the source files itself (e.g. the cursor agent which has
    built-in file-reading tools).
    """
    if include_content:
        a_body = collect_sources(path_a)
        b_body = collect_sources(path_b)
    else:
        a_body = f"Path: {path_a}"
        b_body = f"Path: {path_b}"
    return textwrap.dedent(f"""\
        {criterion_prompt}

        ## Implementation A

        {a_body}

        ## Implementation B

        {b_body}

        Respond with JSON only: {{"winner": "A" | "B" | "tie", "reasoning": "..."}}
    """)


def collect_sources(root: Path, max_bytes: int = _MAX_FILE_BYTES) -> str:
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


def parse_json_response(text: str) -> dict:
    """Extract and repair the first JSON object from an LLM response.

    Delegates to ``json-repair`` which handles markdown fences, single quotes,
    trailing commas, nested braces inside string values, and many other quirks
    produced by LLMs.
    """
    result = repair_json(text, return_objects=True)
    if isinstance(result, dict):
        return result
    raise ValueError(f"Could not parse JSON object from agent response:\n{text}")
