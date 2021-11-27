import warnings
from functools import cache, wraps
from inspect import getfullargspec
from typing import Callable, Dict, Optional

import click

from camundactl.client import Client, create_client
from camundactl.client.client import CamundaOpenAPIClient
from camundactl.config import ConfigDict, load_config
from camundactl.openapi.cache import OpenAPISpecCache
from camundactl.openapi.loader import load_spec


class ContextObject:

    _selected_engine = None
    _spec: Optional[Dict] = None
    _config: Optional[Dict] = None
    _spec_cache = None

    def __getitem__(self, key):

        warnings.warn(
            "__getitem__ is deprecated, use get... instead", DeprecationWarning
        )

        if key == "client":
            return self.get_client()
        if key == "config":
            return self.get_config()
        if key == "spec":
            return self.get_spec()
        if key == "spec_cache":
            return self.get_spec_cache()
        if key == "camunda_client":
            return self.get_camunda_client()

        raise KeyError(key)

    def set_selected_engine(self, engine: str):
        # TODO: validate Engine
        self._selected_engine = engine

    @cache
    def get_client(self) -> Client:
        return create_client(
            self.get_config(),
            selected_engine=self._selected_engine,
        )

    @cache
    def get_config(self) -> ConfigDict:
        if self._config is None:
            self._config = load_config()
        return self._config

    @cache
    def get_spec(self) -> Dict:
        if self._spec is None:
            self._spec = load_spec()
        return self._spec

    @cache
    def get_spec_cache(self) -> OpenAPISpecCache:
        if self._spec_cache is None:
            spec = self.get_spec()
            self._spec_cache = OpenAPISpecCache(spec)
        return self._spec_cache

    @cache
    def get_camunda_client(self):
        return CamundaOpenAPIClient(
            spec=self.get_spec(),
            client=self.get_client(),
        )

    def resolve_alias(self, name: str) -> Optional[str]:
        """
        tries to resolve the given alias if not
        found returns none
        """
        config = self.get_config()
        try:
            return config["alias"][name]
        except KeyError:
            return None


def _is_bound_method(func: Callable) -> bool:
    """
    tests weather this method is bound and so the
    frist argument is cls or self

    https://stackoverflow.com/questions/2435764/how-to-differentiate-between-method-and-function-in-a-decorator
    """
    args = getfullargspec(func).args
    return bool(args and args[0] in ("self", "cls"))


def ensure_object():
    """
    a command decorator which ensures the context object to be created
    """

    def inner(func):
        if _is_bound_method(func):

            @wraps(func)
            def wrapper_bound(self_or_cls, ctx: click.Context, *args, **kwargs):
                ctx.ensure_object(ContextObject)
                return func(self_or_cls, ctx, *args, **kwargs)

            return wrapper_bound

        @wraps(func)
        def wrapper(ctx: click.Context, *args, **kwargs):
            ctx.ensure_object(ContextObject)
            return func(ctx, *args, **kwargs)

        return wrapper

    return inner
