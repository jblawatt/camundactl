import functools
from typing import Any, Callable


class OutputHandler:

    name: str = ""
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
