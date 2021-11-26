import json
import logging
from functools import partial
from typing import Callable, Dict, List, Optional, Tuple, TypedDict

import click
import jsonschema
import yaml
from toolz import first

from camundactl.client import Client
from camundactl.cmd.context import ensure_object
from camundactl.cmd.helpers import (
    ArgumentTuple,
    OptionTuple,
    with_args_factory,
    with_exception_handler,
    with_query_option_factory,
)
from camundactl.openapi.cache import OpenAPISpecCache
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

logger = logging.getLogger(__name__)

get = None


@ensure_object()
def generic_autocomplete(
    ctx: click.Context, param: str, incomplete: str, endpoint: str
) -> List[str]:
    client: Client = ctx.obj["client"]
    resp = client.get(endpoint)
    try:
        resp.raise_for_status()
    except Exception as error:
        logger.error("error autocompleting param '%s': %s", param, error)
        return []
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


class OpenAPIOperationDict(TypedDict):
    description: str


APIPath = str


class OpenAPIDict(TypedDict):
    version: dict[str, str]
    paths: dict[APIPath, OpenAPIOperationDict]


class OpenAPICommandFactory(object):
    def __init__(
        self, openapi: OpenAPIDict, openapi_cache: Optional[OpenAPISpecCache] = None
    ):
        self.openapi = openapi
        self._definition_cache = {}
        self.openapi_cache = openapi_cache or OpenAPISpecCache(openapi)

    def _build_operation_id_cache(self) -> dict:
        cache = dict()
        for path, path_definition in self.openapi["paths"].items():
            for method, definition in path_definition.items():
                operation_id = definition["operationId"]
                cache[operation_id] = {
                    "path": path,
                    "method": method,
                    "definition": definition,
                }
        return cache

    def _get_operation_definition(
        self, operation_id: str, method: str
    ) -> tuple[str, OpenAPIOperationDict]:

        if not self._definition_cache:
            self._definition_cache = self._build_operation_id_cache()

        try:
            item = self._definition_cache[operation_id]
        except KeyError:
            raise Exception("invalid operation id " + operation_id)
        return item["path"], item["definition"]

    def _create_command_name(self, definition) -> str:
        operation = definition["operationId"]
        for value in ("get", "delete", "resolve", "update", "set"):
            if operation.startswith(value) and operation != value:
                operation = operation[len(value) :]
                break
        operation = operation[0].lower() + operation[1:]
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
        output_handlers: Optional[Tuple[OutputHandler]] = None,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):

        path = self.openapi_cache.get_operation_id_path(operation_id)
        definition = self.openapi_cache.get_operation_id_spec(operation_id)
        try:
            schema = self.openapi_cache.get_operation_id_schema(operation_id)
        except KeyError:
            schema = None

        command_name = self._create_command_name(definition)
        command_desc = "\n".join(
            filter(
                None,
                (
                    definition.get("summary"),
                    definition["description"],
                    "",
                    f"URL: `{path}`",
                    "",
                    f"Schema: `{schema or '-'}`",
                ),
            )
        )

        options = self._get_options(definition, options_autocomplete)
        args = self._get_args(definition, args_autocomplete)

        command = with_output(*output_handlers)(command)
        command = with_query_option_factory(options=options, name="options")(command)
        command = with_args_factory(args=args, name="args")(command)
        command = with_exception_handler()(command)
        command = click.pass_context(command)
        command = click.command(
            command_name, short_help=definition.get("description"), help=command_desc
        )(command)

        return command

    def _has_list_response(
        self, definition: OpenAPIOperationDict, status_code: str = "200"
    ) -> bool:
        try:
            schema = definition["responses"][status_code]["content"][
                "application/json"
            ]["schema"]
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

        path = self.openapi_cache.get_operation_id_path(operation_id)
        definition = self.openapi_cache.get_operation_id_spec(operation_id)

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

        options_autocomplete = (
            options_autocomplete or self._get_default_options_autocomplete(definition)
        )

        command_name = operation_id
        command_help = definition.get("summary")

        return self.create_command(
            command=command,
            operation_id=operation_id,
            output_handlers=output_handlers or default_output_handlers,
            args_autocomplete=args_autocomplete
            or self._get_default_args_autocomplete(path),
            options_autocomplete=options_autocomplete,
        )

    def create_delete_command(
        self,
        operation_id,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ) -> click.Command:
        path, definition = self._get_operation_definition(operation_id, "delete")

        def command(ctx: click.Context, options: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.delete(path.format(**args), params=options)
            resp.raise_for_status()

        return self.create_command(
            command=command,
            operation_id=operation_id,
            output_handlers=(default_template_output,),
            args_autocomplete=args_autocomplete
            or self._get_default_args_autocomplete(path),
            options_autocomplete=options_autocomplete
            or self._get_default_options_autocomplete(definition),
        )

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
            "-f",
            "--file",
            "file_input",
            type=click.File(),
            required=False,
            default=None,
            help="input as yaml",
        )
        def command(
            ctx: click.Context,
            options: Dict,
            args: Dict,
            skip_validation: bool,
            file_input,
        ):
            client: Client = ctx.obj["client"]

            data = yaml.load(file_input, Loader=yaml.FullLoader)

            if data and not skip_validation:
                schema = self.openapi_cache.get_operation_id_schema(operation_id)
                jsonschema.validate(data, schema)

            extra = {}
            if data:
                extra["json"] = data

            extra["headers"] = {"Content-Type": "application/json"}

            resp = getattr(client, method)(path.format(**args), params=options, **extra)
            try:
                resp.raise_for_status()
            except Exception:
                click.secho(resp.text, fg="red")
                raise
            if "application/json" in resp.headers.get("Content-Type"):
                return resp.json()

        return self.create_command(
            command=command,
            operation_id=operation_id,
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

    def create_get_commands(self) -> None:
        for _, path in self.openapi["paths"].items():
            get_operation = path.get("get")
            if not get_operation:
                continue

            self.create_get_command(
                operation_id=get_operation["operationId"],
            )

    def create_delete_commands(self) -> None:
        for _, path in self.openapi["paths"].items():
            delete_operation = path.get("delete")
            if not delete_operation:
                continue

            self.create_delete_command(
                operation_id=delete_operation["operationId"],
            )

    def create_apply_commands(self) -> None:
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
