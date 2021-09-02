from typing import Optional

import click

from camundactl.cmd.base import root
from camundactl.cmd.helpers import with_exception_handler
from camundactl.context import activate_engine, add_engine, load_context, remove_engine


@root.group("config")
def config():
    pass


@config.group("engines")
def engines():
    pass


@engines.command("ls")
@with_exception_handler()
def list_():
    context = load_context()
    for engine in context["engines"]:
        is_current = engine["name"] == context.get("current_engine")
        print(engine["name"] + (" *" if is_current else ""))


@engines.command("add")
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
def add(
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


@engines.command("remove")
@click.argument("name")
@with_exception_handler()
def remove(name: str):
    remove_engine(name)


@engines.command("activate")
@click.argument("name")
@with_exception_handler()
def activate(name: str):
    activate_engine(name)
