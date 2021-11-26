from typing import Optional

from requests import Session, session

from camundactl.config import ConfigDict, EngineDict


def create_session(engine_config: EngineDict) -> Session:
    s = session()
    auth = engine_config.get("auth")
    if auth:
        s.auth = (auth["user"], auth["password"])
    if "verify" in engine_config:
        s.verify = engine_config["verify"]
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


def create_client(
    config_: ConfigDict,
    selected_engine: Optional[str] = None,
) -> Client:

    if not config_["engines"]:
        raise Exception("invalid configuration")

    if selected_engine is None:
        selected_engine = config_.get("current_engine")
    if not selected_engine:
        raise Exception("no current and no given engine")

    for engine in config_["engines"]:
        if selected_engine == engine["name"]:
            return Client(create_session(engine), engine["url"])
    else:
        raise Exception(f"no engine with name: {selected_engine}")
