from pathlib import Path
from typing import List, Optional, TypedDict

import click
import yaml
from toolz import pluck

ContextAuthDict = TypedDict("ContextAuthDict", {"user": str, "password": str})


class EngineDict(TypedDict):
    name: Optional[str]
    url: str
    auth: ContextAuthDict
    verify: bool


class ContextDict(TypedDict):
    version: str
    current_engine: Optional[str]
    engines: List[EngineDict]


CAMUNDA_CONFIG_FILE = "config"


def _get_configfile() -> Path:
    app_dir = click.get_app_dir("Camunda")
    return Path(app_dir) / "config.yml"


def _write_context(context: ContextDict):
    config_file = _get_configfile()
    with open(config_file, "w") as fh:
        context = yaml.dump(context, fh)


def load_context() -> ContextDict:
    config_file = _get_configfile()
    with open(config_file, "r") as fh:
        context = yaml.load(fh, Loader=yaml.FullLoader)

    return context


def add_engine(engine: EngineDict, select: bool = False):
    context = load_context()
    engines = list(pluck("name", context["engines"]))
    if engine["name"] in engines:
        raise Exception("Engine with name '%s' already exists." % engine["name"])
    context["engines"].append(engine)
    if select:
        context["current_engine"] = engine["name"]

    _write_context(context)


def remove_engine(name: str):
    context = load_context()

    context["engines"] = [e for e in context["engines"] if e["name"] != name]

    if context["current_engine"] == name:
        context["current_engine"] = None

    _write_context(context)


def activate_engine(name: str):
    context = load_context()
    engine_names = list(pluck("name", context["engines"]))
    if name not in engine_names:
        raise Exception(
            "invalid engine name '%s'. choose one of %s."
            % (name, ", ".join(engine_names))
        )

    context["current_engine"] = name

    _write_context(context)
