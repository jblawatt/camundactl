from camundactl.cmd.config import load_config
from camundactl.cmd.openapi.base import load_spec
from camundactl.cmd.openapi.factory import OpenAPICommandFactory


def register_commands():
    spec = load_spec()
    command_factory = OpenAPICommandFactory(spec)
    command_factory.create_get_commands()
    command_factory.create_delete_commands()
    command_factory.create_apply_commands()
