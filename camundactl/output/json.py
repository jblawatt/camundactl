import json

import click

from camundactl.output.base import OutputHandler


class JSONOutputHandler(OutputHandler):

    name: str = "json"

    def handle(self, result, **kwargs):
        click.echo(json.dumps(result, indent=2))
