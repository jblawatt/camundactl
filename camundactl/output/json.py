import json

import click

from camundactl.output.base import OutputHandler


class JSONOutputHandler(OutputHandler):

    name: str = "json"

    def __init__(self, *args, indent: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.indent = indent

    def handle(self, result, **kwargs):
        click.echo(json.dumps(result, indent=self.indent))
