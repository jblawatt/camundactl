# Usage

[TOC]

## `get` Resource Information

Get commands provides the ability to request ressource information from a given engine. It contains all OpenAPI Operations of the Verb `get`.

## `delete` Resource Information

Delete commands provide the ability to delete specific ressources in the camunda engine.

## `apply` Resource Information

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

## `describe` Resource Information

_not quite implemented_. It's planned to use this commands to collect and output complex informationations about a given ressoure including combining multiple endpoints (e.g. process instances with all occured incidents and variable information.)


## Autocomplete

`cctl` uses [click](https://click.palletsprojects.com/) which brings a buildin
autocomplte feature. Have a look at their [shell completion documentation](https://click.palletsprojects.com/en/8.0.x/shell-completion/).

*`zsh` Example*
```bash
\_CCTL_COMPLETE=zsh_source cctl
```
## Others
### Info
### Version
