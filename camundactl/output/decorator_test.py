from unittest.mock import Mock, call

import click
import pytest

from camundactl.output.base import OutputHandler

from .decorator import with_output


def test_with_output():
    output_handler = Mock(spec=OutputHandler)
    output_handler.name = "test"

    output_name = "test"

    @with_output(output_handler)
    def func(*a, **kw):
        pass

    func(ctx=Mock(), output=output_name)

    output_handler.apply.assert_called()
    assert output_handler.set_current_output.call_count == 2

    output_handler.set_current_output.assert_has_calls([call(output_name), call(None)])


def test_with_output_invalid_output():
    output_handler = Mock(spec=OutputHandler)
    output_handler.name = "test"

    @with_output(output_handler)
    def func(*a, **kw):
        pass

    with pytest.raises(click.ClickException):
        func(ctx=Mock(), output="invalid-name")


def test_with_output_no_handler_error():
    with pytest.raises(Exception):

        @with_output()
        def func(*a, **kw):
            pass
