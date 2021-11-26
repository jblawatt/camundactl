import click

import functools
from typing import List, Optional

from camundactl.cmd.get import OpenAPIMulitCommandBase
from camundactl.cmd.openapi.factory import OpenAPICommandFactory



class ApplyMultiCommand(OpenAPIMulitCommandBase):

    verbs = ["post", "put"]

    def get_factory_method(self, factory: OpenAPICommandFactory):
        return functools.partial(factory.create_apply_command, method=self.verb)

    def list_commands(self, ctx: click.Context) -> List[str]:
        result = []
        for verb in self.verbs:
            self.verb = verb
            result += super().list_commands(ctx)
        self.verb = None
        return  result

    def get_command(self, ctx: click.Context, name: str) -> Optional[click.Command]:
        for verb in self.verbs:
            self. verb = verb
            if cmd := super().get_command(ctx, name):
                return cmd
        return None


