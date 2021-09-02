import json
from functools import lru_cache, partial
from typing import Callable, Dict, List, Optional, Tuple, TypedDict

import click
import jsonschema
import yaml
from toolz import first, second

from camundactl.client import Client
from camundactl.cmd.base import _ensure_client, apply, delete, get
from camundactl.cmd.helpers import (
    ArgumentTuple,
    OptionTuple,
    with_args_factory,
    with_exception_handler,
    with_query_option_factory,
)
from camundactl.output import (
    default_json_output,
    default_jsonpath_output,
    default_object_table_output,
    default_raw_output,
    default_table_output,
    default_template_output,
)
from camundactl.output.base import OutputHandler
from camundactl.output.decorator import with_output


def generic_autocomplete(
    ctx: click.Context, param: str, incomplete: str, endpoint: str
) -> List[str]:
    _ensure_client(ctx)
    client: Client = ctx.obj["client"]
    resp = client.get(endpoint)
    resp.raise_for_status()
    resp_json = resp.json()
    return [item["id"] for item in resp_json if item["id"].startswith(incomplete)]


process_instance_autocomplete = partial(
    generic_autocomplete,
    endpoint="/process-instance",
)

incidents_autocomplete = partial(
    generic_autocomplete,
    endpoint="/incident",
)
process_definition_autocomplete = partial(
    generic_autocomplete,
    endpoint="/process-definition",
)
task_id_autocomplete = partial(
    generic_autocomplete,
    endpoint="/task",
)


class OpenAPIDict(TypedDict):
    pass


class OpenAPIOperationDict(TypedDict):
    pass


