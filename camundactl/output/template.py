from typing import Any, List, Optional

import click
from jinja2 import Environment, Template, TemplateNotFound
from jinja2.loaders import (
    BaseLoader,
    ChoiceLoader,
    DictLoader,
    FileSystemLoader,
    PackageLoader,
)

from camundactl.config import get_configdir, load_config
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
        extra_loaders: Optional[list[BaseLoader]] = None,
    ):
        self.default_template = default_template
        self.extra_loaders = extra_loaders or []
        loader = ChoiceLoader(self._create_loaders() + self.extra_loaders)
        self.env = Environment(loader=loader)

    def _create_loaders(self) -> List[BaseLoader]:
        choices = []
        choices.append(DictLoader(DEFAULT_TEMPLATES_DICT))
        config = load_config()
        for path in config.get("extra_template_paths", []):
            choices.append(FileSystemLoader(path))
        choices.append(FileSystemLoader(get_configdir() / "templates"))
        return choices

    def handle(self, result: Any, output_template: Optional[str]) -> Any:
        if result is None and output_template is None:
            return
        output_template = output_template or self.default_template
        try:
            template = self.env.get_template(output_template)
        except TemplateNotFound:
            template = Template(output_template)
        if isinstance(result, dict):
            context = {**result, "result": result}
        else:
            context = {"result": result}
        click.echo(template.render(**context))
