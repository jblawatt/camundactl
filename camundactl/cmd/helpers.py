import re
import json
from jsonpath_ng import jsonpath, parse
from typing import List, Optional, Any, Tuple
from jinja2 import Template
from tabulate import tabulate
import click
import functools


output_option = click.option(
    "-o", "--output", "output", default="table", help="defines the output format"
)


def table_output(result: Any, headers=None):
    if headers is None:
        headers = "keys"
    elif isinstance(headers, (tuple, list)):
        result = [[row[key] for key in headers] for row in result]
    elif isinstance(headers, dict):
        result = [[row[key] for key in headers.values()] for row in result]
        headers = headers.keys()
    return tabulate(result, headers=headers)


ALLOWED_OUTPUT = ["table", "json", "jsonpath", "template", "text"]


def with_output_factory(
    allow: Optional[List[str]] = ALLOWED_OUTPUT,
    default: str = "table",
    default_table_headers: Optional[List[str]] = None,
    default_template: str = "",
):
    def wrapper(func):

        output_option = click.option(
            "-o",
            "--output",
            "output",
            type=click.Choice(allow or ALLOWED_OUTPUT),
            default=default,
            help="defines the output format",
        )
        func = output_option(func)

        if "template" in allow:
            template_option = click.option(
                "-oT",
                "--output-template",
                "output_template",
                default=default_template,
                help="defines the output tempalte to be used",
            )
            func = template_option(func)

        if "jsonpath" in allow:
            jsonpath_option = click.option(
                "-oJ",
                "--output-jsonpath",
                "output_jsonpath",
                default="$",
                help="defines the jsonpath to be used for the output",
            )
            func = jsonpath_option(func)

        @functools.wraps(func)
        def inner(*args, output, output_template, output_jsonpath, **kwargs):
            result = func(*args, **kwargs)

            if result is None:
                return

            if output == "table":
                return click.echo(table_output(result, default_table_headers))
            if output == "json":
                return click.echo(json.dumps(result, indent=2))
            if output == "template":
                return click.echo(Template(output_template).render(result))
            if output == "jsonpath":
                expr = parse(output_jsonpath)
                matches = expr.find(result)
                for match in matches:
                    click.echo(match.value)
                return

            raise Exception("invalid output")

        return inner

    return wrapper


def with_query_param_factory(params: List[Tuple[str, str]], name: str):
    def inner(func):
        options = {}

        for param, help in params:
            capital_param = param[0].title() + param[1:]
            parts = re.findall("[A-Z][^A-Z]*", capital_param)
            long = "--%s" % "-".join(list(map(str.lower, parts)))
            first, *rest = parts
            short = "-" + first[0].lower() + "".join(map(lambda s: s[0], rest))

            option = click.option(long, param, help=help, multiple=True)
            func = option(func)
            options[param] = option

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            query_params = {}

            for param, __ in params:
                value = kwargs.pop(param, None)
                if value is None:
                    continue
                query_params[param] = value

            return func(*args, **{name: query_params}, **kwargs)

        return wrapper

    return inner


def with_args_factory(args, name: str):
    def inner(func):

        for arg, __ in args:
            func = click.argument(arg, nargs=1)(func)

        @functools.wraps(func)
        def wrapper(*a, **kwargs):
            values = {}
            for arg, __ in args:
                value = kwargs.pop(arg, None)
                if value is not None:
                    values[arg] = value

            return func(*a, **{name: values}, **kwargs)

        return wrapper

    return inner
