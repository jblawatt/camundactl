from typing import Any, Dict, Optional

import click
from jinja2 import Environment, Template, TemplateNotFound
from jinja2.loaders import DictLoader

from camundactl.output.base import OutputHandler

DEFAULT_TEMPLATES_DICT = {
    "default": "{{result}}",
    "result-length": "{{result|length}}",
}


class TemplateOutputHandler(OutputHandler):

    name: str = "template"

    options = {
        "output_template": click.option(
            "-oT",
            "--output-template",
            "output_template",
            default=None,
            required=False,
            help=(
                f"provide a template name (one of "
                f"{', '.join(DEFAULT_TEMPLATES_DICT.keys())})"
                f" or provide a jinja2 template string that will be used."
            ),
        ),
    }

    def __init__(
        self,
        default_template="default",
        extra_template_mapping: Optional[Dict[str, str]] = None,
    ):
        self.default_template = default_template
        loader = DictLoader(
            dict(**DEFAULT_TEMPLATES_DICT, **(extra_template_mapping or {}))
        )
        self.env = Environment(loader=loader)

    def handle(self, result: Any, output_template: str) -> Any:
        try:
            template = self.env.get_template(output_template)
        except TemplateNotFound:
            template = Template(output_template or self.default_template)
        if isinstance(result, dict):
            context = {**result, "result": result}
        else:
            context = {"result": result}
        click.echo(template.render(**context))
