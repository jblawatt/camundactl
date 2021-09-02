from camundactl.output.json import JSONOutputHandler
from camundactl.output.jsonpath import JSONPathOutputHandler
from camundactl.output.raw import RawOutputHandler
from camundactl.output.table import ObjectTableOutputHandler, TableOutputHandler
from camundactl.output.template import TemplateOutputHandler

default_table_output = TableOutputHandler(table_headers_backlist=["links"])
default_object_table_output = ObjectTableOutputHandler()
default_json_output = JSONOutputHandler()
default_jsonpath_output = JSONPathOutputHandler()
default_template_output = TemplateOutputHandler()
default_raw_output = RawOutputHandler()
