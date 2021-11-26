from collections import defaultdict
from typing import Dict, List, Optional

__all__ = ["OpenAPISpecCache"]


class OpenAPISpecCache:
    def __init__(self, spec: Dict):
        self.spec = spec
        self.process()

    def process(self):
        self.operation_ids = []
        self.operation_id_spec = {}
        self.operation_id_verbs = {}
        self.operation_id_paths = {}
        self.verb_operation_ids = defaultdict(list)
        self.operation_id_schema_names = {}

        for path, config in self.spec["paths"].items():
            for verb, op_conf in config.items():
                operation_id = op_conf["operationId"]
                self.operation_ids.append(operation_id)
                self.operation_id_spec[operation_id] = op_conf
                self.operation_id_verbs[operation_id] = verb
                self.operation_id_paths[operation_id] = path
                self.verb_operation_ids[verb].append(operation_id)

                try:
                    content = op_conf["requestBody"]["content"]
                    schema_ref = content["application/json"]["schema"]["$ref"]
                except KeyError:
                    # no schema
                    continue
                else:
                    __, __, schema_name = schema_ref.strip("#").strip("/").split("/")
                    self.operation_id_schema_names[operation_id] = schema_name

    def get_operation_ids(self) -> List[str]:
        return self.operation_ids

    def has_operation_id(self, operation_id: str, verb: Optional[str] = None) -> bool:
        if verb:
            return operation_id in self.verb_operation_ids[verb]
        return operation_id in self.operation_ids

    def get_operation_ids_by_verb(self, verb: str) -> List[str]:
        return self.verb_operation_ids[verb]

    def get_operation_id_spec(self, operation_id: str) -> Dict:
        return self.operation_id_spec[operation_id]

    def get_operation_id_path(self, operation_id: str) -> str:
        return self.operation_id_paths[operation_id]

    def get_operation_id_schema_name(self, operation_id: str) -> str:
        return self.operation_id_schema_names[operation_id]

    def get_operation_id_schema(self, operation_id: str) -> Dict:
        schema_name = self.get_operation_id_schema_name(operation_id)
        return self.spec["components"]["schemas"][schema_name]
