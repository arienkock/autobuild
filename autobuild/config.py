from pathlib import Path

import yaml

from .models import Config

_DEFAULT_QUALITY_GATES = ["python -m pytest --tb=short -q"]


def load_config(repo_root: Path) -> Config:
    path = repo_root / ".autobuild" / "config.yaml"
    data: dict = yaml.safe_load(path.read_text()) if path.exists() else {}
    return Config(
        quality_gates=data.get("quality_gates", _DEFAULT_QUALITY_GATES),
    )
