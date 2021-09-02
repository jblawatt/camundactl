from typing import Any

import click
from jinja2 import Template

from camundactl.output.base import OutputHandler


class TemplateOutputHandler(OutputHandler):

    name: str = "template"

    options = {
        "output_template": click.option(
            "-oT",
            "--output-template",
            "output_template",
            default=None,
            required=False,
            help="jinja2 template",
        )
    }

    def __init__(self, default_template="{{result}}"):
        self.default_template = default_template

    def handle(self, result, output_template) -> Any:
        template = Template(output_template or self.default_template)
        click.echo(template.render(result=result))
