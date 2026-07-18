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
document: operation order
"""

from OperationBase import *
from collections import defaultdict
import UtilsEnum as ue
import Utils as utils
import json, threading, time

class OperationOrder(OperationBase):
    def __init__(self, max_threads=16):
        self.lock = threading.Lock()  # Use to protect access to shared dictionary
        self.global_count_dict = defaultdict(int)  # Dictionary shared between threads
        self.max_threads = max_threads
        self.keyword = "!order"
        self.order = "asc"

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [ self.keyword + " by <field> " + self.order]

    def parse_operation(self, operation: str):
        """ Order statistic operation of type 'order by <field> [asc|desc]'. """
        # Regex captures fields in group 1, and order (optional) in group 2
        count_match = re.match(
            self.keyword + r"\s+by\s+(\w+(?:\s*,\s*\w+)*)(?:\s+(asc|desc))?$", 
            operation.strip(), 
            re.IGNORECASE # Match 'desc', 'DESC', 'Asc' and so on
        )
        if count_match:
            fields = [f.strip() for f in count_match.group(1).split(',')]
            direction = count_match.group(2) if count_match.group(2) else self.order
            return {
                "fields": fields,
                "direction": direction.lower()
            }
        else:
            raise ValueError("Invalid stats syntax")

    def _count_records(self, sub_data, fields):
        """Count occurences specified fields for a sublist of data."""
        local_count_dict = defaultdict(int)
        for record in sub_data:
            key = tuple(record.get(field, None) for field in fields)  # Generate key
            local_count_dict[key] += 1
        # Add local account to global dictionary
        with self.lock:
            for key, count in local_count_dict.items():
                self.global_count_dict[key] += count


    def evaluate_operation(self, data, parsed_op):
        """Execute only the sorting operation on existing data."""
        if not data:
            return []
        else:
            var = {}
            if "variables" in data:
                var = data["variables"]
            data = data["data"]
        # If there is no data to sort, return early
        if not data:
            return utils.update_siem_search_result({"data": [], "variables": var})
        # Extract fields and direction from the parsed operation
        fields = parsed_op["fields"]
        direction = parsed_op["direction"]
        reverse_sort = True if direction == "desc" else False
        # Define the key to sort by (the first field specified in the command)
        sort_key = fields[0]
        start_ordering = time.time()
        # Sort the data dynamically based on the key (works for both strings and numbers like 'count')
        if sort_key in data[0]:
            results = sorted(data, key=lambda x: x[sort_key], reverse=reverse_sort)
        else:
            # Fallback if the field doesn't exist in the data records
            results = data
        print("Ordering execution time: ", time.time() - start_ordering)
        return utils.update_siem_search_result({"data": results, "variables": var})

    def execute_operation(self, operation: str, data: list, index: list, tenant: list, technology: list, start_time: str, end_time: str, token: str):
        fields = self.parse_operation(operation)
        return self.evaluate_operation(data, fields)
    
    def all_pages(self):
        return False
    
    def get_required_permissions(self):
        """ Does not require any permissions """
        return []
    
    def get_help(self):
        return f"""
        <button class="ui button collapsible">Order values</button>
        <div class="ui segment collapsed-content">
            <p>The order operation allows you to sort values by fields <code>| {self.keyword} by [field1, field2, ...] [asc|desc]</code>.</p>
            <h3>Examples:</h3>
            <pre><code class="hljs">!search duser:administrator | {self.keyword} by duser,name desc</code></pre>
            <pre><code class="hljs">!search duser:administrator | {self.keyword} by count asc</code></pre>
        </div>
        """