def test_ContextObject_get_client():
    co = ContextObject()

    client = co.get_client()
    assert isinstance(client, Client)
