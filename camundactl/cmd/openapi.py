from functools import partial
import yaml
import json
import jsonschema
from typing import Callable, Dict, List, Optional, Tuple

import click

from camundactl.client import Client
from camundactl.cmd.base import _ensure_client, delete, get, apply
from camundactl.cmd.helpers import (
    ArgumentTuple,
    OptionTuple,
    with_args_factory,
    with_output,
    with_query_option_factory,
    default_table_output,
    default_json_output,
    default_jsonpath_output,
    default_template_output,
    default_object_table_output,
    default_raw_output,
)


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
    generic_autocomplete, endpoint="/process-instance"
)
incidents_autocomplete = partial(generic_autocomplete, endpoint="/incident")
process_definition_autocomplete = partial(
    generic_autocomplete, endpoint="/process-definition"
)
task_id_autocomplete = partial(generic_autocomplete, endpoint="/task")


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

    def create_get(
        self,
        operation_id,
        parent,
        output_handlers: Optional[Tuple] = None,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):

        path, definition = self._get_operation_definition(operation_id, "get")

        operation = self._create_name(definition)
        description = definition["description"] + " (URL: " + path + ")"

        options = self._get_options(definition, options_autocomplete)
        args = self._get_args(definition, args_autocomplete)

        default_output_handlers = (
            default_table_output,
            default_json_output,
            default_jsonpath_output,
            default_template_output,
            default_raw_output,
        )

        @with_output(*(output_handlers or default_output_handlers))
        @with_query_option_factory(options=options, name="options")
        @with_args_factory(args=args, name="args")
        @click.pass_context
        def command(ctx: click.Context, options: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.get(path.format(**args), params=options)
            resp.raise_for_status()
            if "application/json" in resp.headers.get("Content-Type"):
                return resp.json()
            return resp.content

        parent.command(operation, help=description)(command)

    def create_delete(
        self,
        operation_id,
        parent,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
    ):
        path, definition = self._get_operation_definition(operation_id, "delete")

        operation = self._create_name(definition)
        description = definition["description"] + " (URL: " + path.strip() + ")"

        params = self._get_options(definition, options_autocomplete)
        args = self._get_args(definition, args_autocomplete)

        @with_output(default_template_output)
        @with_query_option_factory(options=params, name="params")
        @with_args_factory(args=args, name="args")
        @click.pass_context
        def command(ctx: click.Context, params: Dict, args: Dict):
            client: Client = ctx.obj["client"]
            resp = client.delete(path.format(**args), params=params)
            resp.raise_for_status()
            return "Ok"

        parent.command(operation, help=description)(command)

    def create_apply(
        self,
        operation_id,
        parent,
        output_handlers: Optional[Tuple] = None,
        args_autocomplete: Optional[Dict[str, Callable]] = None,
        options_autocomplete: Optional[Dict[str, Callable]] = None,
        method: str = "put",
    ):
        path, definition = self._get_operation_definition(operation_id, method)

        try:
            request_body_ref = definition["requestBody"]["content"]["application/json"][
                "schema"
            ]["$ref"]
        except KeyError:
            schema = {}
        else:
            __, __, schema_name = request_body_ref.strip("#").strip("/").split("/")
            schema = self.openapi["components"]["schemas"][schema_name]

        operation = self._create_name(definition)
        description = (
            definition["description"]
            + " (URL: "
            + path.strip()
            + ")"
            + "\n"
            + json.dumps(schema, indent=2)
        )

        default_output_handlers = (default_template_output,)

        params = self._get_options(definition, options_autocomplete)
        args = self._get_args(definition, args_autocomplete)

        @with_output(*(output_handlers or default_output_handlers))
        @with_query_option_factory(options=params, name="params")
        @with_args_factory(args=args, name="args")
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
        @click.pass_context
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
            return "ok"

        parent.command(operation, help=description)(command)

    def create_get_commands(self):
        for url, path in self.openapi["paths"].items():
            get_operation = path.get("get")
            if not get_operation:
                continue

            args_autocomplete = {}

            if url.startswith("/process-instance/{id}"):
                args_autocomplete.update({"id": process_instance_autocomplete})
            if url.startswith("/process-definition/{id}"):
                args_autocomplete.update({"id": process_definition_autocomplete})
            if url.startswith("/task/{id}"):
                args_autocomplete.update({"id": task_id_autocomplete})
            if url.startswith("/incident/{id}"):
                args_autocomplete.update({"id": incidents_autocomplete})

            output_handlers = (
                default_json_output,
                default_jsonpath_output,
                default_template_output,
                default_raw_output,
            )

            try:
                schema = get_operation["responses"]["200"]["content"][
                    "application/json"
                ]["schema"]
            except KeyError:
                pass
            else:
                if schema.get("type") == "array":
                    output_handlers = (default_table_output,) + output_handlers
                if schema.get("type") == "object":
                    output_handlers = (default_object_table_output,) + output_handlers

            self.create_get(
                operation_id=get_operation["operationId"],
                parent=get,
                output_handlers=output_handlers,
                args_autocomplete=args_autocomplete,
                options_autocomplete={
                    "processInstanceId": process_definition_autocomplete,
                    "taskId": task_id_autocomplete,
                    "incidentId": incidents_autocomplete,
                    "processDefinitionId": process_definition_autocomplete,
                },
            )

    def create_delete_commands(self):
        for url, path in self.openapi["paths"].items():
            delete_operation = path.get("delete")
            if not delete_operation:
                continue

            args_autocomplete = {}

            if url.startswith("/process-instance/{id}"):
                args_autocomplete.update({"id": process_instance_autocomplete})
            if url.startswith("/process-definition/{id}"):
                args_autocomplete.update({"id": process_definition_autocomplete})
            if url.startswith("/task/{id}"):
                args_autocomplete.update({"id": task_id_autocomplete})
            if url.startswith("/incident/{id}"):
                args_autocomplete.update({"id": incidents_autocomplete})

            self.create_delete(
                operation_id=delete_operation["operationId"],
                parent=delete,
                args_autocomplete=args_autocomplete,
                options_autocomplete={
                    "processInstanceId": process_definition_autocomplete,
                    "taskId": task_id_autocomplete,
                    "incidentId": incidents_autocomplete,
                    "processDefinitionId": process_definition_autocomplete,
                },
            )

    def create_apply_commands(self):
        for url, path in self.openapi["paths"].items():
            for method, operation in path.items():
                if method not in ("put", "post"):
                    continue

                args_autocomplete = {}

                if "200" in operation["responses"]:
                    output_handlers = (
                        default_json_output,
                        default_jsonpath_output,
                        default_template_output,
                        default_raw_output,
                    )
                else:
                    output_handlers = (default_template_output,)

                if url.startswith("/process-instance/{id}"):
                    args_autocomplete.update({"id": process_instance_autocomplete})
                if url.startswith("/process-definition/{id}"):
                    args_autocomplete.update({"id": process_definition_autocomplete})
                if url.startswith("/task/{id}"):
                    args_autocomplete.update({"id": task_id_autocomplete})
                if url.startswith("/incident/{id}"):
                    args_autocomplete.update({"id": incidents_autocomplete})

                self.create_apply(
                    operation_id=operation["operationId"],
                    parent=apply,
                    method=method,
                    output_handlers=output_handlers,
                    args_autocomplete=args_autocomplete,
                )


factory = CommandFactory(json.load(open("openapi.json", "r")))
factory.create_get_commands()
factory.create_delete_commands()
factory.create_apply_commands()
