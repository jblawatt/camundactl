# Configuration

[TOC]


`cctl` uses a config file. The locations differ from os. If the configuration file does not it exists, it becomes created.

- MacOS: `$HOME/Libarary/Application Support/camundactl/config.yml`
- Linux: `$HOME/.config/camundactl/config.yml`
- Windows: `$HOME/Appdata/Local/camundactl/config.yml`

## Fileformat

The configuration is stored in a yaml file.

```yaml
version: beta1
extra_paths:
  - module.to.my.plugin
current_engine: localhost
log_level: DEBUG
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
- `extra_paths` is a list of python modules that can be autodiscovered in command discovering to add user defined commands or plugins
- `current_engine` is the currently selected engine to be used
- `log_level` defines the level for application logging.
- `engine` contains a list of engines within you can switch witch `cctl config engines activate ANOTHER`.
  - `name` the engines display name
  - `url` the urls of the camunda engine rest api
  - `auth` is an object of `user` and `password` for basic authentication
  - `verify` is a boolen that ignores ssl verification (default `true`)


## Engines

### Add engine

Add a camunda engine to the list of engines and directly select it.

```bash
$ cctl config engines add local http://localhost:8080/engine-rest --select
```

### List all engines

List all engines that are configured. The `*` indicates the currently selected engine.

```bash
$ cctl config engines ls
local *
client-a
```

### Activate engine

Activates the `client-a` engine.

```bash
$ cctl config engines activate client-a
```

### Remove engine

Removes the `client-a` engine.

```bash
$ cctl config engines remove client-a
```

## Logging

TODO

## Extra Paths

TODO
