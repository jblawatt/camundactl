# Camunda Control (cctl)

Camunda Contorl (`cctl`) is a command line interface to the camunda REST API.
It is heavily inspired by `kubectl`.

``` bash
$ cctl [command] [resource] [args] [flags]
```

where `command`, `operation/resource`, `args` and `flags` are:

* `command`: Specifies the operation you want to perform on a resource. For
example: `get`, `delete`, `apply` or `describe`.

* `resource`: Desribes the resource you want to apply the operation on. For
example: `processInstance`, `variableInstance`, `deployment`, ...

* `args`: Arguments to specify the exact resource. For example:
`processInstanceId`, `variableInstanceId`, ...

* `flags`: Extra arguments to be send to the REST API or specifing the output.


## Examples

```shell
$ cctl get processInstances --max-results 2 -o table -oH id,suspended
id                                    suspended
------------------------------------  -----------
0027da48-0a61-11ec-bd5f-0242ac120014  False
003248e7-0b05-11ec-990f-0242ac12000d  False
```
