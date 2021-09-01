import sys
import functools
import json
import re
from typing import Any, Callable, List, NamedTuple, Optional
from contextlib import contextmanager

import click
from jinja2 import Template
from jsonpath_ng import parse
from tabulate import tabulate


# headeres blacklist to make sure only usefull headers are used
HEADERS_BLACKLIST = ("links",)


def ensure_length(value: Any, max_length: int = 1000):
    """makes sure the value is no longer then the given lengths"""
    if isinstance(value, str):
        if len(value) > max_length:
            return value[0:max_length] + "..."
    return value


ALLOWED_OUTPUT = ["table", "json", "jsonpath", "template", "text"]


class OutputHandler:

    name: str = "table"
    options = {}

    def set_current_output(self, output):
        self.current_output = output

    def apply(self, func: Callable) -> Callable:

        for option in self.options.values():
            func = option(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handle_kwargs = {}
            for name in self.options.keys():
                handle_kwargs[name] = kwargs.pop(name)
            result = func(*args, **kwargs)
            if self.current_output == self.name:
                self.handle(result, **handle_kwargs)
            return result

        return wrapper

    def handle(self, result, **kwargs) -> Any:
        raise NotImplementedError()


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
            first, *_ = result
            headers = [
                key for key in first.keys() if key not in self.table_headers_backlist
            ]
            result = [
                [ensure_length(item.get(key), cell_max_length) for key in headers]
                for item in result
            ]
        elif isinstance(headers, (tuple, list)):
            result = [
                [ensure_length(row[key], cell_max_length) for key in headers]
                for row in result
            ]
        elif isinstance(headers, dict):
            result = [
                [ensure_length(row[key], cell_max_length) for key in headers.values()]
                for row in result
            ]
            headers = headers.keys()
        click.echo(tabulate(result, headers=headers))


class JSONOutputHandler(OutputHandler):

    name: str = "json"

    def handle(self, result, **kwargs):
        click.echo(json.dumps(result, indent=2))


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


default_table_output = TableOutputHandler(table_headers_backlist=["links"])
default_object_table_output = ObjectTableOutputHandler()
default_json_output = JSONOutputHandler()
default_jsonpath_output = JSONPathOutputHandler()
default_template_output = TemplateOutputHandler()
default_raw_output = RawOutputHandler()


class VariablesTableOutputHandler(TableOutputHandler):
    pass


@contextmanager
def set_current_output(wrappers, output):
    for w in wrappers:
        w.set_current_output(output)
    yield
    for w in wrappers:
        w.set_current_output(None)


def with_output(*wrappers: OutputHandler, default: Optional[str] = None):
    def inner(func):

        output_lookup = dict((oh.name, oh) for oh in wrappers)

        func = click.option(
            "-o",
            "--output",
            "output",
            default=default or wrappers[0].name,
            type=click.Choice([oh.name for oh in wrappers]),
        )(func)

        for oh in wrappers:
            func = oh.apply(func)

        @functools.wraps(func)
        def wrapper(*args, output, **kwargs):
            if output not in output_lookup:
                raise click.ClickException("invalid output '%s'" % output)
            with set_current_output(wrappers, output):
                return func(*args, **kwargs)

        return wrapper

    return inner


class OptionTuple(NamedTuple):
    name: str
    help: str
    multiple: bool
    type_: type
    autocomplete: Optional[Callable]


class ArgumentTuple(NamedTuple):
    name: str
    help: str
    autocomplete: Optional[Callable]


def with_query_option_factory(options: List[OptionTuple], name: str):
    def inner(func):
        options_generated = {}

        for option in options:
            capital_param = option.name[0].title() + option.name[1:]
            parts = re.findall("[A-Z][^A-Z]*", capital_param)
            value = "-".join(list(map(str.lower, parts)))

            long = f"--{value}"

            # fixme: no short options currently becouse of naming conflicts
            # first, *rest = parts
            # short = "-" + first[0].lower() + "".join(map(lambda s: s[0], rest))

            click_kwargs = {}

            if not option.multiple:
                if option.type_ == bool:
                    click_kwargs.update(
                        {
                            "is_flag": True,
                            "default": False,
                        }
                    )
                else:
                    click_kwargs["default"] = None

            click_option = click.option(
                long,
                option.name,
                help=option.help,
                multiple=option.multiple,
                shell_complete=option.autocomplete,
                **click_kwargs,
            )
            func = click_option(func)
            options_generated[option.name] = click_option

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            query_params = {}

            for option in options:
                value = kwargs.pop(option.name, None)

                # multiple and empty tuple -> continue
                # not multiple and value is none -> continue
                if (option.multiple and not value) or (
                    not option.multiple and value is None
                ):
                    continue
                if isinstance(value, bool):
                    value = "true" if value else "false"

                query_params[option.name] = value

            return func(*args, **{name: query_params}, **kwargs)

        return wrapper

    return inner


def with_args_factory(args: List[ArgumentTuple], name: str):
    def inner(func):

        for arg in args:
            func = click.argument(
                arg.name,
                nargs=1,
                shell_complete=arg.autocomplete,
            )(func)

        @functools.wraps(func)
        def wrapper(*a, **kwargs):
            values = {}
            for arg in args:
                # clicks makes options lowercase. so correct this here
                value = kwargs.pop(arg.name.lower(), None)
                if value is not None:
                    values[arg.name] = value

            return func(*a, **{name: values}, **kwargs)

        return wrapper

    return inner


def with_exception_handler():
    def inner(func):

        func = click.option(
            "--traceback",
            "show_traceback",
            is_flag=True,
            default=False,
            required=False,
            help="do not hide traceback on error",
        )(func)

        @functools.wraps(func)
        def wrapper(*args, show_traceback, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                if show_traceback:
                    raise
                else:
                    click.secho(str(error), fg="red")
                return 1

        return wrapper

    return inner
