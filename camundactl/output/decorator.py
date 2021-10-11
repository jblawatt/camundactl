import functools
from contextlib import contextmanager
from typing import Optional

import click

from camundactl.output.base import OutputHandler


@contextmanager
def set_current_output(output_handlers: list[OutputHandler], output: str):
    for w in output_handlers:
        w.set_current_output(output)
    yield
    for w in output_handlers:
        w.set_current_output(None)


def with_output(*wrappers: OutputHandler, default: Optional[str] = None):
    def inner(func):

        if not wrappers:
            raise Exception("there must be at least one output handler")

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
                raise click.ClickException(
                    "Invalid output '%s'. "
                    "Has to be one of: %s"
                    % (output, ", ".join(oh.name for oh in wrappers))
                )
            with set_current_output(wrappers, output):
                return func(*args, **kwargs)

        return wrapper

    return inner
