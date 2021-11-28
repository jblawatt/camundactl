        _   _
  __ __| |_| |
 / _/ _|  _| |
 \__\__|\__|_|

cctl -- Camunda Control
~~~~~~~~~~~~~~~~~~~~~~~

Version:        ---
Git:            ---
Current Engine: {{config.current_engine}}
Config-File:    {{config_file}}

OpenAPI:{% for openapi in openapi_specs %}
    - Version:     {{openapi.info.version}}{% endfor %}

Engines: {% if config.engines %}{% for engine in config.engines %}
    - Name: {{engine.name}} {% if engine.name == config.current_engine %}(selected){% endif %}
      URL: {{engine.url}}
      Version: {{ camunda_engine_version(engine) }}{% endfor %}{% else %}-{% endif %}

Alias: {% if config.alias %}{% for key, value in config.alias.items() %}
    - {{key}}: {{value}}{% endfor %}{% else %}-{% endif %}

Extra Paths: {%if config.extra_path %}{% for ep in config.extra_paths %}
    - {{ep}} {% endfor %}{% else %}-{% endif %}

Templates: {%if config.extra_path %}{% for ep in config.extra_paths %}
    - {{ep}} {% endfor %}{% else %}-{% endif %}
