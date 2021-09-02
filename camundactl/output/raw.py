import sys
from typing import Any

import click

from camundactl.output.base import OutputHandler


class RawOutputHandler(OutputHandler):

    name: str = "raw"
    options = {
        "output_file": click.option(
            "-oF",
            "--output-file",
            "output_file",
            type=click.File(mode="wb"),
            required=False,
            help="output file",
        ),
    }

    def handle(self, result, output_file) -> Any:
        (output_file or sys.stdout.buffer).write(result)
