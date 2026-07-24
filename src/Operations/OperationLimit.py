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
document: operation limit
"""

from OperationBase import  *
import UtilsEnum as ue
import Utils as utils
import re, json

class OperationLimit(OperationBase):
    def __init__(self):
        self.keyword = "!limit"

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [self.keyword + " <number>"]
    
    def parse_operation(self, operation: str):
        """Analyse an operation of type limit 'limit <number>'."""
        pattern = self.keyword + r"\s+(\d+)"
        print("OPERATION LIMIT")
        print(str(pattern))
        limit_match = re.match(pattern, operation)
        if limit_match:
            return limit_match.group(1)
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
            f = data["fields"]
            data = data["data"]
            results = []
            print(str(fields))
            for i in range(int(fields)):
                results.append(data[i])
            return utils.update_siem_search_result({"data":results, "fields":f, "variables":var})
        
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
        <!-- Fields Limit Section -->
        <button class="ui button collapsible">Event Limit</button>
        <div class="ui segment collapsed-content">
            <p>Event Limit keeps only the number of event you specify, discarding others. This can be achieved with the <code>| {self.keyword} \<number\> </code> command.</p>
            <h3>Example:</h3>
            <pre><code class="hljs">!search duser:administrator | !counts by duser | !order by counts | {self.keyword} 3 </code></pre>
        </div>
        """