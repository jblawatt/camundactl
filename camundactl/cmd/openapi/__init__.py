import json
from importlib.resources import open_text

from camundactl.cmd.openapi.factory import OpenAPICommandFactory

__all__ = ["command_factory"]


def load(openapi_filename: str = "openapi.json"):
    command_factory = OpenAPICommandFactory(
        json.load(open_text(__package__, openapi_filename))
    )

    command_factory.create_get_commands()
    command_factory.create_delete_commands()
    command_factory.create_apply_commands()
