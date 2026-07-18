"""
Copyright 2026 ttdantett DevBytesArt®

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
document: operation project
"""

from OperationBase import  *
import UtilsEnum as ue
import Utils as utils
import re, json

class OperationProject(OperationBase):
    def __init__(self):
        self.keyword = "!project"

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [self.keyword + " <field1>, <field2>, ..."]
    
    def parse_operation(self, operation: str):
        """Analyse an operation of type projection 'project <field1>, <field2>, ...'."""
        pattern = self.keyword + r"\s+(\w+(?:\s*,\s*\w+)*)"
        project_match = re.match(pattern, operation)
        if project_match:
            # TODO trim on groups
            return project_match.group(1).split(',')
        else:
            raise ValueError("Invalid project syntax")
        

    def evaluate_operation(self, data, fields):
        """Return the table with only the fields mentioned."""
        # TODO add error management
        if not data:
            return []
        else:
            var = {}
            if "variables" in data:
                var = data["variables"]
            data = data["data"]
            # TODO improve this part (not efficient)
            # data = self.search_data(data)
            # print("PERFORM PROJECT:" + str(data))
            results = []
            for d in data:
                # d = json.loads(d)
                dic = {}
                for field in fields:
                    if field not in d:
                        dic[field] = None
                    else:
                        dic[field] = d[field]
                # TODO change the json.dumps and json loads. In dedicated function
                # results.append(json.dumps(dic))
                results.append(dic)
            # print(results)
            # return {"type": "table", "data": results, "fields": fields, "variables": var}
            return utils.update_siem_search_result({"data":results, "fields":fields, "variables":var})
        
    def execute_operation(self, operation: str, data: list, index:list, tenant: list, technology: list, start_time: str, end_time: str, token: str):
        fields = self.parse_operation(operation)
        return  self.evaluate_operation(data, fields)

    def all_pages(self):
        return False
    
    def get_required_permissions(self):
        """ Does not require any permissions """
        return []
    
    def get_help(self):
        return f"""
        <!-- Fields Projection Section -->
        <button class="ui button collapsible">Fields Projection</button>
        <div class="ui segment collapsed-content">
            <p>Field projection keeps only the fields you specify, discarding others. This can be achieved with the <code>| {self.keyword} [field1, field2, ...]</code> command.</p>
            <h3>Example:</h3>
            <pre><code class="hljs">!search duser:administrator | {self.keyword} duser,name,externalId</code></pre>
        </div>
        """