from types import FunctionType
from typing import Dict
from unittest.mock import Mock, patch
from uuid import uuid4

import click
import pytest
from requests.exceptions import HTTPError

from camundactl.output.base import OutputHandler

from .factory import OpenAPICommandFactory, generic_autocomplete


@patch("camundactl.cmd.openapi.factory.prepare_context")
def test_generic_autocomplete_list(_: Mock) -> None:
    url = "http://www.camunda-engine.test"
    id_1 = str(uuid4())
    id_2 = str(uuid4())

    response = Mock()
    response.json.return_value = [{"id": id_1}, {"id": id_2}]

    client = Mock()
    client.get.return_value = response

    context = Mock(spec=click.Context)
    context.obj = dict(client=client)

    result = generic_autocomplete(context, "", "", url)

    assert id_1 in result
    assert id_2 in result


@patch("camundactl.cmd.openapi.factory.prepare_context")
@patch("camundactl.cmd.openapi.factory.logger")
def test_generic_autocomplete_http_error(logger: Mock, _: Mock) -> None:
    url = "http://www.camunda-engine.test"

    response = Mock()
    response.raise_for_status.side_effect = HTTPError()

    client = Mock()
    client.get.return_value = response

    context = Mock(spec=click.Context)
    context.obj = dict(client=client)

    result = generic_autocomplete(context, "", "", url)

    assert [] == result
    logger.error.assert_called()


@patch("camundactl.cmd.openapi.factory.prepare_context")
def test_generic_autocomplete_partial(_: Mock) -> None:
    url = "http://www.camunda-engine.test"
    id_1 = "abcdef"
    id_2 = "ghijkl"

    response = Mock()
    response.json.return_value = [{"id": id_1}, {"id": id_2}]

    client = Mock()
    client.get.return_value = response

    context = Mock(spec=click.Context)
    context.obj = dict(client=client)

    result = generic_autocomplete(context, "", "ghi", url)

    assert id_2 in result
    assert id_1 not in result


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("getTest", "test"),
        ("deleteTest", "test"),
        ("resolveTest", "test"),
        ("updateTest", "test"),
        ("setTest", "test"),
        ("notFound", "notFound"),
    ],
)
def test_openapi_command_factory_create_command_name(
    operation: str,
    expected: str,
) -> None:
    result = OpenAPICommandFactory._create_command_name(
        Mock(), {"operationId": operation}
    )
    assert result == expected


@pytest.mark.parametrize(
    "type_,type_expected,multiple_expected",
    [
        ("string", str, True),
        ("integer", int, False),
        ("boolean", bool, False),
        ("unknown", str, False),
    ],
)
def test_openapi_command_factory_get_options(
    type_: str, type_expected: type, multiple_expected: bool
) -> None:
    name = str(uuid4())
    description = str(uuid4())
    autocomplete_mock = Mock()
    options_autocomplete = {name: autocomplete_mock}

    definition = {
        "parameters": [
            {
                "in": "query",
                "name": name,
                "description": description,
                "schema": {"type": type_},
            },
            {"in": "no-query"},
        ]
    }
    result = OpenAPICommandFactory._get_options(None, definition, options_autocomplete)

    assert len(result) == 1

    option, *_ = result

    assert option.name == name
    assert option.help == description
    assert option.multiple is multiple_expected
    assert option.type_ == type_expected
    assert option.autocomplete == autocomplete_mock


def test_openapi_command_factory_get_operation_definition() -> None:
    test_operation_id = "test-op-id"
    test_method = "get"
    test_operation = {"operationId": test_operation_id}
    test_method_operation = {test_method: test_operation}
    test_path = "/path"
    openapi_test = {"paths": {test_path: test_method_operation}}
    f = OpenAPICommandFactory(openapi_test)

    res_path, res_op = f._get_operation_definition(test_operation_id, test_method)

    assert test_path == res_path
    assert test_operation == res_op


def test_openapi_command_factory_get_operation_definition_error() -> None:
    openapi_test = {"paths": {}}
    factory = OpenAPICommandFactory(openapi_test)
    with pytest.raises(Exception):
        factory._get_operation_definition("doesNotExist", "get")


def test_openapi_command_factory_get_operation_definition_not_found() -> None:
    openapi_test = {"paths": []}
    f = OpenAPICommandFactory(openapi_test)

    with pytest.raises(Exception):
        f._get_operation_definition("not-exists", "get")


@pytest.mark.parametrize(
    "operation_id,expected",
    [
        ("getOperationName", "operationName"),
        ("deleteOperationName", "operationName"),
        ("resolveOperationName", "operationName"),
        ("updateOperationName", "operationName"),
        ("setOperationName", "operationName"),
        ("OperationName", "operationName"),
    ],
)
def test_openapi_command_factory_create_command_name(
    operation_id: str, expected: str
) -> None:
    definition = {"operationId": operation_id}
    name = OpenAPICommandFactory._create_command_name(None, definition)
    assert name == expected


@pytest.mark.parametrize(
    "name,description,callback",
    [
        ("name1", "description1", None),
        ("name1", "description1", Mock()),
    ],
)
def test_openapi_command_factory_get_args(name, description, callback) -> None:
    args_autocomplete = {}
    if callback:
        args_autocomplete[name] = callback
    definition = {
        "parameters": (
            {"in": "path", "name": name, "description": description},
            {"in": "not-path"},
        )
    }
    result = OpenAPICommandFactory._get_args(
        Mock(spec=OpenAPICommandFactory),
        definition,
        args_autocomplete,
    )
    assert len(result) == 1
    arg, *_ = result
    assert arg.name == name
    assert arg.help == description
    assert arg.autocomplete is callback


def test_openapi_command_factory_create_command():
    operation_id = "getOperationId"
    operation_help = "i am the help text"
    operation_path = "/path"
    operation_method = "get"

    openapi_test = {
        "paths": {
            operation_path: {
                operation_method: {
                    "operationId": operation_id,
                    "description": operation_help,
                    "parameters": [],
                }
            }
        }
    }

    factory = OpenAPICommandFactory(openapi_test)

    command_mock = Mock(spec=FunctionType)
    parent_mock = Mock(spec=click.Group)
    decorator_mock = Mock()
    command_mock = Mock()
    command_mock.return_value = decorator_mock
    parent_mock.command = command_mock

    factory.create_command(
        command_mock,
        operation_id,
        operation_method,
        parent_mock,
        [Mock(spec=OutputHandler)],
        [],
        [],
    )

    command_mock.called_with("operationId", help=operation_help)
    assert decorator_mock.called


@pytest.mark.parametrize(
    "schema,expected",
    [
        ({"schema": {"type": "array"}}, True),
        ({"schema": {"type": "string"}}, False),
        ({}, True),
    ],
)
def test_openapi_command_factory_has_list_response_true(
    schema: Dict,
    expected: bool,
) -> None:
    definition = {
        "responses": {
            "200": {
                "content": {
                    "application/json": schema,
                },
            },
        }
    }
    has_list_response = OpenAPICommandFactory._has_list_response(Mock(), definition)
    assert has_list_response is expected
