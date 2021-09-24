# camundactl

camundactl (`cctl`) is a command line interface (cli) that interacts with the camunda rest api. It provides commands for all endpoints with the ability to filtes and different output format. The cli usaged is heavily inspired by [kubecl](https://kubernetes.io/) to work with kubernetes.

**Features**

- request all endpoints, defined in the camunda openapi.json
- generate `get`, `delete` and `apply` commands from openapi.json
- dedicated implementations for `describe`
- multiple output formats: `table`, `json`, `jsonpath`, `template` (jinja2)
- shell autocomplete for `zsh`, `bash`, `fish`)
- shell autocomplete for processInstanceId, incidentIds, aso.
- configuration for multipe camunda engines
- ...

**Contents**

- [Examples](#examples)
- [Installation](#installation)
- [Configuration](#usage/configuration)
  - [Format](#usage/configuration)
  - [Add/Select/List/Remove Engine](#usage/configuration)
  - [Autocomplete](#usage/configuration)
- [Usage](#usage/configuration)
  - [Global Options](#usage/configuration)
  - [`get` Command](#usage/configuration)
  - [`describe` Command](#usage/configuration)
  - [`delete` Command](#usage/configuration)
  - [`apply` Command](#usage/configuration)
  - [`config` Command](#usage/configuration)
  - [`output` Option](#usage/configuration)

## Examples

Load two active process instances and use only the columns id and suspended

```shell
$ cctl get processInstances --max-results 2 -o table -oH id,suspended
id                                    suspended
------------------------------------  -----------
0027da48-0a61-11ec-bd5f-0242ac120014  False
003248e7-0b05-11ec-990f-0242ac12000d  False
```

Load all active process instances and use the result in a jinja2 template.

```bash
$  cctl get processInstances -o template -oT '{{result|length}}'
1337
```

Load five active process instances and apply jsonpath formatting.

```bash
$ cctl get processInstances -o jsonpath -oJ '$.[*].id' --max-results 5
0027da48-0a61-11ec-bd5f-0242ac120014
003248e7-0b05-11ec-990f-0242ac12000d
005ec7db-0a6c-11ec-bd5f-0242ac120014
00957ceb-0b18-11ec-990f-0242ac12000d
00f522c0-0b10-11ec-990f-0242ac12000d
```

Load only one active process instance and ouput as json.

```bash
$ cctl get processInstances -o json --max-results 1
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

Pipe commands together. Get all active process instances by process defintion and delete them:

```bash
$ cctl get processInstances --process-definition-id f87b25ce-0577-11ec-8801-0242ac12000a -o jsonpath -oJ "$.[*].id" | xargs -n 1 cctl delete processInstance -o template -oT "Ok"
Ok
Ok
Ok
...
```

## Installation

camundactl can be installed via pip.

```bash
$ pip install camundactl
```

## Configuration

camundactl uses a config file. The locations differ from os. If the configuration file does not it exists, it becomes created.

- MacOS: `$HOME/Libarary/Application Support/camundactl/config.yml`
- Linux: `$HOME/.config/camundactl/config.yml`
- Windows: `$HOME/Appdata/Local/camundactl/config.yml`

### Format

```yaml
version: beta1
extra_paths:
  - module.to.my.plugin
current_engine: localhost
engines:
  - name: localhost
    url: http://localhost:8080/engine-rest
    auth:
      user: camunda
      password: camunda
  - name: client-a
    url: http://localhost:8080/engine-rest
    auth:
      user: camunda
      password: camunda
  - name: client-c
    url: https://localhost:8080/engine-rest
    verify: false
    auth:
      user: camunda
      password: camunda
```

- `version` defines the current config file version for later update purpose
- `extra_path` is a list of python modules that can be autodiscovered in command discovering to add user defined commands or plugins
- `current_engine` is the currently selected engine to be used
- `engine` contains a list of engines within you can switch witch `cctl config engines activate ANOTHER`.
  - `name` the engines display name
  - `url` the urls of the camunda engine rest api
  - `auth` is an object of `user` and `password` for basic authentication
  - `verify` is a boolen that ignores ssl verification (default `true`)

### Add/List/Activate/Remove Engines

**Add an engine**

Add a camunda engine to the list of engines and directly select it.

```bash
$ cctl config engines add local http://localhost:8080/engine-rest --select
```

**List all engines**

List all engines that are configured. The `*` indicates the currently selected engine.

```bash
$ cctl config engines ls
local *
client-a
```

**Activate an engine**

Activates the `client-a` engine.

```bash
$ cctl config engines activate client-a
```

**Remove an engine**

Removes the `client-a` engine.

```bash
$ cctl config engines remove client-a
```

### Autocomplete

camundactl provides the functionality to autocomplete at the console.

camundactl bases on [click](http://click.parallelprojects.com/), which
autocomplete method could be used.

**Example for zsh**

```bash
$ _CCTL_COMPLETE=zsh_source cctl > $HOME/.cctl-completion.sh
```

You can find more Details on the project-page: https://click.palletsprojects.com/en/8.0.x/shell-completion/

## Usage

### Gloabl options

--help
--log
-e, --engine

### `get` Resource Information

Get commands provides the ability to request ressource information from a given engine. It contains all OpenAPI Operations of the Verb `get`.

### `delete` Resource Information

Delete commands provide the ability to delete specific ressources in the camunda engine.

### `apply` Resource Information

Apply commands provide the ability to apply changes to the camunda engine. They combine the functionality of `put` and `post` verbs and these operations.

As `kubectl` you can use `apply` in combination with files that contains the payload.

You can use JSON or YAML payloads.

```bash
$ cat EOF>>
value: hello-world
type: String
EOF >> variable.yaml

$ cctl apply processInstanceVariable foobar 0027da48-0a61-11ec-bd5f-0242ac120014 -y variable.yml
```

**Schema validation**
If provided, the given payload becomes validated against the openapi schema. The openapi documentation sometimes does not fully match the api. (e.g. while updating variables. The values is describes as `object` but values of primitive variables are also allowed.)

To skip this use the option `--skip-validation`.

### `describe` Resource Information

_not quite implemented_. It's planned to use this commands to collect and output complex informationations about a given ressoure including combining multiple endpoints (e.g. process instances with all occured incidents and variable information.)

### `output` Option

The `-o/--output` option defines the output format. The default ist `table`. All other options are described in the following.

#### Table Output

The camunda responses are nearly all of type `application/json`. If the response is of type `array` a table will be printed. If it's an `object` a table with `key` and `value` headers are used.

**Options**

- `-o table`
- `-oH`, `--output-headers` gives the possibility to select the columns to show
- `-oCL`, `--output-cell-length` cell values of type string are limited to `40` characters.

_Example_

```bash
$ cctl get processInstances -o table -oH id,suspended
```

#### JSON Output

Prints the json API response with end indent of 2.

**Options**

- `-o json`

#### JSON-Path Output

`-o jsonpath` activates a jsonpath output. With `-oJ` you can apply the jsonpath filter which will be applied. 
For this [jsonpath-ng](https://pypi.org/project/jsonpath-ng/) is used. There you can find further information about the filter format.

#### Template Output



#### Raw Output

### root command

```bash

$ python -m camundactl --help

Usage: __main__.py [OPTIONS] COMMAND [ARGS]...

Options:
  -l, --log-level TEXT  activates the logger with the given level
  -e, --engine TEXT     define the engine name to be used
  --help                Show this message and exit.

Commands:
  delete
  describe
  get

```

### delete command

```bash

$ python -m camundactl delete --help

Usage: __main__.py delete [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  attachment                      Removes an attachment from a task by...
  deployment                      Deletes a deployment by id.
  processDefinition               Deletes a running process instance by...
  processDefinitionsByKey         Deletes process definitions by a given...
  processDefinitionsByKeyAndTenantId
                                  Deletes process definitions by a given...
  processInstance                 Deletes a running process instance by...
  processInstanceVariable         Deletes a variable of a process...
  task                            Removes a task by id.
  taskLocalVariable               Removes a local variable from a task...
  taskVariable                    Removes a variable that is visible to...


```

### get command

```bash

$ python -m camundactl get --help

Usage: __main__.py get [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  activityInstanceTree            Retrieves an Activity...
  activityStatistics              Retrieves runtime...
  activityStatisticsByProcessDefinitionKey
                                  Retrieves runtime...
  activityStatisticsByProcessDefinitionKeyAndTenantId
                                  Retrieves runtime...
  attachment                      Retrieves a task...
  attachmentData                  Retrieves the binary...
  attachments                     Gets the attachments...
  comment                         Retrieves a task...
  comments                        Gets the comments for...
  deployedForm                    Retrieves the...
  deployedStartForm               Retrieves the...
  deployedStartFormByKey          Retrieves the...
  deployedStartFormByKeyAndTenantId
                                  Retrieves the...
  deployment                      Retrieves a...
  deploymentResource              Retrieves a...
  deploymentResourceData          Retrieves the binary...
  deploymentResources             Retrieves all...
  deploymentsCount                Queries for the...
  eventSubscriptions              Queries for event...
  eventSubscriptionsCount         Queries for the...
  externalTask                    Retrieves an external...
  externalTaskErrorDetails        Retrieves the error...
  externalTasks                   Queries for the...
  externalTasksCount              Queries for the...
  form                            Retrieves the form...
  formVariables                   Retrieves the form...
  identityLinks                   Gets the identity...
  interval                        Retrieves a list of...
  latestProcessDefinitionByTenantId
                                  Retrieves the latest...
  metrics                         Retrieves the `sum`...
  processDefinition               Retrieves a process...
  processDefinitionBpmn20Xml      Retrieves the BPMN...
  processDefinitionBpmn20XmlByKey
                                  Retrieves latest...
  processDefinitionBpmn20XmlByKeyAndTenantId
                                  Retrieves latest...
  processDefinitionByKey          Retrieves the latest...
  processDefinitionDiagram        Retrieves the diagram...
  processDefinitionDiagramByKey   Retrieves the diagram...
  processDefinitionDiagramByKeyAndTenantId
                                  Retrieves the diagram...
  processDefinitionStatistics     Retrieves runtime...
  processDefinitions              Queries for process...
  processDefinitionsCount         Requests the number...
  processEngineNames              Retrieves the names...
  processInstance                 lists all active...
  processInstanceVariable         Retrieves a variable...
  processInstanceVariableBinary   Retrieves the content...
  processInstanceVariables        Retrieves all...
  processInstances                Queries for process...
  processInstancesCount           Queries for the...
  renderedForm                    Retrieves the...
  renderedStartForm               Retrieves the...
  renderedStartFormByKey          Retrieves the...
  renderedStartFormByKeyAndTenantId
                                  Retrieves the...
  restAPIVersion                  Retrieves the version...
  schemaLog                       Queries for schema...
  startForm                       Retrieves the key of...
  startFormByKey                  Retrieves the key of...
  startFormByKeyAndTenantId       Retrieves the key of...
  startFormVariables              Retrieves the start...
  startFormVariablesByKey         Retrieves the start...
  startFormVariablesByKeyAndTenantId
                                  Retrieves the start...
  task                            Retrieves a task by...
  taskLocalVariable               Retrieves a variable...
  taskLocalVariableBinary         Retrieves a binary...
  taskLocalVariables              Retrieves all...
  taskVariable                    Retrieves a variable...
  taskVariableBinary              Retrieves a binary...
  taskVariables                   Retrieves all...
  tasks                           Queries for tasks...
  tasksCount                      Retrieves the number...
  topicNames                      Queries for distinct...


```

## autocomplete

\_CCTL_COMPLETE=zsh_source cctl

# TODO / Ideas

- output column length in options or parameter (currently hard 40)

- display

  - list of strings
  - list of objects
  - object with keys
  - object with one value

- use template loader to save and load templates somewhere and let use use them or save some for default
- templates with more context variables. not just "result"
