from requests import Session, session

from camundactl.context import EngineDict


def create_session(engine_config: EngineDict) -> Session:
    s = session()
    auth = engine_config.get("auth")
    if auth:
        s.auth = (auth["user"], auth["password"])
    s.verify = engine_config.get("verify", True)
    return s


class Client:
    def __init__(self, session: Session, base_url: str):
        self.base_url = base_url
        self.session = session

    def get(self, path: str, /, **kwargs):
        return self.session.get(self.base_url + path, **kwargs)

    def post(self, path, /, **kwargs):
        return self.session.post(self.base_url + path, **kwargs)

    def put(self, path, /, **kwargs):
        return self.session.put(self.base_url + path, **kwargs)

    def delete(self, path, /, **kwargs):
        return self.session.delete(self.base_url + path, **kwargs)
