from camundactl.openapi.cache import OpenAPISpecCache
from camundactl.client import Client
from camundactl.cmd.context import ContextObject


def test_ContextObject_get_client():
    co = ContextObject()

    client = co.get_client()
    assert isinstance(client, Client)


def test_ContextObject_get_config():
    co = ContextObject()

    config = co.get_config()
    assert isinstance(config, dict)


def test_ContextObject_get_spec_cache():
    co = ContextObject()

    spec_cache = co.get_spec_cache()
    assert isinstance(spec_cache, OpenAPISpecCache)
