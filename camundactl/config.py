import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional, TypedDict, cast

import click
import yaml
from toolz import pluck

APP_NAME = "camundactl"


logger = logging.getLogger(__name__)


class ContextAuthDict(TypedDict):
    user: str
    password: str


class EngineDict(TypedDict):
    name: str
    url: str
    auth: ContextAuthDict
    verify: bool
    spec_version: Optional[str]


CommandAliasLookup = dict[str, str]


class TemplateConfig(TypedDict):
    extra_paths: Optional[List[str]]
    extra_patterns: Optional[List[str]]


class ConfigDict(TypedDict):
    version: str
    current_engine: Optional[str]
    engines: List[EngineDict]
    extra_paths: Optional[List[str]]
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR"]]
    alias: Optional[CommandAliasLookup]
    spec_version: Optional[str]
    template: Optional[TemplateConfig]
    logging: Optional[Dict]


CAMUNDA_CONFIG_FILE = "config"


NEW_CONTEXT_TEMPATE = ConfigDict(
    version="beta1",
    current_engine=None,
    engines=[],
    log_level="ERROR",
    extra_paths=[],
    alias={},
    spec_version=None,
    template=None,
    logging=None,
)


class EngineAlreadyExistsError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"An engine with the name '{name}' already exists.")
        self.name = name


class EngineDoesNotExists(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"An engine with the name {name} does not exist.")
        self.name = name


def get_configfile() -> Path:
    app_dir = click.get_app_dir(APP_NAME)
    return Path(app_dir) / "config.yml"


def _write_config(config: ConfigDict) -> None:
    config_file = get_configfile()
    with open(config_file, "w") as fh:
        yaml.dump(config, fh)
    logger.info("config file written.")


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
    """
    Adds a new engine to the config file. Selects it as current
    engine if `selected` or if it is the first one.
    """
    config = load_config()
    engines = list(pluck("name", config["engines"]))
    if engine["name"] in engines:
        raise EngineAlreadyExistsError(engine["name"])
    config["engines"].append(engine)
    # activate if this is the first engine added
    if len(config["engines"]) == 1:
        logging.debug(
            "configuring the first engine. overruling the "
            "selection parameter and selecting it by default."
        )
        select = True
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
    """
    Activates the given engine as current_engine in the config file.
    """
    config = load_config()
    engine_names = list(pluck("name", config["engines"]))
    if name not in engine_names:
        raise EngineDoesNotExists(
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
    logger.info("added alias %s for command %s.", alias, command)


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
