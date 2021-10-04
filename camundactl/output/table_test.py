from typing import Any
from unittest.mock import Mock, patch

import pytest
from requests.sessions import default_headers

from .table import ObjectTableOutputHandler, TableOutputHandler, _ensure_length


@pytest.mark.parametrize(
    "input_,expected",
    [
        ("hello", "hello"),
        ("hello world", "hello..."),
        (1337, 1337),
    ],
)
def test_ensure_length_untouch(input_, expected):
    assert _ensure_length(input_, max_length=5) == expected


@patch("camundactl.output.table.click")
@patch("camundactl.output.table.tabulate")
def test_table_output_handle(tabulate: Mock, click: Mock):
    handler = TableOutputHandler()
    result = [
        {"a": "abc", "b": "bcd", "c": "cde"},
        {"a": "bcd", "b": "cde", "c": "def"},
    ]

    handler.handle(result, None, 40)
    expected = [
        ["abc", "bcd", "cde"],
        ["bcd", "cde", "def"],
    ]
    tabulate.assert_called_with(
        expected,
        headers=[
            "a",
            "b",
            "c",
        ],
    )


@pytest.mark.parametrize("result", [None, []])
@patch("camundactl.output.table.click")
def test_table_empty(click: Mock, result: Any):
    handler = TableOutputHandler()
    handler.handle(result, None, 40)
    click.echo.assert_called_with("empty result")


@patch("camundactl.output.table.click")
@patch("camundactl.output.table.tabulate")
def test_table_strings(tabulate: Mock, click: Mock):
    result = ["a", "b", "c"]
    handler = TableOutputHandler()
    handler.handle(result, None, 40)

    tabulate.assert_called_with([(v,) for v in result], headers=("unknown",))


@patch("camundactl.output.table.click")
@patch("camundactl.output.table.tabulate")
def test_table_with_headers(tabulate: Mock, click: Mock):
    handler = TableOutputHandler()
    result = [
        {"a": "abc", "b": "bcd", "c": "cde"},
        {"a": "bcd", "b": "cde", "c": "def"},
    ]

    handler.handle(result, "a,b", 40)
    expected = [
        ["abc", "bcd"],
        ["bcd", "cde"],
    ]
    tabulate.assert_called_with(
        expected,
        headers=[
            "a",
            "b",
        ],
    )


def test_table_with_invalid_headers() -> None:
    unknown_headers = Mock()
    handler = TableOutputHandler(table_headers=unknown_headers)
    with pytest.raises(Exception):
        handler.handle([], None, 40)


@patch("camundactl.output.table.TableOutputHandler.handle")
def test_objecttable_handle(handle: Mock) -> None:
    handler = ObjectTableOutputHandler()
    handler.handle({"a": "abc", "b": "def", "c": 1337}, None, 40)

    handle.assert_called_with(
        [
            {"key": "a", "value": "abc"},
            {"key": "b", "value": "def"},
            {"key": "c", "value": "1337"},
        ],
        "key,value",
        40,
    )
