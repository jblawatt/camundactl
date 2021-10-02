from typing import Type
from .factory import OpenAPICommandFactory, generic_autocomplete
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4
from requests.exceptions import HTTPError
import pytest
import responses
import click


@patch("camundactl.cmd.openapi.factory._create_client")
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


@patch("camundactl.cmd.openapi.factory._create_client")
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


@patch("camundactl.cmd.openapi.factory._create_client")
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
        None, {"operationId": operation}
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
):
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


def test_openapi_command_factory_get_args():

    name = str(uuid4())
    description = str(uuid4())

    autocomplete_mock = Mock()
    args_autocomplete = {name: autocomplete_mock}

    definition = {
        "parameters": [
            {
                "in": "path",
                "name": name,
                "description": description,
            },
            {"in": "no-query"},
        ]
    }

    result = OpenAPICommandFactory._get_args(None, definition, args_autocomplete)

    assert len(result) == 1

    argument, *_ = result

    assert argument.name == name
    assert argument.help == description
    assert argument.autocomplete == autocomplete_mock

