

<p align="center">
  <img src="images/Camunda_Logo_Black.png" alt="Camunda Logo" width="300px">
</p>
<p align="center">
    <em>
        this is a community project and not owned by camunda!!
    </em>
</p>
<p align="center">
    <img src="https://github.com/jblawatt/camundactl/actions/workflows/unittests.yml/badge.svg" alt="Test">
</a>
    <img src="https://img.shields.io/pypi/v/camundactl?color=%2334D058&label=pypi%20package)" alt="Package">
</a>
</p>

<hr />


# Camunda Control (cctl)


_Camunda Control_ (`cctl`) is a command line interface to the camunda REST API.

The majority of the direct camunda commands are generated from the `openapi.json`
file provided by the camunda project. For more details have a look a their [documentation](https://docs.camunda.org/manual/7.15/reference/rest/openapi/).

## What it does

```bash
$ cctl [command] [resource] [args] [flags]
```

where `command`, `operation/resource`, `args` and `flags` are:

- `command`: Specifies the operation you want to perform on a resource. For
  example: `get`, `delete`, `apply` or `describe`.

- `resource`: Desribes the resource you want to apply the operation on. For
  example: `processInstance`, `variableInstance`, `deployment`, ...

- `args`: Arguments to specify the exact resource. For example:
  `processInstanceId`, `variableInstanceId`, ...

- `flags`: Extra arguments to be send to the REST API or specifing the output.

## Install

Camunda Control can be installed via pip:

```bash
$ pip install camuncactl [--user]
```

## Examples

**List all process instances:**

```shell
$ cctl get processInstances
id                                    suspended
------------------------------------  -----------
0027da48-0a61-11ec-bd5f-0242ac120014  False
003248e7-0b05-11ec-990f-0242ac12000d  False
...
```

**Load all active process isntances and use the result in a jinja2 template**

```bash
$  cctl get processInstances -o template -oT '{{result|length}}'
1337
```

More [Examples](examples.md)

