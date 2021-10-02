import json
from unittest.mock import Mock, patch

import pytest

from .json import JSONOutputHandler


@patch("camundactl.output.json.click")
def test__jsonoutputhandler_success(click: Mock):
    input_ = {"hello": "world"}
    handler = JSONOutputHandler()
    handler.handle(input_)
    click.echo.called_with(json.dumps(input_, indent=2))
