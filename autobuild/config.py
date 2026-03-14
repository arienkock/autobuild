from pathlib import Path
from typing import Dict, Optional

import yaml

from .models import AgentConfig, Config

_DEFAULT_QUALITY_GATES = ["python -m pytest --tb=short -q"]
_DEFAULT_SRC_DIR = "src"


def _parse_agents(raw: Optional[dict]) -> Dict[str, AgentConfig]:
    if not raw:
        return {}
    result = {}
    for name, agent_data in raw.items():
        if isinstance(agent_data, dict):
            result[name] = AgentConfig(
                implement_command=agent_data.get("implement_command", ""),
                compare_command=agent_data.get("compare_command", ""),
                model=agent_data.get("model", ""),
            )
    return result


def load_config(repo_root: Path) -> Config:
    path = repo_root / ".autobuild" / "config.yaml"
    data: dict = yaml.safe_load(path.read_text()) if path.exists() else {}
    agents_raw = data.get("agents")
    return Config(
        quality_gates=data.get("quality_gates", _DEFAULT_QUALITY_GATES),
        src_dir=data.get("src_dir", _DEFAULT_SRC_DIR),
        default_variation_instructions=data.get("default_variation_instructions", []),
        agents=_parse_agents(agents_raw),
        default_agent=data.get("default_agent"),
    )
