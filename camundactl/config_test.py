import pytest
from toolz import first
from unittest.mock import patch, Mock

from camundactl.config import EngineDict, ConfigDict, add_engine, EngineExistsError


@pytest.fixture
def new_engine() -> EngineDict:
    return {
        "name": "new-engine",
        "url": "http://test.camunda/engine-rest",
        "verify": False,
        "spec_version": "latest",
        "auth": {"user": "camunda", "password": "camunda"},
    }


@pytest.fixture
def engine() -> EngineDict:
    return {
        "name": "existing-engine",
        "url": "http://existing.camunda/engine-rest",
        "verify": False,
        "spec_version": "latest",
        "auth": {"user": "camunda", "password": "camunda"},
    }


@pytest.fixture
def config_with_new_engine(new_engine: EngineDict):
    return {"engines": [new_engine]}


@pytest.fixture
def config_with_engine(engine: EngineDict):
    return {"engines": [engine], "current_engine": engine["name"]}


@pytest.fixture
def config_no_engines() -> ConfigDict:
    return {"engines": []}


@patch("camundactl.config.load_config")
@patch("camundactl.config._write_config")
def test__add_engine_select_first(
    write_config: Mock,
    load_config: Mock,
    new_engine: EngineDict,
    config_no_engines: ConfigDict,
):
    load_config.return_value = config_no_engines

    add_engine(new_engine, False)

    assert write_config.called
    args, _ = write_config.call_args
    config, *_ = args

    assert config["current_engine"] == new_engine["name"]
    assert len(config["engines"]) == 1
    assert first(config["engines"]) == new_engine


@patch("camundactl.config.load_config")
@patch("camundactl.config._write_config")
def test__add_engine_no_select(
    write_config: Mock,
    load_config: Mock,
    new_engine: EngineDict,
    config_with_engine: ConfigDict,
):
    load_config.return_value = config_with_engine

    add_engine(new_engine, False)

    assert write_config.called
    args, _ = write_config.call_args
    config, *_ = args

    assert config["current_engine"] != new_engine["name"]
    assert len(config["engines"]) == 2
    assert any(new_engine == e for e in config["engines"])


@patch("camundactl.config.load_config")
@patch("camundactl.config._write_config")
def test__add_engine_select(
    write_config: Mock,
    load_config: Mock,
    new_engine: EngineDict,
    config_with_engine: ConfigDict,
):
    load_config.return_value = config_with_engine

    add_engine(new_engine, True)

    assert write_config.called
    args, _ = write_config.call_args
    config, *_ = args

    assert config["current_engine"] == new_engine["name"]
    assert len(config["engines"]) == 2
    assert any(new_engine == e for e in config["engines"])


@patch("camundactl.config.load_config")
def test_add_engine_exists(
    load_config: Mock,
    new_engine: EngineDict,
    config_with_new_engine: ConfigDict,
):

    load_config.return_value = config_with_new_engine
    with pytest.raises(EngineExistsError):
        add_engine(new_engine)
