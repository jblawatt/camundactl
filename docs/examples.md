# Examples


## Get all active process instances

The easiest way to get all active process instances is to use the following
command:

```shell
$ cctl get processInstances
```

## Get all active process instances of a specific process definition

To filter the result, each command provides all REST API filter options for the
command line. So you can specify the `processDefintionId` to search for.

```shell
$ cctl get processInstances --process-definition-id f87b25ce-0577-11ec-8801-0242ac12000a
```

## Limit resultset

Sometimes `get` prints to much information for a single result. Per default all
keys of the server json become printed. If you would like limt the output you
can use `-o table` ensuring table output, combinted with the
`-oT/--output-headers` option and provide the columns.

Beside that, most endpoints provide a `--max-limit` and `--first-result` option
to paginate or limit the result set.

```shell
$ cctl get processInstances --max-results 2 -o table -oH id,suspended
id                                    suspended
------------------------------------  -----------
0027da48-0a61-11ec-bd5f-0242ac120014  False
003248e7-0b05-11ec-990f-0242ac12000d  False
```

## Use template output to print result count

The `--ouput/-o template` option gives you the option to provide a output Template (jinja2)
which gets the resultset as context variable. All [jinja2 builtins](https://jinja.palletsprojects.com/en/3.0.x/templates/)
can be used.

Here we just output the result length.

```bash
$  cctl get processInstances -o template -oT '{{result|length}}'
1337
```

## Get processInstanceIds only with jsonpath

Sometime you just need the processInstanceId i.e. to pipe it into another
command. The can be reached with a `-o/--ouput jsonpath` option and providing
a jsonpath query which will be applied on the resultset. (For jsonpath whe
utilize [jsonpath-ng](https://github.com/h2non/jsonpath-ng) under the hood.)

```bash
$ cctl get processInstances -o jsonpath -oJ '$.[*].id' --max-results 5
0027da48-0a61-11ec-bd5f-0242ac120014
003248e7-0b05-11ec-990f-0242ac12000d
005ec7db-0a6c-11ec-bd5f-0242ac120014
00957ceb-0b18-11ec-990f-0242ac12000d
00f522c0-0b10-11ec-990f-0242ac12000d
```

## Limited JSON output

Load only one active process instance and ouput as json.

```bash
$ cctl get processInstances -o json --max-results 1
```

```json
[
  {
    "links": [],
    "id": "0027da48-0a61-11ec-bd5f-0242ac120014",
    "definitionId": "f87b25ce-0577-11ec-8801-0242ac12000a",
    "businessKey": null,
    "caseInstanceId": null,
    "ended": false,
    "suspended": false,
    "tenantId": null
  }
]
```

## Piping commands

Pipe commands together. Get all active process instances by process defintion and delete them:

```bash
$ cctl get processInstances --process-definition-id f87b25ce-0577-11ec-8801-0242ac12000a -o jsonpath -oJ "$.[*].id" | xargs -n 1 cctl delete processInstance -o template -oT "Ok"
Ok
Ok
Ok
...
```
