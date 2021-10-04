from unittest.mock import Mock, patch

from .jsonpath import JSONPathOutputHandler


@patch("camundactl.output.jsonpath.click")
def test_handle(click: Mock):
    oh = Mock()

    JSONPathOutputHandler.handle(oh, {"hello": "world"}, "$.hello")

    click.echo.assert_called_with("world")
