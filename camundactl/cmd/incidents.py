from typing import Any, Dict

import click

from camundactl.client import Client
from camundactl.cmd.base import describe, get
from camundactl.cmd.helpers import with_output_factory, with_query_option_factory

GET_DEFAULT_TABLE_HEADERS = {
    "Id": "id",
    "Message": "incidentMessage",
    "Timestamp": "incidentTimestamp",
    "Annotation": "annotation",
    "Activity Id": "activityId",
    "Process Instance Id": "processInstanceId",
}


INCIDENT_FILTER_PARAMS = [
    (
        "processDefinitionId",
        "The id of the process definition this incident is associated with.",
    ),
    (
        "processInstanceId",
        "The key of the process definition this incident is associated with.",
    ),
    (
        "executionId",
        "The id of the execution this incident is associated with.",
    ),
    (
        "incidentTimestamp",
        "The time this incident happened. Default format* yyyy-MM-dd'T'HH:mm:ss.SSSZ.",
    ),
    (
        "incidentType",
        "The type of incident, for example: failedJobs will be returned in case of an incident which identified a failed job during the execution of a process instance. See the User Guide for a list of incident types.",
    ),
    (
        "activityId",
        "The id of the activity this incident is associated with.",
    ),
    (
        "failedActivityId",
        "The id of the activity on which the last exception occurred.",
    ),
    (
        "causeIncidentId",
        "The id of the associated cause incident which has been triggered.",
    ),
    (
        "rootCauseIncidentId",
        "The id of the associated root cause incident which has been triggered.",
    ),
    (
        "configuration",
        "The payload of this incident.",
    ),
    (
        "tenantId",
        "The id of the tenant this incident is associated with.",
    ),
    (
        "incidentMessage",
        "The message of this incident.",
    ),
    (
        "jobDefinitionId",
        "The job definition id the incident is associated with.",
    ),
    (
        "annotation",
        "The annotation set to the incident.",
    ),
]


@get.command("incidents")
@with_output_factory(default_table_headers=GET_DEFAULT_TABLE_HEADERS)
@with_query_option_factory(
    options=INCIDENT_FILTER_PARAMS,
    name="params",
)
@click.pass_context
def get_incidents(ctx: click.Context, params: Dict):
    client: Client = ctx.obj["client"]
    path = "/incident"
    resp = client.get(path, params=params)
    return resp.json()


DESCRIBE_DEFAULT_TEMPLATE = """
Incident:

Id: {id}
""".strip()


@describe.command("incidents")
@with_output_factory(default_template=DESCRIBE_DEFAULT_TEMPLATE, default="template")
@click.argument("incident_id", nargs=1)
@click.pass_context
def describe_incident(ctx: click.Context, incident_id: str):
    client: Client = ctx.obj["client"]
    path = f"/incident/{incident_id}"
    params: Dict[str, Any] = {}
    resp = client.get(path, params=params)
    return resp.json()
