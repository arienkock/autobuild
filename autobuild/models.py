from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    description: str
    context_files: list[str]
    variation_instructions: list[str]
    extensibility_scenario: str
    min_coverage: int = 80


@dataclass(frozen=True)
class Workspace:
    task_id: str
    variation: str  # "a", "b", "c"
    path: Path


@dataclass(frozen=True)
class Config:
    quality_gates: list[str]


@dataclass(frozen=True)
class AgentResult:
    success: bool
    workspace: Workspace
    reason: str  # failure cause or completion summary


@dataclass(frozen=True)
class Comparison:
    criterion: str
    winner: str  # "A", "B", or "tie"
    reasoning: str


@dataclass(frozen=True)
class JudgeResult:
    winner: Workspace
    comparisons: list[Comparison]
    reasoning: str  # human-readable summary of tournament

