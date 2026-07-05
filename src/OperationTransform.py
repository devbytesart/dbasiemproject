"""
Copyright 2026 ttdantett DevBytesArt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: operation transform
"""

from OperationBase import  *
import UtilsEnum as ue
import Utils as utils
import re, json

class OperationTransform(OperationBase):
    def __init__(self):
        self.keyword = "!transform"

    def identify_operation(self, operation):
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [self.keyword + " <field1> as <format1>, <field2> as <format2>, ..."]
    
    def parse_operation(self, operation):
        # TODO improve the pattern, the case <field> as <format>,<field> as <format> is not handled well when no space between comma
        pattern = r"\s*([\w\(\)\d\,\:\-\_]+)\s+as\s+([\w\(\)\d\,\:\-\_]+)\s*,*"
        transform_match = re.findall(pattern, operation)
        if len(transform_match) > 0:
            # TODO trim on groups
            return transform_match
        else:
            raise ValueError("Invalid transform syntax")
        
    def evaluate_operation(self, data, fields):
        # TODO add error management here
        if not data:
            return []
        # Init variables
        variables = data.get("variables", {})
        for d in data["data"]:
            for field in fields:
                field_name = field[0]
                format_name = field[1]
                str_format_name = format_name.replace("(","").replace(")","").replace(":","").replace(" ","_")
                # Add new fields to 'list_fields'
                new_field = f"{field_name}_{str_format_name}"
                # Transformation des données
                # Transform data
                if field_name in d:
                    d[new_field] = self.transform(d[field_name], format_name)
                else:
                    d[new_field] = None
        # return {"type": "table", "data": data["data"],  "fields": data["fields"], "variables": variables}
        return utils.update_siem_search_result({"data": data["data"], "fields":data["fields"], "variables":variables})

    def transform(self, value, format):
        if format.startswith("substring"):
            regex = r"substring\((?:(\d+),(\d+)|:(\d+)|(\d+):)\)"
            start, end = self.parse_substring_call(format, len(value), regex)
            return value[start:end]
        else:
            raise ValueError("Invalid format")
        
    def execute_operation(self, operation: str, data: list, index:list, tenant: list, technology: list, start_time: str, end_time: str, token: str):
        fields = self.parse_operation(operation)
        return  self.evaluate_operation(data, fields)

    def all_pages(self):
        return False
    
    def parse_substring_call(self, text, string_length, regex):
        match = re.match(regex, text)
        if not match:
            return None, None  # No correspondance
        if match.group(1) and match.group(2):  # Cas "substring(0,3)"
            start = int(match.group(1))
            end = int(match.group(2))
        elif match.group(3):  # Cas "substring(:2)"
            start = 0
            end = int(match.group(3))
        elif match.group(4):  # Cas "substring(3:)"
            start = int(match.group(4))
            end = string_length
        else:
            return None, None  # No valid correspondance
        return start, end
    
    def get_required_permissions(self):
        """ Does not require any permissions """
        return []
    
    def get_help(self):
        return f"""
        <!-- Transform Section -->
        <button class="ui button collapsible">Transform Operation</button>
        <div class="ui segment collapsed-content">
            <p>The transform operation allows you to create temporary columns with transformation applied. You transform data using <code> ...| {self.keyword} field1 as transform1, field2 as transform2 </code>.</p>
            <p>New columns will be named according to the transformation.</p>
            <h3>Example:</h3>
            <pre><code class="hljs"> ...| {self.keyword} duser as substring(2,10), suser as substring(:10), auser as substring(10:)</code></pre>
        </div>
        """