import importlib
import logging
from typing import List, Optional, Union

import click

from camundactl.client import Client, create_session
from camundactl.context import load_context


class AliasGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        for cmd_other_name in self.list_commands(ctx):
            cmd = super().get_command(ctx, cmd_other_name)
            alias = getattr(cmd, "alias", None)
            if alias is None:
                continue
            if isinstance(alias, list) and cmd_name in alias:
                return cmd
            if isinstance(alias, str) and cmd_name == alias:
                return cmd
        return None


class AliasCommand(click.MultiCommand):
    def __init__(self, *args, alias: Union[str, List[str]], **kwargs):
        super().__init__(*args, **kwargs)
        self.alias = alias


@click.group(cls=AliasGroup)
@click.option(
    "-l", "--log-level", "log_level", help="activates the logger with the given level"
)
@click.option("-e", "--engine", "engine", help="define the engine name to be used")
@click.pass_context
def root(ctx: click.Context, log_level: Optional[str], engine: Optional[str]):
    if log_level is not None:
        assert log_level in ("DEBUG", "INFO", "WARN", "WARNING", "ERROR")
        logging.basicConfig(level=getattr(logging, log_level))
    ctx.ensure_object(dict)

    ctx.obj["log_level"] = log_level
    ctx.obj["selected_engine"] = engine


@root.group(cls=AliasGroup, help="query resources of camunda engine")
@click.pass_context
def get(ctx: click.Context):
    ctx.ensure_object(dict)
    _ensure_client(ctx, ctx.obj.get("selected_engine"))


@root.group(
    cls=AliasGroup, help="get complex collected information about engine ressources"
)
@click.pass_context
def describe(ctx: click.Context):
    ctx.ensure_object(dict)
    _ensure_client(ctx, ctx.obj.get("selected_engine"))


@root.group(cls=AliasGroup, help="delete ressources")
@click.pass_context
def delete(ctx: click.Context):
    ctx.ensure_object(dict)
    _ensure_client(ctx, ctx.obj.get("selected_engine"))


@root.group(cls=AliasGroup, help="apply changes to the engine")
@click.pass_context
def apply(ctx: click.Context):
    ctx.ensure_object(dict)
    _ensure_client(ctx, ctx.obj.get("selected_engine"))


def _ensure_client(ctx: click.Context, selected_engine: Optional[str] = None):
    ctx.ensure_object(dict)
    config = load_context()
    client = None

    if not config["engines"]:
        raise Exception("invalid configuration")

    if selected_engine is None:
        selected_engine = config.get("current_engine")
        if not selected_engine:
            raise Exception("no current and no given engine")

    for engine in config["engines"]:
        if selected_engine == engine["name"]:
            client = Client(create_session(engine), engine["url"])
            break
    else:
        raise Exception(f"no engine with name: {selected_engine}")

    ctx.obj["config"] = config
    ctx.obj["client"] = client


def autodiscover(paths):
    for path in paths:
        importlib.import_module(path)


from camundactl.cmd import config  # noqa
from camundactl.cmd import openapi  # noqa

# import custom modules and overrides
autodiscover(load_context().get("extra_paths", []))
