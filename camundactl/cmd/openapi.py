from camundactl.client import Client
from typing import Dict
import click
import json
from camundactl.cmd.helpers import (
    with_output_factory,
    with_query_param_factory,
    with_args_factory,
)
from camundactl.cmd.base import get, delete


class CommandFactory(object):
    def __init__(self, openapi):
        self.openapi = openapi

    def _get_operation_definition(self, operation_id, method):
        for path, path_definition in self.openapi["paths"].items():
            definition = path_definition.get(method)
            if definition is None:
                continue
            if definition["operationId"] == operation_id:
                # got it
                break
        else:
            raise Exception("invalid operation id " + operation_id)
        return path, definition

    def _create_name(self, definition) -> str:
        operation = definition["operationId"]
        if operation.startswith("get"):
            operation = operation[3:]
            operation = operation[0].lower() + operation[1:]
        if operation.startswith("delete"):
            operation = operation[6:]
            operation = operation[0].lower() + operation[1:]
        return operation

    def _get_options(self, definition):
        return [
            (param.get("name"), param.get("description"))
            for param in definition.get("parameters", ())
            if param.get("in") == "query"
        ]

    def _get_args(self, definition):
        return [
            (param.get("name"), param.get("description"))
            for param in definition.get("parameters", ())
            if param.get("in") == "path"
        ]

    def create_get(self, operation_id, parent):
        path, definition = self._get_operation_definition(operation_id, "get")

        operation = self._create_name(definition)
        description = definition["description"]

        params = self._get_options(definition)
        args = self._get_args(definition)

        @with_output_factory()
        @with_query_param_factory(params=params, name="params")
        @with_args_factory(args=args, name="args")
        @click.pass_context
        def command(ctx: click.Context, params: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.get(path.format(**args), params=params)
            resp.raise_for_status()
            return resp.json()

        parent.command(operation, help=description)(command)

    def create_delete(self, operation_id, parent):
        path, definition = self._get_operation_definition(operation_id, "delete")

        operation = self._create_name(definition)
        description = definition["description"]

        params = self._get_options(definition)
        args = self._get_args(definition)

        @with_output_factory()
        @with_query_param_factory(params=params, name="params")
        @with_args_factory(args=args, name="args")
        @click.pass_context
        def command(ctx: click.Context, params: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.delete(path.format(**args), params=params)
            resp.raise_for_status()
            return None

        parent.command(operation, help=description)(command)


factory = CommandFactory(json.load(open("openapi.json", "r")))

factory.create_get("getDeploymentsCount", get)
factory.create_get("getDeployment", get)
factory.create_get("getDeploymentResources", get)
factory.create_get("getDeploymentResource", get)
factory.create_get("getDeploymentResourceData", get)
factory.create_get("getProcessEngineNames", get)
factory.create_get("getEventSubscriptions", get)
factory.create_get("getEventSubscriptionsCount", get)
factory.create_get("getExternalTasks", get)
factory.create_get("getExternalTasksCount", get)
factory.create_get("getTopicNames", get)
factory.create_get("getExternalTask", get)
factory.create_get("getExternalTaskErrorDetails", get)
factory.create_get("interval", get)
factory.create_get("getMetrics", get)
factory.create_get("getProcessDefinitions", get)
factory.create_get("getProcessDefinitionsCount", get)
factory.create_get("getProcessDefinitionByKey", get)
factory.create_get("getDeployedStartFormByKey", get)
factory.create_get("getProcessDefinitionDiagramByKey", get)
factory.create_get("getStartFormVariablesByKey", get)
factory.create_get("getRenderedStartFormByKey", get)
factory.create_get("getStartFormByKey", get)
factory.create_get("getActivityStatisticsByProcessDefinitionKey", get)
factory.create_get("getLatestProcessDefinitionByTenantId", get)
factory.create_get("getDeployedStartFormByKeyAndTenantId", get)
factory.create_get("getProcessDefinitionDiagramByKeyAndTenantId", get)
factory.create_get("getStartFormVariablesByKeyAndTenantId", get)
factory.create_get("getRenderedStartFormByKeyAndTenantId", get)
factory.create_get("getStartFormByKeyAndTenantId", get)
factory.create_get("getActivityStatisticsByProcessDefinitionKeyAndTenantId", get)
factory.create_get("getProcessDefinitionBpmn20XmlByKeyAndTenantId", get)
factory.create_get("getProcessDefinitionBpmn20XmlByKey", get)
factory.create_get("getProcessDefinitionStatistics", get)
factory.create_get("getProcessDefinition", get)
factory.create_get("getDeployedStartForm", get)
factory.create_get("getProcessDefinitionDiagram", get)
factory.create_get("getStartFormVariables", get)
factory.create_get("getRenderedStartForm", get)
factory.create_get("getStartForm", get)
factory.create_get("getActivityStatistics", get)
factory.create_get("getProcessDefinitionBpmn20Xml", get)
factory.create_get("getProcessInstances", get)
factory.create_get("getProcessInstancesCount", get)
factory.create_get("getActivityInstanceTree", get)
factory.create_get("getProcessInstanceVariables", get)
factory.create_get("getProcessInstanceVariable", get)
factory.create_get("getProcessInstanceVariableBinary", get)
factory.create_get("getSchemaLog", get)
factory.create_get("getTasks", get)
factory.create_get("getTasksCount", get)
factory.create_get("getTask", get)
factory.create_get("getAttachments", get)
factory.create_get("getAttachment", get)
factory.create_get("getAttachmentData", get)
factory.create_get("getComments", get)
factory.create_get("getComment", get)
factory.create_get("getDeployedForm", get)
factory.create_get("getForm", get)
factory.create_get("getFormVariables", get)
factory.create_get("getIdentityLinks", get)
factory.create_get("getTaskLocalVariables", get)
factory.create_get("getTaskLocalVariable", get)
factory.create_get("getTaskLocalVariableBinary", get)
factory.create_get("getRenderedForm", get)
factory.create_get("getTaskVariables", get)
factory.create_get("getTaskVariable", get)
factory.create_get("getTaskVariableBinary", get)
factory.create_get("getRestAPIVersion", get)

factory.create_delete("deleteDeployment", delete)
factory.create_delete("deleteProcessDefinitionsByKey", delete)
factory.create_delete("deleteProcessDefinitionsByKeyAndTenantId", delete)
factory.create_delete("deleteProcessDefinition", delete)
factory.create_delete("deleteProcessInstance", delete)
factory.create_delete("deleteProcessInstanceVariable", delete)
factory.create_delete("deleteTask", delete)
factory.create_delete("deleteAttachment", delete)
factory.create_delete("deleteTaskLocalVariable", delete)
factory.create_delete("deleteTaskVariable", delete)
