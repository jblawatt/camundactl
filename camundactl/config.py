import logging
from pathlib import Path
from typing import List, Literal, Optional, TypedDict, cast

import click
import yaml
from toolz import pluck

APP_NAME = "camundactl"


logger = logging.getLogger(__name__)


class ContextAuthDict(TypedDict):
    user: str
    password: str


class EngineDict(TypedDict):
    name: Optional[str]
    url: str
    auth: ContextAuthDict
    verify: bool
    spec_version: Optional[str]


CommandAliasLookup = dict[str, str]


class ConfigDict(TypedDict):
    version: str
    current_engine: Optional[str]
    engines: List[EngineDict]
    extra_paths: Optional[List[str]]
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR"]]
    alias: Optional[CommandAliasLookup]
    spec_version: Optional[str]
    extra_template_paths: Optional[list[str]]


CAMUNDA_CONFIG_FILE = "config"


NEW_CONTEXT_TEMPATE = ConfigDict(
    version="beta1",
    current_engine=None,
    engines=[],
    log_level="ERROR",
    extra_paths=[],
    alias={},
    spec_version=None,
    extra_template_paths=[],
)


def get_configfile() -> Path:
    app_dir = click.get_app_dir(APP_NAME)
    return Path(app_dir) / "config.yml"


def _write_config(config: ConfigDict) -> None:
    config_file = get_configfile()
    with open(config_file, "w") as fh:
        yaml.dump(config, fh)


def get_configdir() -> Path:
    return Path(click.get_app_dir(APP_NAME))


def _ensure_configfile() -> None:
    config_file = get_configfile()
    if not config_file.exists():
        app_dir = Path(click.get_app_dir(APP_NAME))
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "templates").mkdir(parents=True, exist_ok=True)
        _write_config(NEW_CONTEXT_TEMPATE)


def load_config() -> ConfigDict:
    _ensure_configfile()
    config_file = get_configfile()
    with open(config_file, "r") as fh:
        return cast(ConfigDict, yaml.load(fh, Loader=yaml.FullLoader))


def add_engine(engine: EngineDict, select: bool = False) -> None:
    config = load_config()
    engines = list(pluck("name", config["engines"]))
    if engine["name"] in engines:
        raise Exception(f"Engine with name '{engine['name']}' already exists.")
    config["engines"].append(engine)
    if select:
        config["current_engine"] = engine["name"]

    _write_config(config)


def remove_engine(name: str) -> None:
    config = load_config()

    config["engines"] = [e for e in config["engines"] if e["name"] != name]

    if config["current_engine"] == name:
        config["current_engine"] = None

    _write_config(config)


def activate_engine(name: str) -> None:
    config = load_config()
    engine_names = list(pluck("name", config["engines"]))
    if name not in engine_names:
        raise Exception(
            "invalid engine name '%s'. choose one of %s."
            % (name, ", ".join(engine_names))
        )

    config["current_engine"] = name

    _write_config(config)


def add_alias(alias: str, command: str) -> None:
    config = load_config()
    if "alias" not in config or config["alias"] is None:
        config["alias"] = {}
    config["alias"][alias] = command
    _write_config(config)
    logger.info("added alias %s for command %s", alias, command)


def remove_alias(alias: str) -> None:
    config = load_config()
    if "alias" not in config or config["alias"] is None:
        config["alias"] = {}
    try:
        del config["alias"][alias]
    except KeyError:
        logger.warning("alias %s should be deleted. but does not exist.", alias)
    else:
        logger.info("deleted alias %s", alias)
    _write_config(config)


def get_alias() -> dict[str, str]:
    config = load_config()
    return config.get("alias", {})
