from typing import Any, Dict

import click

from camundactl.client import Client
from camundactl.cmd.base import AliasCommand, describe, get
from camundactl.cmd.helpers import with_output_factory, with_query_option_factory

PROCESS_INSTANCE_FILTER_PARAMS = []


@get.command(
    "processInstance",
    help="lists all active process instances",
    alias=["pi"],
    cls=AliasCommand,
)
@with_output_factory(
    default_table_headers=["id", "businessKey", "definitionId", "suspended"]
)
@with_query_option_factory(options=PROCESS_INSTANCE_FILTER_PARAMS, name="params")
@click.pass_context
def get_process_instance(ctx: click.Context, params: Dict, **kwargs) -> None:
    client: Client = ctx.obj["client"]
    path = "/process-instance"
    resp = client.get(path, params=params)
    return resp.json()


DESCRIBE_DEFAULT_TEMPLATE = """
Process Instance

Id: {{id}}
""".strip()


@describe.command("processInstance", help="describe one process instance")
@with_output_factory(
    allow=["template", "json"],
    default="template",
    default_template=DESCRIBE_DEFAULT_TEMPLATE,
)
@click.argument("process_instance_id", nargs=1)
@click.pass_context
def describe_process_instance(ctx: click.Context, process_instance_id: str, **kwargs):
    client: Client = ctx.obj["client"]
    path = f"/process-instance/{process_instance_id}"
    params: Dict[str, Any] = {}
    resp = client.get(path, params=params)
    return resp.json()
