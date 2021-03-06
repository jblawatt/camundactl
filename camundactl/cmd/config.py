from typing import List, Optional

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


def _engine_shell_completion(
    ctx: click.Context, param: str, incomplete: str
) -> List[str]:
    config = load_config()
    return sorted(
        [
            engine["name"]
            for engine in config["engines"]
            if engine["name"].startswith(incomplete)
        ]
    )


@config_cmd.command("get-engines")
@with_exception_handler()
def get_engines():
    context = load_config()
    engines = context["engines"]
    for engine in engines:
        is_current = engine["name"] == context.get("current_engine")
        if is_current:
            click.echo(click.style(engine["name"] + " *", bold=True, fg="yellow"))
        else:
            click.echo(engine["name"])
    if not engines:
        click.echo(click.style("no engines configured", fg="yellow"))


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
def add_engine_cmd(
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
@click.argument("name", autocompletion=_engine_shell_completion)
@with_exception_handler()
def remove(name: str):
    remove_engine(name)


@config_cmd.command("use-engine")
@click.argument("name", autocompletion=_engine_shell_completion)
@with_exception_handler()
def activate(name: str) -> None:
    activate_engine(name)
    click.echo("engine " + click.style(name, bold=True, fg="yellow") + " selected")


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
