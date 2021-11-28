from typing import Any, Dict, List, Optional, Iterable

import click
import logging
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


__all__ = ["TemplateOutputHandler"]


DEFAULT_TEMPLATES_DICT = {
    "default": "{{result}}",
    "result-length": "{{result|length}}",
}

logger = logging.getLogger(__name__)


class TemplateOutputHandler(OutputHandler):
    """
    Output handler for template output. Loads the template based
    on different rules and provied the api result and some
    other information as template context.
    """

    name: str = "template"

    # default patterns to load the template if there is
    # no specific teplate provided
    default_template_patterns = [
        "{operation_id}.tpl",
        "{parent}_{command}.tpl",
        "{command}.tpl",
        "{verb}_default.tpl",
        "{parent}_default.tpl",
        "default.tpl",
    ]

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
        tpl_lookup_context: Dict[str, str] = None,
    ):
        self.default_template = default_template
        self.tpl_lookup_context = tpl_lookup_context or {}

    def _create_loaders(self) -> Iterable[BaseLoader]:
        """
        creates a list of templates loaders.
        """
        yield DictLoader(DEFAULT_TEMPLATES_DICT)
        if self.ctx:
            config = self.ctx.obj.get_config()
            extra_paths = config.get("template", {}).get("extra_paths", [])
            for path in extra_paths:
                yield FileSystemLoader(path)
        yield FileSystemLoader(get_configdir() / "templates")
        yield PackageLoader("camundactl.output", "templates")

    def _create_environment(self) -> Environment:
        loaders = list(self._create_loaders())
        loader = ChoiceLoader(loaders)
        return Environment(loader=loader)

    def _get_empty_template(self, env: Environment) -> Template:
        try:
            return env.get_template("emtpy.tpl")
        except TemplateNotFound:
            return Template("")

    def _create_tpl_lookup_context(self) -> dict[str, Any]:
        command_name = "NO_COMMAND_FOUND"
        parent_name = "NO_PARENT_FOUND"
        if self.ctx:
            command_name = self.ctx.command.name
            if self.ctx.parent:
                parent_name = self.ctx.parent.command.name
        return {
            "command": command_name,
            "parent": parent_name,
            **self.tpl_lookup_context,
        }

    def _get_user_template_patterns(self) -> List[str]:
        if not self.ctx:
            return []
        config = self.ctx.obj.get_config()
        try:
            return config["template"]["extra_patterns"]
        except KeyError:
            return []

    def _get_template_patterns(self) -> List[str]:
        user_template_patterns = self._get_user_template_patterns()
        template_patterns = user_template_patterns + self.default_template_patterns

        if self.default_template:
            template_patterns.insert(0, self.default_template)
        return template_patterns

    def _get_template(
        self, env: Environment, name_or_tpl: Optional[str] = None
    ) -> Template:
        if name_or_tpl is not None:
            try:
                return env.get_template(name_or_tpl)
            except TemplateNotFound:
                return Template(name_or_tpl)

        template_patterns = self._get_template_patterns()
        lookup_context = self._create_tpl_lookup_context()
        lookup = []
        for pattern in template_patterns:
            try:
                lookup.append(pattern.format(**lookup_context))
            except KeyError as error:
                logger.warn(
                    "Cannot apply to template pattern %s. Error: %s.", pattern, error
                )
                continue

        try:
            return env.select_template(lookup)
        except TemplateNotFound:
            return Template("NO TEMPLATE FOUND")

    def handle(self, result: Any, output_template: Optional[str]) -> Any:
        env = self._create_environment()
        if result is None and output_template is None:
            template = self._get_empty_template(env)
        else:
            template = self._get_template(env, output_template)

        if isinstance(result, dict):
            context = {**result, "result": result}
        else:
            context = {"result": result}
        click.echo(template.render(**context))
