from pathlib import Path
from typing import List, Literal, Mapping, Optional, TypedDict, cast

import click
import yaml
from toolz import pluck

APP_NAME = "camundactl"


class ContextAuthDict(TypedDict):
    user: str
    password: str


class EngineDict(TypedDict):
    name: Optional[str]
    url: str
    auth: ContextAuthDict
    verify: bool


CommandAliasLookup = Mapping[str, str]


class ConfigDict(TypedDict):
    version: str
    current_engine: Optional[str]
    engines: List[EngineDict]
    extra_paths: Optional[List[str]]
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR"]]
    alias: Optional[CommandAliasLookup]


CAMUNDA_CONFIG_FILE = "config"


NEW_CONTEXT_TEMPATE = ConfigDict(
    version="beta1", current_engine=None, engines=[], log_level="ERROR", extra_paths=[]
)


def _get_configfile() -> Path:
    app_dir = click.get_app_dir(APP_NAME)
    return Path(app_dir) / "config.yml"


def _write_context(config: ConfigDict) -> None:
    config_file = _get_configfile()
    with open(config_file, "w") as fh:
        yaml.dump(config, fh)


def _ensure_configfile() -> None:
    config_file = _get_configfile()
    if not config_file.exists():
        app_dir = Path(click.get_app_dir(APP_NAME))
        app_dir.mkdir(parents=True, exist_ok=True)
        _write_context(NEW_CONTEXT_TEMPATE)


def load_config() -> ConfigDict:
    _ensure_configfile()
    config_file = _get_configfile()
    with open(config_file, "r") as fh:
        return cast(ConfigDict, yaml.load(fh, Loader=yaml.FullLoader))


def add_engine(engine: EngineDict, select: bool = False) -> None:
    config = load_config()
    engines = list(pluck("name", config["engines"]))
    if engine["name"] in engines:
        raise Exception("Engine with name '%s' already exists." % engine["name"])
    config["engines"].append(engine)
    if select:
        config["current_engine"] = engine["name"]

    _write_context(config)


def remove_engine(name: str) -> None:
    config = load_config()

    config["engines"] = [e for e in config["engines"] if e["name"] != name]

    if config["current_engine"] == name:
        config["current_engine"] = None

    _write_context(config)


def activate_engine(name: str) -> None:
    context = load_config()
    engine_names = list(pluck("name", context["engines"]))
    if name not in engine_names:
        raise Exception(
            "invalid engine name '%s'. choose one of %s."
            % (name, ", ".join(engine_names))
        )

    context["current_engine"] = name

    _write_context(context)
