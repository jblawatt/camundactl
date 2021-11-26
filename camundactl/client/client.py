from typing import Any, Dict, List, Optional, TypedDict


class OpenAPILicense(TypedDict):
    name: str
    url: str


class OpenAPIInfo(TypedDict):
    title: str
    descrition: str
    version: str
    licence: OpenAPILicense


class OpenAPIPath(TypedDict):
    pass


class OpenAPISpec(TypedDict):
    openapi: str
    info: OpenAPIInfo
    externalDocs: Dict[str, str]
    paths: Dict[str, OpenAPIPath]


class CamundaOpenAPIClient:
    def __init__(self, spec: OpenAPISpec, client: Any):
        self.spec = spec
        self.client = client

    def get_operation_ids(self, filter_verb: Optional[str] = None) -> List[str]:
        for _, conf in self.spec["paths"].items():
            for verb, op_conf in conf.items():
                if filter_verb is None or filter_verb == verb:
                    yield op_conf["operationId"]

    @classmethod
    def for_version(cls, version: str):
        return cls()
