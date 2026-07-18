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
document: operation render
"""

from OperationBase import *
import UtilsEnum as ue
import Utils as utils
import re, json

class OperationRender(OperationBase):
    def __init__(self):
        self.keyword = "!render"

    def identify_operation(self, operation: str) -> bool:
        if operation.startswith(self.keyword):
            return True
        return False
    
    def get_suggestions(self):
        return [ self.keyword + " <type> by <field> over <count>"]
    
    def parse_operation(self, operation: str):
        """Analyse an expression of graph rendering 'render graph <type>'."""
        render_match = re.match(self.keyword + r"\s+(\w+)\s+by\s+(\w+(?:\s*,\s*\w+)*)\s+over\s(\w+(?:\s*,\s*\w+)*)", operation)
        if render_match:
            return render_match.group(1), render_match.group(2).split(","), render_match.group(3).split(",")
        else:
            raise ValueError("Invalid render syntax")
        
    def evaluate_operation(self, data, graph_type, fields, values):    
        """Render the graph depending on the type of graph"""
        #TODO change this part to transform data in right format
        #TODO add error management
        if not data:
            return []
        else:
            var = {}
            if "variables" in data:
                var = data["variables"]
            data = data["data"]
        results = []
        for d in data:
            # d = json.loads(d)
            dic = {}
            for field in fields:
                if field not in d:
                    dic[field] = None
                else:
                    dic[field] = d[field]
                    for value in values:
                        if value not in d:
                            dic[value] = None
                        else:
                            dic[value] = d[value]
            # TODO change the json.dumps and json loads. In dedicated function
            # results.append(json.dumps(dic))
            results.append(dic)
            # TODO to complete
            # TODO change the json.dumps and json loads. In dedicated function
        # Fields 
        t = "bar"
        if graph_type.lower() == "linechart" or graph_type.lower() == "line":
            t = "line"
        elif graph_type.lower() == "piechart" or graph_type.lower() == "pie":
            t = "pie"
        elif graph_type.lower() == "bubblechart" or graph_type.lower() == "bubble":
            t = "bubble"
        elif graph_type.lower() == "scatterchart" or graph_type.lower() == "scatter":
            t = "scatter"
        elif graph_type.lower() == "radarchart" or graph_type.lower() == "radar":
            t = "radar"
        elif graph_type.lower() == "polarchart" or graph_type.lower() == "polar":
            t = "polarArea"
        elif graph_type.lower() == "donutchart" or graph_type.lower() == "donut" or graph_type.lower() == "doughnut" or graph_type.lower() == "donuts":
            t = "doughnut"
        # return {"type":"graph", "data": results, "graph_type": t, "variables": var}
        return utils.update_siem_search_result({"type":"graph", "data":results, "graph_type":t, "variables":var})

    

    def execute_operation(self, operation: str, data: list, index:list, tenant: list, technology: list, start_time: str, end_time: str, token: str):
        graph_type, fields, values = self.parse_operation(operation)
        return self.evaluate_operation(data, graph_type, fields, values)

    def all_pages(self):
        return True
    
    def get_required_permissions(self):
        """ Does not require any permissions """
        return []
    
    def get_help(self):
        return f"""
        <!-- Render Graphs Section -->
        <button class="ui button collapsible">Render Graphs</button>
        <div class="ui segment collapsed-content">
            <p>The render operation displays different types of graphs for your data. Specify the graph type, data, and value field for counting.</p>
            <p>Available graph types include:</p>
            <ul class="ui list">
                <li>Bar</li>
                <li>Pie</li>
                <li>Line</li>
                <li>Scatter</li>
                <li>Doughnut</li>
                <li>Polar</li>
                <li>Radar</li>
                <li>Bubble</li>
            </ul>
            <h3>Example:</h3>
            <pre><code class="hljs">!search duser:administrator | !counts by duser over count | {self.keyword} piechart by duser over count</code></pre>
        </div>
        """