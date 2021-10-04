# Examples

## Filter result

Load two active process instances and use only the columns id and suspended

```zsh
$ cctl get processInstances --max-results 2 -o table -oH id,suspended
id                                    suspended
------------------------------------  -----------
0027da48-0a61-11ec-bd5f-0242ac120014  False
003248e7-0b05-11ec-990f-0242ac12000d  False
```

## Use template for output

Load all active process instances and use the result in a jinja2 template.

```bash
$  cctl get processInstances -o template -oT '{{result|length}}'
1337
```

## Apply jsonpath to result

Load five active process instances and apply jsonpath formatting.

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
