import importlib
import logging
import sys
from typing import Mapping, Optional

import click

from camundactl.client import create_client
from camundactl.config import ConfigDict, load_config

try:
    from rainbow_logging_handler import RainbowLoggingHandler as DefaultLogHandler
except ImportError:
    from logging import StreamHandler as DefaultLogHandler


logger = logging.getLogger(__name__)

LookupDict = Mapping[str, str]


class AliasGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        logging.basicConfig(
            level=getattr(logging, log_level), handlers=[DefaultLogHandler(sys.stdout)]
        )


def _group_factory(parent, parent_kwargs):
    @parent.group(**parent_kwargs)
    @click.pass_context
    @click.option("-e", "--engine", "engine", required=False)
    def group(ctx: click.Context, engine: Optional[str]):
        prepare_context(ctx, engine=engine)

    return group


def prepare_context(ctx: click.Context, engine: Optional[str] = None) -> None:
    """builds up the context with config and client instance"""
    ctx.ensure_object(dict)
    config_ = load_config()
    ctx.obj["config"] = config_
    ctx.obj["client"] = create_client(config_, selected_engine=engine)


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


def init():
    for module_name in (
        "camundactl.cmd.config",
        "camundactl.cmd.info",
        "camundactl.cmd.openapi",
        "camundactl.cmd.openapi.schema",
        "camundactl.cmd.process_instance",
    ):
        module = importlib.import_module(module_name)
        if hasattr(module, "register_commands"):
            module.register_commands()

    # import custom modules and overrides
    config_ = load_config()
    for path in config_.get("extra_paths", []):
        importlib.import_module(path)


init()
