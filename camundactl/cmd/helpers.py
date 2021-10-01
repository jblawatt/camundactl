import functools
import re
from http import HTTPStatus
from typing import Callable, List, NamedTuple, Optional

import click
from click.exceptions import ClickException
from requests.models import HTTPError


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

            click_kwargs = {}

            if not option.multiple:
                if option.type_ == bool:
                    long = f"--{value}/--not-{value}"
                    # FIXME: cannt always be false
                    click_kwargs.update(
                        {
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

        func = click.option(
            "--query-extra",
            "query_extra",
            help="extra query parameters, not listed in openapi (format: PARAM=VALUE)",
            multiple=True,
        )(func)

        @functools.wraps(func)
        def wrapper(*args, query_extra, **kwargs):

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

            for extra in query_extra:
                extra_name, extra_value = extra.strip().split("=")
                query_params[extra_name] = extra_value

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
                try:
                    return func(*args, **kwargs)
                except HTTPError as http_error:
                    if http_error.response.status_code != HTTPStatus.NOT_FOUND:
                        raise
                    try:
                        context, *_ = args
                    except ValueError:
                        # no context passed and args are empty
                        # FIXME: should not happen. where is the context gone?
                        raise ClickException(
                            f"error loading requested object: {http_error}"
                        )
                    else:
                        raise ClickException(
                            f"the object '{context.info_name}' you requested does not exists"
                        )
            except Exception as error:
                if show_traceback:
                    raise
                else:
                    raise click.ClickException(str(error))

        return wrapper

    return inner
