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
document: operation variable
"""

from src.Operations.OperationBase import *
import UtilsEnum as ue
import Utils as utils
# from OperationAdvancedCondition import *
import re, json, traceback

class OperationVariable(OperationBase):
    def __init__(self, indexers, max_threads=10):
        self.keyword = "!var"
        self.max_threads = max_threads
        self.indexers = indexers
        # self.advanced_condition = OperationAdvancedCondition(self.indexers, self.max_threads)

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [self.keyword + " <name> = <value>", self.keyword + " <name> = <condition>"]

    def parse_operation(self, operation: str):
        """Analyse an expression of variable 'var <name> = <value>'."""
        # TODO if it is working
        var_match = re.match(self.keyword + r"\s+([\-\w]+)\s*=\s*(.+)", operation)
        if var_match:
            var_name = var_match.group(1).strip()
            var_value = var_match.group(2).strip()
            return var_name, var_value
        else:
            raise ValueError("Invalid variable assignment syntax")
        
    def evaluate_operation(self, data, name, value):
        """Evaluate the value of the variable and return it"""
        # TODO test if it is ok
        # TODO change the json.dumps and json loads. In dedicated function
        pass

    def execute_operation(self, operation: str, data: list, index:list, tenant: list, technology: list, start_time: str, end_time: str, token: str):
        try:
            print("In operation variable: ", operation, "technology: ", str(technology))
            var_name, var_query = self.parse_operation(operation)
            if data is None:
                # data = {"type": "table", "data": [], "fields": [], "variables": {}}
                data = ue.SIEM_SEARCH_FORMAT.result.value
            if "variables" not in data:
                data["variables"] = {}
            # TODO migate this part in the evaluate operation
            # results = self.advanced_condition.execute_operation(var_query, [], index, tenant, start_time, end_time)
            results = self.indexers.interpretRequest(var_query, index, tenant, technology, start_time, end_time, token,  ";", var_name)
            data["variables"][var_name] = results
            return data
        except Exception:
            print(f"Error in operation variable: {traceback.format_exc()}")
            data["errors"].append(f"Error during variable operation: {operation}")
            return data

    def all_pages(self):
        return False
    
    def get_required_permissions(self):
        """ Does not require any permissions """
        return []
    
    def get_help(self):
        return f"""
        <!-- Store Variables Section -->
        <button class="ui button collapsible">Store Variables</button>
        <div class="ui segment collapsed-content">
            <p>The variable operation allows you to store results of advanced researches in variables.  You can store variable using <code>| {self.keyword} [name] = [advanced condition]</code>.</p>
            <h3>Example:</h3>
            <pre><code class="hljs">{self.keyword} firstvar = duser:administrator</code></pre>
        </div>
        """