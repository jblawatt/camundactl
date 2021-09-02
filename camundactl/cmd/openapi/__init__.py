import json
from camundactl.cmd.openapi.factory import OpenAPICommandFactory
from importlib.resources import open_text


factory = OpenAPICommandFactory(json.load(open_text(__package__, "openapi.json")))

factory.create_get_commands()
factory.create_delete_commands()
factory.create_apply_commands()
