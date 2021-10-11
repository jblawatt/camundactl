# Configuration

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
extra_template_paths:
  - /path/to/custom/templates
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
- `extra_template_paths` is a list of paths to secifiy additionals template locations for the template output
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
$ cctl config add-engine local http://localhost:8080/engine-rest --select
```

### List all engines

List all engines that are configured. The `*` indicates the currently selected engine.

```bash
$ cctl config get-engines
local *
client-a
```

### Activate engine

Activates the `client-a` engine.

```bash
$ cctl config activate-engine client-a
```

### Remove engine

Removes the `client-a` engine.

```bash
$ cctl config remove-engine client-a
```

## Logging

TODO

## Extra Paths

TODO

## Alias

You can modify config file and add alias names for subcommand.

```yaml
alias:
  pi: processInstance
  pis: processInstances
  hpi: historicProcessInstance
  hpis: historicProcessInstances
  i: incident
  is: incidents
  deploy: deployment
  desc: describe
  g: get
```

Alias are configured for your installation and become applied for all engines.

### Add alias
You can add extra alias for long commands as follows:
```bash
$ cctl config add-alias COMMAND ALIAS
```

### Remove alias
To remove a alias you can use the following command:
```bash
$ cctl config remove-alias ALIAS
```

### Remove alias
To see which alias are configured
```bash
$ cctl config get-alias
Alias    Command
-------  ----------------
pi       processInstance
pis      processInstances
```

## Templates

The output handler `template` provides the functionality to render the returned
output to a given template. The result and some other variables are provided in
the template context.

Details about the template output handler can be found in the separate
[documentation](output.md).

The option `extra_template_paths` gives you the option to extend the loader
context and provide custom templates.

Templates are searched in the following order:

- Defaults provided by dictionary (`default`, `result-length`)
- `confg.extra_template_paths`
- `$CONFIG_DIR/templates`

