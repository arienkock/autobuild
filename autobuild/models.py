from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class AgentConfig:
    implement_command: str
    compare_command: str
    model: str


@dataclass(frozen=True)
class VariationInstruction:
    """Per-variation overrides: at least one of prompt, agent, or model must be set.

    - prompt: additional instruction text passed to the LLM
    - agent: agent name from config (falls back to default_agent when absent)
    - model: model override, replacing the agent's default model
    """

    prompt: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None

    def __post_init__(self) -> None:
        if not any([self.prompt, self.agent, self.model]):
            raise ValueError(
                "A VariationInstruction must specify at least one of: prompt, agent, model"
            )

    @classmethod
    def from_raw(cls, raw: "str | dict | VariationInstruction") -> "VariationInstruction":
        """Parse a raw YAML value (str or dict) or pass through an existing instance."""
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, str):
            return cls(prompt=raw)
        if isinstance(raw, dict):
            known = {k: v for k, v in raw.items() if k in {"prompt", "agent", "model"}}
            return cls(**known)
        raise ValueError(
            f"variation_instructions entries must be strings or dicts, got {type(raw).__name__}"
        )


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    description: str
    variation_instructions: list[VariationInstruction]
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
    default_variation_instructions: list[VariationInstruction] = None
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    default_agent: Optional[str] = None

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

