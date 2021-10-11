from unittest.mock import Mock, patch

import click

from .base import AliasGroup


@patch("camundactl.cmd.base.load_config")
def test_alias_group_(load_config: Mock):
    command_name = "testCommand"
    command_alias = "tc"
    load_config.return_value = {"alias": {command_alias: command_name}}
    command_mock = Mock(spec=click.Command)
    group = AliasGroup()
    group.add_command(command_mock, name=command_name)
    command = group.get_command(Mock(), command_name)
    assert command == command_mock
