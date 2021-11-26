import functools
import click

from typing import Any, Callable, Optional


class OutputHandler:

    name: str = ""
    options = {}
    ctx: Optional[click.Context] = None

    def set_current_output(self, output):
        self.current_output = output

    def _extract_context(
        self, func: Callable, args: tuple, kwargs: dict
    ) -> Optional[click.Context]:
        for arg in list(args) + list(kwargs.values()):
            if isinstance(arg, click.Context):
                return arg
        return None

    def apply(self, func: Callable) -> Callable:
        """
        applies the output options to the call
        funcs and returns a call wrapper which
        handles the output if it is activated.
        """

        for option in self.options.values():
            func = option(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handle_kwargs = {}
            for name in self.options.keys():
                handle_kwargs[name] = kwargs.pop(name)
            self.ctx = self._extract_context(func, args, kwargs)
            result = func(*args, **kwargs)
            if self.current_output == self.name:
                self.handle(result, **handle_kwargs)
            return result

        return wrapper

    def handle(self, result, **kwargs) -> Any:
        raise NotImplementedError()
