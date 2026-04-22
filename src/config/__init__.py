import yaml
from pathlib import Path

with open(Path(__file__).parent.parent.parent / "config.yml") as f:
    settings = yaml.safe_load(f)
