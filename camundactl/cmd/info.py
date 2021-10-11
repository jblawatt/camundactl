import click
from jinja2 import Template

from camundactl.client import Client, create_session
from camundactl.cmd.base import root
from camundactl.config import EngineDict, get_configfile, load_config

template = Template(
    """        _   _
  __ __| |_| |
 / _/ _|  _| |
 \__\__|\__|_|

cctl -- Camunda Control
~~~~~~~~~~~~~~~~~~~~~~~

Version:        ---
Git:            ---
Current Engine: {{config.current_engine}}
Config-File:    {{config_file}}

OpenAPI:
    Title:       {{openapi.info.title}}
    Description: {{openapi.info.description}}
    Version:     {{openapi.info.version}}

Engines: {% if config.engines %}{% for engine in config.engines %}
    - Name: {{engine.name}}
      URL: {{engine.url}}
      Version: {{ camunda_engine_version(engine) }}{% endfor %}{% else %}-{% endif %}

Extra Paths: {%if config.extra_path %}{% for ep in config.extra_paths %}
    - {{ep}} {% endfor %}{% else %}-{% endif %}

"""
)


def camunda_engine_version(engine: EngineDict) -> str:
    session = create_session(engine)
    client = Client(session, engine["url"])
    try:
        resp = client.get("/version")
        resp.raise_for_status()
    except Exception:
        return "OFFLINE"
    else:
        resp_json: dict[str, str] = resp.json()
        return resp_json["version"]


@root.command()
def info() -> None:
    config = load_config()

    click.echo(
        template.render(
            config=config,
            openapi="",
            camunda_engine_version=camunda_engine_version,
            config_file=get_configfile(),
        )
    )
