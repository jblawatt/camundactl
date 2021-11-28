from jinja2.environment import Environment
from jinja2.loaders import (
    ChoiceLoader,
    DictLoader,
    FileSystemLoader,
    PackageLoader,
    BaseLoader,
)
import pytest
import click
from unittest.mock import Mock, patch

from camundactl.config import ConfigDict
from camundactl.cmd.context import ContextObject
from camundactl.output.template import TemplateOutputHandler


@pytest.fixture
def config_dict() -> ConfigDict:
    return {"template": {"extra_paths": ["eins", "zwei"]}}


@pytest.fixture
def context_object(config_dict: ConfigDict) -> ContextObject:
    obj = Mock(spec=ContextObject)
    obj.get_config.return_value = config_dict
    return obj


@pytest.fixture
def click_context(context_object: ContextObject) -> click.Context:
    context = Mock(spec=["obj", "command", "parent"])
    context.obj = context_object
    context.command.name = "mock_command"
    context.parent.command.name = "mock_command_parent"
    return context


@pytest.fixture
def tpl_lookup_context() -> dict:
    return {
        "operation_id": "operation-id",
        "verb": "test",
    }


@pytest.fixture
def template_output_handler_default(tpl_lookup_context: dict) -> TemplateOutputHandler:
    return TemplateOutputHandler(tpl_lookup_context=tpl_lookup_context)


def test_TemplateOutputHandler_create_loaders_with_ctx(
    template_output_handler_default: TemplateOutputHandler,
    click_context: click.Context,
) -> None:
    """
    tests weather the FileSystemLoaders for the extra_paths
    in then configuration become loaded
    """
    template_output_handler_default.ctx = click_context
    loaders = template_output_handler_default._create_loaders()
    loaders = list(loaders)
    assert len(loaders) == 5
    a, b, c, d, e = loaders
    assert isinstance(a, DictLoader)
    assert isinstance(b, FileSystemLoader)
    assert isinstance(c, FileSystemLoader)
    assert isinstance(d, FileSystemLoader)
    assert isinstance(e, PackageLoader)


def test_TemplateOutputHandler_create_loaders_without_ctx(
    template_output_handler_default: TemplateOutputHandler,
) -> None:
    """
    tests weather the config loading becomes ignored if the
    context is not set.
    """
    loaders = template_output_handler_default._create_loaders()
    loaders = list(loaders)
    assert len(loaders) == 3
    a, b, c = loaders
    assert isinstance(a, DictLoader)
    assert isinstance(b, FileSystemLoader)
    assert isinstance(c, PackageLoader)


def test_TemplateOutputHandler_create_environment(
    template_output_handler_default: TemplateOutputHandler,
) -> None:
    mock_loader = Mock(spec=BaseLoader)
    create_loader_mock = Mock()
    create_loader_mock.return_value = [mock_loader]
    template_output_handler_default._create_loaders = create_loader_mock
    env = template_output_handler_default._create_environment()

    assert isinstance(env, Environment)
    assert isinstance(env.loader, ChoiceLoader)
    assert len(env.loader.loaders) == 1
    assert env.loader.loaders[0] == mock_loader


def test_TemplateOutputHandler_create_tpl_lookup_context_without_ctx(
    template_output_handler_default: TemplateOutputHandler,
    tpl_lookup_context: dict,
) -> None:
    ctx = template_output_handler_default._create_tpl_lookup_context()
    assert ctx["command"] == "NO_COMMAND_FOUND"
    assert ctx["parent"] == "NO_PARENT_FOUND"
    for key, value in tpl_lookup_context.items():
        assert ctx[key] == value


def test_TemplateOutputHandler_create_tpl_lookup_context_with_ctx(
    template_output_handler_default: TemplateOutputHandler,
    tpl_lookup_context: dict,
    click_context: click.Context,
) -> None:
    template_output_handler_default.ctx = click_context
    ctx = template_output_handler_default._create_tpl_lookup_context()
    assert ctx["command"] == "mock_command"
    assert ctx["parent"] == "mock_command_parent"
    for key, value in tpl_lookup_context.items():
        assert ctx[key] == value
