import json
from importlib.resources import files, open_text
from typing import cast

from camundactl.config import load_config


def load_spec() -> dict:
    spec_module = "camundactl.cmd.openapi.openapi_specs"

    config = load_config()
    spec_version = config.get("spec_version", "latest")
    spec_filename = f"openapi-{spec_version}.json"
    try:
        spec_file = open_text(spec_module, spec_filename)
    except FileNotFoundError:
        versions = []
        for file_ in files(spec_module).glob("openapi*.json"):
            # strip "openapi-" and ".json"
            name = file_.name[8:][:-5]
            versions.append(name)
        raise Exception(
            f"No OpenAPI spec with version '{spec_version}' found. "
            f"Try one of: {', '.join(sorted(versions, reverse=True))}"
        )
    return cast(dict, json.load(spec_file))
