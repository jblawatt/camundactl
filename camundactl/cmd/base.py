import importlib
import logging
from functools import cache
from typing import Mapping, Optional

import click

from camundactl.client import Client, create_session
from camundactl.config import ConfigDict, load_config

try:
    from rainbow_logging_handler import RainbowLoggingHandler as DefaultLogHandler
except ImportError:
    from logging import StreamHandler as DefaultLogHandler


LookupDict = Mapping[str, str]


class AliasGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cache
    def get_alias_lookup(self) -> LookupDict:
        return load_config().get("alias", {})

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """
        override default with the functionalitity
        to lookup for aliases
        """
        if cmd := super().get_command(ctx, cmd_name):
            return cmd
        alias_lookup = self.get_alias_lookup()
        if alias_name := alias_lookup.get(cmd_name):
            if cmd := super().get_command(ctx, alias_name):
                return cmd
        for cmd_other_name in self.list_commands(ctx):
            cmd = super().get_command(ctx, cmd_other_name)
            if alias := getattr(cmd, "alias", None):
                if isinstance(alias, list) and cmd_name in alias:
                    return cmd
                if isinstance(alias, str) and cmd_name == alias:
                    return cmd
        return None


@click.group(cls=AliasGroup)
@click.option(
    "-l",
    "--log-level",
    "log_level",
    type=click.Choice(["DEBUG", "WARNING", "INFO", "ERROR"], case_sensitive=False),
    default=None,
    required=False,
)
@click.pass_context
def root(ctx: click.Context, log_level: Optional[str] = None) -> None:
    ctx.ensure_object(dict)
    config_ = load_config()
    if log_level or (log_level := config_.get("log_level", "")):
        import sys

        logging.basicConfig(
            level=getattr(logging, log_level), handlers=[DefaultLogHandler(sys.stdout)]
        )


def _group_factory(parent, parent_kwargs):
    @parent.group(**parent_kwargs)
    @click.pass_context
    @click.option("-e", "--engine", "engine", required=False)
    def group(ctx: click.Context, engine: Optional[str]):
        config_ = load_config()
        engine = engine or config_.get("current_engine")
        logging.debug("using engine %s", engine)
        client = _create_client(config_, engine)
        ctx.obj["client"] = client
        ctx.obj["config"] = config

    return group


def _create_client(config_: ConfigDict, selected_engine: Optional[str] = None):

    if not config_["engines"]:
        raise Exception("invalid configuration")

    if selected_engine is None:
        selected_engine = config_.get("current_engine")
        if not selected_engine:
            raise Exception("no current and no given engine")

    for engine in config_["engines"]:
        if selected_engine == engine["name"]:
            return Client(create_session(engine), engine["url"])
    else:
        raise Exception(f"no engine with name: {selected_engine}")


get = _group_factory(
    root,
    dict(
        name="get",
        cls=AliasGroup,
        help="query resources of camunda engine",
    ),
)


describe = _group_factory(
    root,
    dict(
        name="describe",
        cls=AliasGroup,
        help="get complex collected information about engine ressources",
    ),
)


delete = _group_factory(
    root,
    dict(
        name="delete",
        cls=AliasGroup,
        help="delete ressources",
    ),
)


apply = _group_factory(
    root,
    dict(
        name="apply",
        cls=AliasGroup,
        help="apply changes to the engine",
    ),
)


def autodiscover(paths):
    for path in paths:
        importlib.import_module(path)


from camundactl.cmd import config  # noqa
from camundactl.cmd import info  # noqa
from camundactl.cmd import openapi  # noqa

# TODO: with specifix openapi version
openapi.load()
from camundactl.cmd import process_instance  # noqa

# import custom modules and overrides
autodiscover(load_config().get("extra_paths", []))
