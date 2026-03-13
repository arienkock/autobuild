from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    description: str
    variation_instructions: list[str]
    extensibility_scenario: str


@dataclass(frozen=True)
class Workspace:
    task_id: str
    variation: str  # "a", "b", "c"
    path: Path
    src_dir: str


@dataclass(frozen=True)
class Config:
    quality_gates: list[str]
    src_dir: str
    default_variation_instructions: list[str] = None

    def __post_init__(self):
        if self.default_variation_instructions is None:
            object.__setattr__(self, "default_variation_instructions", [])


@dataclass(frozen=True)
class AgentResult:
    success: bool
    workspace: Workspace
    reason: str  # failure cause or completion summary
    cpu_time_seconds: float = 0.0


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

