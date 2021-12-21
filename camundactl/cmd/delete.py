from camundactl.cmd.get import OpenAPIMulitCommandBase
from camundactl.cmd.openapi.factory import OpenAPICommandFactory


class DeleteMultiCommand(OpenAPIMulitCommandBase):
    verb = "delete"

    def get_factory_method(self, factory: OpenAPICommandFactory):
        return factory.create_delete_command

