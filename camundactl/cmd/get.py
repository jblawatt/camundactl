from logging import getLogger
from functools import reduce
from typing import Callable, List, Optional, cast

import click
from toolz.functoolz import curry

from camundactl.cmd.context import ContextObject, ensure_object
from camundactl.cmd.openapi.factory import OpenAPICommandFactory
from camundactl.openapi.cache import OpenAPISpecCache

logger = getLogger(__name__)

@curry
def to_command_name(operation_id: str, prefix: str) -> str:
    if not operation_id.startswith(prefix):
        return operation_id
    command_name = operation_id[len(prefix) :]
    return command_name[0].lower() + command_name[1:]


@curry
def from_command_name(command_name: str, prefix: str) -> str:
    return prefix + command_name[0].upper() + command_name[1:]


class OpenAPIMulitCommandBase(click.MultiCommand):

    verb: str
    _command_factory: OpenAPICommandFactory

    def _get_or_create_factory(self, spec, spec_cache=None):
        if not hasattr(self, "_command_factory"):
            self._command_factory = OpenAPICommandFactory(spec, spec_cache)
        return self._command_factory

    def get_factory_method(self, factory: OpenAPICommandFactory) -> Callable:
        raise NotImplementedError()

    @ensure_object()
    def list_commands(self, ctx: click.Context) -> List[str]:
        """
        returns a list of commands based on the operation ids the verb
        for this class.

        Args:
            ctx: the click context.
        """
        cache: OpenAPISpecCache = ctx.obj.get_spec_cache()
        op_ids = cache.get_operation_ids_by_verb(self.verb)
        command_names = list(map(to_command_name(prefix=self.verb), op_ids))
        return sorted(command_names)

    @ensure_object()
    def get_command(self, ctx: click.Context, name: str) -> Optional[click.Command]:
        """
        returns the command object by the given name. if the operation
        based on the given name could not be found, this method returns none.

        Args:
            ctx: the click context.
            name: the commands name.
        """
        spec = ctx.obj.get_spec()
        cache: OpenAPISpecCache = ctx.obj.get_spec_cache()
        if alias := ctx.obj.resolve_alias(name):
            name = alias
        operation_id: str = cast(str, from_command_name(name, prefix=self.verb))
        if not cache.has_operation_id(operation_id):
            if not cache.has_operation_id(name):
                return None
            operation_id = name
        factory = self._get_or_create_factory(spec, cache)
        method = self.get_factory_method(factory)
        return method(operation_id=operation_id)


class GetMulitCommand(OpenAPIMulitCommandBase):
    verb = "get"

    def get_factory_method(self, factory: OpenAPICommandFactory):
        return factory.create_get_command
