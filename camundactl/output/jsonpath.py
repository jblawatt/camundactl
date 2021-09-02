from typing import Any

import click
from jsonpath_ng import parse

from camundactl.output.base import OutputHandler


class JSONPathOutputHandler(OutputHandler):

    name: str = "jsonpath"

    options = {
        "output_jsonpath": click.option(
            "-oJ",
            "--output-jsonpath",
            "output_jsonpath",
            default="$",
            required=False,
            help="jsonpath template",
        )
    }

    def handle(self, result, output_jsonpath) -> Any:
        expr = parse(output_jsonpath)
        matches = expr.find(result)
        for match in matches:
            click.echo(match.value)
