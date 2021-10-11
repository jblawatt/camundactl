import json

import click
import yaml

from camundactl.cmd.base import root
from camundactl.cmd.helpers import with_exception_handler
from camundactl.cmd.openapi.base import load_spec


def _autocomplete_schema_names(
    ctx: click.Context, param: str, incomplete: str
) -> list[str]:
    spec = load_spec()
    keys = sorted(spec["components"]["schemas"].keys())
    autocomplete = []
    for key in keys:
        if incomplete:
            if key.startswith(incomplete):
                autocomplete.append(key)
        else:
            autocomplete.append(key)
    return autocomplete


@root.command("schema")
@click.argument("schema_name", type=str, autocompletion=_autocomplete_schema_names)
@click.option(
    "-f",
    "--format",
    "format_",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
)
@with_exception_handler()
@click.pass_context
def schema(ctx: click.Context, schema_name: str, format_: str):
    spec = load_spec()
    schema = spec["components"]["schemas"][schema_name]
    if format_ == "yaml":
        click.echo(yaml.dump(schema))
    else:
        click.echo(json.dumps(schema, indent=2))
