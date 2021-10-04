from unittest.mock import Mock

from .base import OutputHandler


def test_outputhandler():

    result = "result"
    func_mock = Mock()
    func_mock.return_value = result

    oh = Mock()
    oh.name = "output-name"
    oh.current_output = "output-name"

    option = Mock()
    option.return_value = func_mock
    oh.options = {"output_format": option}

    func_args = Mock()

    wrapper = OutputHandler.apply(oh, func_mock)
    wrapper(func_args, output_format="some-format")

    option.assert_called_with(func_mock)
    func_mock.assert_called_with(func_args)

    oh.handle.assert_called_with(result, output_format="some-format")


def test_outputhandler_outher_output():
    func_mock = Mock()

    option = Mock()
    option.return_value = func_mock

    oh = Mock()
    oh.name = "name"
    oh.current_output = "another"

    oh.options = {"output_format": option}

    wrapper = OutputHandler.apply(oh, func_mock)
    wrapper(output_format=None)

    func_mock.assert_called()
    assert oh.handle.called is False
