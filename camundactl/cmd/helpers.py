import functools
import re
from typing import Callable, List, NamedTuple, Optional

import click


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
