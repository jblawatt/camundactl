from typing import Optional

import click
from tabulate import tabulate

from camundactl.cmd.base import AliasGroup, root
from camundactl.cmd.helpers import with_exception_handler
from camundactl.config import (
    activate_engine,
    add_alias,
    add_engine,
    get_alias,
    get_configfile,
    load_config,
    remove_alias,
    remove_engine,
)


@root.group("config", cls=AliasGroup, help="change engines configuration")
def config_cmd():
    pass


@config_cmd.command("get-engines")
@with_exception_handler()
def get_engines():
    context = load_config()
    for engine in context["engines"]:
        is_current = engine["name"] == context.get("current_engine")
        print(engine["name"] + (" *" if is_current else ""))


@config_cmd.command("add-engine")
@click.argument("name")
@click.argument("url")
@click.option(
    "-u", "--user", "user", default=None, required=False, help="Username for Basic Auth"
)
@click.option(
    "-p",
    "--password",
    "password",
    default=None,
    required=False,
    help="Password for Basic Auth",
)
@click.option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    required=False,
    default=False,
    help="directly select this context",
)
@click.option(
    "--no-verify", "no_verify", default=False, required=False, help="do not verify ssl"
)
@with_exception_handler()
def add_engine(
    name: str,
    url: str,
    user: Optional[str],
    password: Optional[str],
    select: bool,
    no_verify: bool,
):

    new_engine = {"name": name, "url": url, "verify": not no_verify}
    if user and password:
        new_engine["auth"] = {"user": user, "password": password}
    add_engine(new_engine, select)


@config_cmd.command("remove-engine")
@click.argument("name")
@with_exception_handler()
def remove(name: str):
    remove_engine(name)


@config_cmd.command("activate-engine")
@click.argument("name")
@with_exception_handler()
def activate(name: str):
    activate_engine(name)


@config_cmd.command("get-alias")
@with_exception_handler()
def get_alias_cmd():
    click.echo(tabulate(get_alias().items(), headers=("Alias", "Command")))


@config_cmd.command("add-alias")
@click.argument("command")
@click.argument("alias")
@with_exception_handler()
def add_alias_cmd(alias: str, command: str) -> None:
    add_alias(alias, command)


def _alias_shell_complete(ctx: click.Context, param: str, incomplete: str) -> list[str]:
    result: list[str] = []
    for alias in load_config().get("alias", {}).keys():
        if incomplete:
            if alias.startswith(incomplete):
                result.append(alias)
        else:
            result.append(alias)
    return result


@config_cmd.command("remove-alias")
@click.argument("alias", autocompletion=_alias_shell_complete)
@with_exception_handler()
def remove_alias_cmd(alias: str) -> None:
    remove_alias(alias)


@config_cmd.command("edit")
@click.option(
    "-e",
    "--editor",
    "editor",
    required=False,
    help="Specify the editor you want to use",
)
@with_exception_handler()
def edit_config(editor: Optional[str]) -> None:
    click.edit(editor=editor, filename=get_configfile(), require_save=True)
