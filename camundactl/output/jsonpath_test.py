from .jsonpath import JSONPathOutputHandler
from unittest.mock import patch, Mock


@patch("camundactl.output.jsonpath.click")
def test_handle(click: Mock):
    oh = Mock()

    JSONPathOutputHandler.handle(oh, {"hello": "world"}, "$.hello")

    click.echo.assert_called_with("world")
