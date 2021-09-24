from camundactl.cmd.helpers import with_exception_handler
from camundactl.output.decorator import with_output
from camundactl.output import default_json_output, TemplateOutputHandler
from typing import Any, Dict

import click

from camundactl.client import Client
from camundactl.cmd.base import describe

PROCESS_INSTANCE_FILTER_PARAMS = []


DESCRIBE_PROCESS_INSTANCE_TEMPLATE = """
Id: {{id}}
BusinessKey: {{businessKey}}
TenantId: {{tenantId}}
ProcessDefinition:
    Id:      {{definitionId}}

Suspended: {{suspended}}

Incidents: {% for inc in incidents %}
    - Id:         {{inc.id}}
      Type:       {{inc.incidentType}}
      IsOpen:     {{inc.open}}
      ActivityId: {{inc.activityId}}
      Message:    {{inc.incidentMessage}} {% endfor %}

Variables: {% for var in variables%}
    - Id:    {{var.id}}
      Name:  {{var.name}}
      Type:  {{var.type}}
      Value: {{var.value}}
      {% endfor %}
"""


DESCRIBE_HISTORIC_PROCESS_INSTANCE_TEMPLATE = """
Id: {{id}}
BusinessKey: {{businessKey}}
RootProcessInstanceId: {{rootProcessInstanceId}}
TenantId: {{tenantId}}
ProcessDefinition.
    Name:    {{processDefinitionName}}
    Key:     {{processDefinitionKey}}
    Id:      {{processDefinitionId}}
    Version: {{processDefinitionVersion}}

StartTime:   {{startTime}}
EndTime:     {{startTime}}
RemovalTime: {{removalTime}}

Duration: {{durationInMillis}}

Incidents: {% for inc in incidents %}
    - Id:         {{inc.id}}
      Type:       {{inc.incidentType}}
      IsOpen:     {{inc.open}}
      ActivityId: {{inc.activityId}}
      Message:    {{inc.incidentMessage}} {% endfor %}

Variables: {% for var in variables%}
    - Id:    {{var.id}}
      Name:  {{var.name}}
      Type:  {{var.type}}
      Value: {{var.value}}
      {% endfor %}
""".strip()


@describe.command("processInstance", help="describe one process instance")
@with_output(
    TemplateOutputHandler(DESCRIBE_PROCESS_INSTANCE_TEMPLATE),
    default_json_output,
)
@click.argument("process_instance_id", nargs=1)
@click.pass_context
@with_exception_handler()
def describe_process_instance(ctx: click.Context, process_instance_id: str, **kwargs):
    client: Client = ctx.obj["client"]
    path = f"/process-instance/{process_instance_id}"
    params: Dict[str, Any] = {}
    pi_resp = client.get(path, params=params)
    pi_resp.raise_for_status()
    pi_resp_json = pi_resp.json()

    path = f"/variable-instance"
    params: Dict[str, Any] = {"processInstanceIdIn": process_instance_id}
    var_resp = client.get(path, params=params)
    var_resp_json = var_resp.json()

    return {**pi_resp_json, "variables": var_resp_json}


@describe.command(
    "historicProcessInstance", help="describe one historic process instance"
)
@with_output(
    TemplateOutputHandler(DESCRIBE_HISTORIC_PROCESS_INSTANCE_TEMPLATE),
    default_json_output,
)
@click.argument("process_instance_id", nargs=1)
@click.pass_context
def describe_historic_process_instance(
    ctx: click.Context, process_instance_id: str, **kwargs
):
    client: Client = ctx.obj["client"]
    path = f"/history/process-instance/{process_instance_id}"
    params: Dict[str, Any] = {}
    pi_resp = client.get(path, params=params)
    pi_resp_json = pi_resp.json()

    path = f"/history/variable-instance"
    params: Dict[str, Any] = {"processInstanceId": process_instance_id}
    var_resp = client.get(path, params=params)
    var_resp_json = var_resp.json()

    return {**pi_resp_json, "variables": var_resp_json}
