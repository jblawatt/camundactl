import click

from typing import Dict

from camundactl.client import create_client
from camundactl.cmd.base import root
from camundactl.cmd.context import ensure_object
from camundactl.output.decorator import with_output
from camundactl.output.template import TemplateOutputHandler
from camundactl.config import EngineDict, get_configfile, ConfigDict


def camunda_engine_version(engine: EngineDict) -> str:
    client = create_client(engine)
    try:
        resp = client.get("/version")
        resp.raise_for_status()
    except Exception:
        return "OFFLINE"
    else:
        resp_json: dict[str, str] = resp.json()
        return resp_json["version"]


@root.command()
@with_output(TemplateOutputHandler(default_template="info.tpl"))
@click.pass_context
def info(ctx: click.Context) -> Dict:
    config: ConfigDict = ctx.obj.get_config()
    return dict(
            config=config,
        openapi_specs= [],
            camunda_engine_version=camunda_engine_version,
            config_file=get_configfile(),
    )