class OpenAPICommandFactory(object):
    def __init__(self, openapi: OpenAPIDict):
        self.openapi = openapi

    @lru_cache
    def _get_operation_definition(
        self, operation_id: str, method: str
    ) -> OpenAPIOperationDict:
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

    def _create_command_name(self, definition) -> str:
        operation = definition["operationId"]
        for value in ("get", "delete", "resolve", "update", "set"):
            if operation.startswith(value) and operation != value:
                operation = operation[len(value) :]
                operation = operation[0].lower() + operation[1:]
                return operation
        return operation

    def _get_options(self, definition, options_autocomplete) -> List[OptionTuple]:

        options_autocomplete = options_autocomplete or {}
        types_lookup = {"string": str, "integer": int, "boolean": bool}

        return [
            OptionTuple(
                param.get("name"),
                param.get("description"),
                param.get("schema", {}).get("type", "") == "string",
                types_lookup.get(param["schema"]["type"], str),
                options_autocomplete.get(param.get("name"), None),
            )
            for param in definition.get("parameters", ())
            if param.get("in") == "query"
        ]

    def _get_args(
        self,
        definition,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
    ):
        args_autocomplete = args_autocomplete or {}

        return [
            ArgumentTuple(
                param.get("name"),
                param.get("description"),
                args_autocomplete.get(param.get("name"), None),
            )
            for param in definition.get("parameters", ())
            if param.get("in") == "path"
        ]

    def create_command(
        self,
        command: Callable,
        operation_id: str,
        method: str,
        parent: click.Group,
        output_handlers: Optional[Tuple[OutputHandler]],
        args_autocomplete: Optional[Dict[str, Callable]],
        options_autocomplete: Optional[Dict[str, Callable]],
    ):
        path, definition = self._get_operation_definition(operation_id, method)
        command_name = self._create_command_name(definition)
        command_desc = "\n".join((definition["description"], "", f"URL: {path}"))

        options = self._get_options(definition, options_autocomplete)
        args = self._get_args(definition, args_autocomplete)

        @with_output(*output_handlers)
        @with_query_option_factory(options=options, name="options")
        @with_args_factory(args=args, name="args")
        @with_exception_handler()
        @click.pass_context
        def inner(*args, **kwargs):
            return command(*args, **kwargs)

        parent.command(command_name, help=command_desc)(inner)

    def _has_list_response(
        self, definition: OpenAPIOperationDict, status_code: str = "200"
    ) -> bool:
        try:
            schema = definition["responses"]["200"]["content"]["application/json"][
                "schema"
            ]
        except KeyError:
            return True
        else:
            return schema.get("type") == "array"

    def create_get_command(
        self,
        operation_id: str,
        output_handlers: Optional[Tuple] = None,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):

        path, definition = self._get_operation_definition(operation_id, "get")

        def command(ctx: click.Context, options: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.get(path.format(**args), params=options)
            resp.raise_for_status()
            if "application/json" in resp.headers.get("Content-Type"):
                return resp.json()
            return resp.content

        has_list_response = self._has_list_response(definition)

        default_output_handlers = (
            default_table_output if has_list_response else default_object_table_output,
            default_json_output,
            default_jsonpath_output,
            default_template_output,
            default_raw_output,
        )

        self.create_command(
            command=command,
            operation_id=operation_id,
            parent=get,
            method="get",
            output_handlers=output_handlers or default_output_handlers,
            args_autocomplete=args_autocomplete
            or self._get_default_args_autocomplete(path),
            options_autocomplete=options_autocomplete
            or self._get_default_options_autocomplete(definition),
        )

    def create_delete_command(
        self,
        operation_id,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):
        path, definition = self._get_operation_definition(operation_id, "delete")

        def command(ctx: click.Context, params: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.delete(path.format(**args), params=params)
            resp.raise_for_status()

        self.create_command(
            command=command,
            operation_id=operation_id,
            method="delete",
            parent=delete,
            output_handlers=(default_template_output,),
            args_autocomplete=args_autocomplete
            or self._get_default_args_autocomplete(path),
            options_autocomplete=options_autocomplete
            or self._get_default_options_autocomplete(definition),
        )

    def _get_opration_request_schema(self, operation_id: str, method: str):
        _, definition = self._get_operation_definition(operation_id, method)

        # just in two parts to better read it
        try:
            content = definition["requestBody"]["content"]
            schema_ref = content["application/json"]["schema"]["$ref"]
        except KeyError:
            # no schema
            return {}
        else:
            __, __, schema_name = schema_ref.strip("#").strip("/").split("/")
            return self.openapi["components"]["schemas"][schema_name]

    def create_apply_command(
        self,
        operation_id: str,
        method: str,
        output_handlers: Optional[Tuple] = None,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):

        path, definition = self._get_operation_definition(operation_id, method)

        output_handlers = (default_template_output,)

        @click.option(
            "--skip-validation",
            "skip_validation",
            is_flag=True,
            default=False,
            required=False,
            help="ignore validation",
        )
        @click.option(
            "-j",
            "--json",
            "json_input",
            type=click.File(),
            required=False,
            default=None,
            help="input as json",
        )
        @click.option(
            "-y",
            "--yaml",
            "yaml_input",
            type=click.File(),
            required=False,
            default=None,
            help="input as json",
        )
        def command(
            ctx: click.Context,
            params: Dict,
            args: Dict,
            skip_validation: bool,
            json_input,
            yaml_input,
        ):
            client: Client = ctx.obj["client"]

            if json_input and yaml_input:
                raise click.ClickException("provide json OR yaml input")

            data = None
            if yaml_input:
                data = yaml.load(yaml_input, Loader=yaml.FullLoader)
            if json_input:
                data = json.load(json_input)

            if data and not skip_validation:
                schema = self._get_opration_request_schema(operation_id, method)
                jsonschema.validate(data, schema)

            extra = {}
            if data:
                extra["json"] = data

            extra["headers"] = {"Content-Type": "application/json"}

            resp = getattr(client, method)(path.format(**args), params=params, **extra)
            try:
                resp.raise_for_status()
            except Exception:
                click.secho(resp.text, fg="red")
                raise
            if "application/json" in resp.headers.get("Content-Type"):
                return resp.json()

        self.create_command(
            command=command,
            operation_id=operation_id,
            method=method,
            parent=apply,
            output_handlers=output_handlers,
            args_autocomplete=args_autocomplete
            or self._get_default_args_autocomplete(path),
            options_autocomplete=options_autocomplete
            or self._get_default_options_autocomplete(definition),
        )

    def _get_default_options_autocomplete(
        self, operation: OpenAPIOperationDict
    ) -> List[Callable]:
        result = {}
        lookup = {
            "processInstanceId": process_instance_autocomplete,
            "processDefinitionId": process_definition_autocomplete,
            "incidentId": incidents_autocomplete,
            "taskId": task_id_autocomplete,
        }
        for param in operation.get("parametes", []):
            name = param.get("name")
            if name in lookup:
                result[name] = lookup[name]
        return result

    def _get_default_args_autocomplete(self, path) -> Dict[str, Callable]:
        ID = "{id}"
        splitted = path.strip("/").split("/")
        result = {}
        if first(splitted) == "process-instance":
            if ID in splitted:
                result["id"] = process_instance_autocomplete
        if first(splitted) == "process-definition":
            if ID in splitted:
                result["id"] = process_definition_autocomplete
        if first(splitted) == "task":
            if ID in splitted:
                result["id"] = task_id_autocomplete
        if first(splitted) == "incident":
            if ID in splitted:
                result["id"] = incidents_autocomplete
        return result

    def create_get_commands(self):
        for _, path in self.openapi["paths"].items():
            get_operation = path.get("get")
            if not get_operation:
                continue

            self.create_get_command(
                operation_id=get_operation["operationId"],
            )

    def create_delete_commands(self):
        for _, path in self.openapi["paths"].items():
            delete_operation = path.get("delete")
            if not delete_operation:
                continue

            self.create_delete_command(
                operation_id=delete_operation["operationId"],
            )

    def create_apply_commands(self):
        for url, path in self.openapi["paths"].items():
            for method, operation in path.items():
                if method not in ("put", "post"):
                    continue

                if "200" in operation["responses"]:
                    # use default
                    output_handlers = None
                else:
                    output_handlers = (default_template_output,)

                self.create_apply_command(
                    operation_id=operation["operationId"],
                    method=method,
                    output_handlers=output_handlers,
                )
