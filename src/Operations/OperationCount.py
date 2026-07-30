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
document: operation count
"""

from OperationBase import *
from collections import defaultdict
import UtilsEnum as ue
import Utils as utils
import json, threading, time

class OperationCount(OperationBase):
    def __init__(self, max_threads=16):
        self.lock = threading.Lock()  # Use to protect access to shared dictionary
        self.global_count_dict = defaultdict(int)  # Dictionary shared between threads
        self.max_threads = max_threads
        self.keyword = "!counts"
        self.sort_by = "count"

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        # return [ self.keyword + " by <field>"]
        return [{
            "name": self.keyword,
            "description": "Count events and aggregations based on events counts",
            "params": [
                {
                    "name": "fields", 
                    "type": "string", 
                    "description": "Name of fields splitted by ',', required data and search request before using it", 
                    "default": ""
                 }
            ],
            "examples": [
                "!search * | !counts by field", 
                "!search name:test | !counts by status,name,id | !render ... ",
                "!search <conditions> | !project .... | !counts by ..."
            ]
        }]

    def parse_operation(self, operation: str):
        """ Analyse statistic operation of type 'stats count by <field>'. """
        count_match = re.match(self.keyword + r"\s+by\s+(\w+(?:\s*,\s*\w+)*)", operation)
        if count_match:
            return count_match.group(1).split(',')
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

    def evaluate_operation(self, data, fields):
        """Execute operation of count on data using threads. """
        # TODO add error management here
        if not data:
            return []
        else:
            var = {}
            if "variables" in data:
                var = data["variables"]
            data = data["data"]
        # Number of threads to use (can be added according the size of data)
        num_threads = min(max(4, len(data)),self.max_threads)  # For exemple, choose 4 threads or less
        chunk_size = len(data) // num_threads  # Size of each subset
        threads = []
        print("num_threads", num_threads)
        print("chunk_size", chunk_size)
        # Divide data in subset and create a thread foreach subset
        self.global_count_dict = defaultdict(int)
        start_threads_count = time.time()
        for i in range(num_threads):
            start_index = i * chunk_size
            end_index = len(data) if i == num_threads - 1 else (i + 1) * chunk_size
            sub_data = data[start_index:end_index]
            thread = threading.Thread(target=self._count_records, args=(sub_data, fields))
            threads.append(thread)
            thread.start()  # Start the thread
        # Wait all threads ends
        for thread in threads:
            thread.join()
        print("Count in threads: ", time.time() - start_threads_count)
        # Convert global results in list of dictionaries with fields and "count"
        start_ordering = time.time()
        # results = [json.dumps({**dict(zip(fields, key)), 'count': count}) for key, count in self.global_count_dict.items()]
        results = [{**dict(zip(fields, key)), 'count': count} for key, count in self.global_count_dict.items()]
        print("Ordering in threads: ", time.time() - start_ordering)
        # Sort result by count
        if self.sort_by == "count":
            # results = sorted(results, key=lambda x: json.loads(x)[self.sort_by], reverse=True)
            results = sorted(results, key=lambda x: x[self.sort_by], reverse=True)
        # TODO manage others case sort
        # return {"type":"table", "data": results, "fields": fields + ['count']}
        # Variables
        # return {"type":"table", "data": results, "fields": [], "variables": var}
        return utils.update_siem_search_result({"data":results, "variables":var, "sort_field": self.sort_by, "sorted_by": "desc"})
    
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
        <!-- Count Values Section -->
        <button class="ui button collapsible">Count Values</button>
        <div class="ui segment collapsed-content">
            <p>The count operation allows you to count distinct values per field. You can count multiple fields simultaneously using <code>| {self.keyword} by [field1, field2, ...]</code>.</p>
            <h3>Example:</h3>
            <pre><code class="hljs">!search duser:administrator | {self.keyword} by duser,name</code></pre>
        </div>
        """