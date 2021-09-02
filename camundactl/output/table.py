from typing import Any, List, Optional

import click
from tabulate import tabulate

from camundactl.output.base import OutputHandler


def _ensure_length(value: Any, max_length: int = 1000):
    """makes sure the value is no longer then the given lengths"""
    if isinstance(value, str):
        if len(value) > max_length:
            return value[0:max_length] + "..."
    return value


class TableOutputHandler(OutputHandler):

    name: str = "table"

    options = {
        "output_headers": click.option(
            "-oH",
            "--output-header",
            "output_headers",
            default=None,
            help="comma seperated list of headers",
        ),
        "output_cell_max_length": click.option(
            "-oCL",
            "--output-cell-limit",
            "output_cell_max_length",
            type=int,
            required=False,
            default=40,
            help="limit cell value for table output (default=40)",
        ),
    }

    def __init__(
        self,
        table_headers=None,
        table_headers_backlist=None,
        cell_max_length=40,
    ):
        self.default_cell_max_length = cell_max_length
        self.default_table_headers = table_headers
        self.table_headers_backlist = table_headers_backlist or ()

    def handle(
        self,
        result: List[Any],
        output_headers: Optional[str],
        output_cell_max_length,
    ):
        if output_headers:
            headers = output_headers.split(",")
        else:
            headers = self.default_table_headers

        cell_max_length = output_cell_max_length or self.default_cell_max_length

        if not headers:
            # use the keys as headers, but remove all backlist headers
            if not result:
                click.echo("empty result")
                return
            first, *_ = result
            if isinstance(first, dict):
                headers = [
                    key
                    for key in first.keys()
                    if key not in self.table_headers_backlist
                ]
                result = [
                    [_ensure_length(item.get(key), cell_max_length) for key in headers]
                    for item in result
                ]
            else:
                headers = ("unknown",)
                result = [(item,) for item in result]
        elif isinstance(headers, (tuple, list)):
            result = [
                [_ensure_length(row[key], cell_max_length) for key in headers]
                for row in result
            ]
        elif isinstance(headers, dict):
            result = [
                [_ensure_length(row[key], cell_max_length) for key in headers.values()]
                for row in result
            ]
            headers = headers.keys()
        click.echo(tabulate(result, headers=headers))


class ObjectTableOutputHandler(TableOutputHandler):
    def handle(
        self, result: List[Any], output_headers: Optional[str], output_cell_max_length
    ):

        headers = "key,value"

        output_headers = output_headers or self.default_table_headers

        new_result = []
        for key, value in result.items():
            if self.table_headers_backlist and key in self.table_headers_backlist:
                continue
            if output_headers and key not in output_headers:
                continue
            new_result.append({"key": key, "value": str(value)})

        return super().handle(new_result, headers, output_cell_max_length)
