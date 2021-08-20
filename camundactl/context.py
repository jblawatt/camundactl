from typing import Optional, TypedDict, List
from pathlib import Path
import yaml
import typer


ContextAuthDict = TypedDict("ContextAuthDict", {"user": str, "password": str})


class EngineDict(TypedDict):
    name: Optional[str]
    url: str
    auth: ContextAuthDict
    verify: bool
    default: Optional[bool]


class ContextDict(TypedDict):
    version: str
    current_engine: Optional[str]
    engines: List[EngineDict]


CAMUNDA_CONFIG_FILE = "config"


def load_context() -> ContextDict:
    app_dir = typer.get_app_dir("Camunda")
    config_file = Path(app_dir) / "config.yml"
    with open(config_file, "r") as fh:
        context = yaml.load(fh, Loader=yaml.FullLoader)

    return context
