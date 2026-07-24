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
document: operation advanced condition
"""

from OperationBase import *
from WebRequester import *
import UtilsEnum as ue
import Utils as utils
import json, threading, traceback

class OperationAdvancedCondition(OperationBase):
    def __init__(self, indexers, logger, max_threads=10, raw=False, in_raw=False):
        self.keywords = {
            "normal": "!search",
            "raw": "!search_raw",
            "in_raw": "!search_in_raw"
        }
        self.in_raw = in_raw
        self.raw = raw
        self.indexers = indexers
        self.max_threads = max_threads
        self.logger = logger


    """     def identify_operation(self, operation: str) -> bool:
        # TODO find a better way for this function. If value are changed must change this part. 
        print("Operation:" + str(operation) + " self.raw:" + str(self.raw))
        if operation.startswith(self.keyword_2) and self.raw:
            print("self.raw:" + str(self.raw) + " in keyword_2")
            return True
        elif operation.startswith(self.keyword) and not operation.startswith(self.keyword_2) and not self.raw:
            print("self.raw:" + str(self.raw) + " in keyword")
            return True
        return False """

    def identify_operation(self, operation: str) -> bool:
        try:
            if self.raw and self.in_raw:
                if operation.startswith(self.keywords["in_raw"]):
                    self.logger.log("debug",f"self.raw: {self.raw} in keyword (in_raw)")
                    return True
                return False
            elif self.raw:
                if operation.startswith(self.keywords["raw"]):
                    self.logger.log("debug",f"self.raw: {self.raw} in keyword (raw)")
                    return True
                return False
            else:
                if operation.startswith(self.keywords["normal"]) and not operation.startswith(self.keywords["raw"]):
                    self.logger.log("debug", f"self.raw: {self.raw} in keyword (normal)")
                    return True
                return False
        except:
            self.logger.log("error", f"Error during identify_operation {traceback.format_exc()}")
            return False
    
    def get_suggestions(self):
        return [self.keywords["normal"] +  " <value>",self.keywords["normal"] + " <field>:<value>"
                ,self.keywords["raw"] + "<value>", self.keywords["raw"] + " <field>:<value>"
                ,self.keywords["in_raw"] + "<regex>"
                ]
    
    def parse_operation(self, operation: str, start_time: str = None, end_time: str = None):
        """
            Analyse and execute recursive lexical analysis from boolean expression
        """
        # Clean the expression to remove the keyword and add the start en end time
        if self.raw and self.in_raw and self.keywords["in_raw"] in operation:
            # Here no siem_timestamp available
            expression = operation.replace(self.keywords["in_raw"], "").strip()
        elif self.raw and self.keywords["raw"] in operation:
            expression = operation.replace(self.keywords["raw"], "").strip()
            expression = "(" + expression.strip() + ")"
            if start_time:
                expression += " and siem_timestamp >= " + start_time 
            if end_time:
                expression += " and siem_timestamp <= " + end_time
        elif self.keywords["normal"] in operation:
            expression = operation.replace(self.keywords["normal"], "").strip()
            expression = "(" + expression.strip() + ")"
            if start_time:
                expression += " and siem_timestamp >= " + start_time 
            if end_time:
                expression += " and siem_timestamp <= " + end_time
        else: 
            # If keyword already removed and timestamp added, return the expression itself.
            expression = operation.strip()
        # If expression is sourrounded by parenthesis, verify and delete only if balanced 
        if self.is_wrapped_by_parentheses(expression):
            expression = expression[1:-1].strip()
        # Treat operator 'or' at parent level
        or_parts = self.split_by_top_level_operator(expression, "or")
        if len(or_parts) > 1:
            return ["or"] + [self.parse_operation(part) for part in or_parts]
        # Treat operator 'and' at parent level
        and_parts = self.split_by_top_level_operator(expression, "and")
        if len(and_parts) > 1:
            return ["and"] + [self.parse_operation(part) for part in and_parts]
        # Treat operator 'not'
        if expression.startswith("not"):
            return ["not", self.parse_operation(expression[3:].strip())]
        # If none logic operation is found, return raw expression
        return expression


    def split_by_top_level_operator(self, expression, operator):
        """
        Split expression by an operator at top-level (without parenthesis)
        """
        parts = []
        parenthesis_count = 0
        start = 0
        for i, char in enumerate(expression):
            if char == '(':
                parenthesis_count += 1
            elif char == ')':
                parenthesis_count -= 1
            # Identify operator at parent level
            elif parenthesis_count == 0 and expression[i:i + len(operator)] == operator and \
                    (i == 0 or expression[i - 1].isspace()) and \
                    (i + len(operator) == len(expression) or expression[i + len(operator)].isspace()):
                parts.append(expression[start:i].strip())
                start = i + len(operator)
        # Add last part after last operator
        parts.append(expression[start:].strip())
        return parts


    def is_wrapped_by_parentheses(self, expression):
        # TODO change this function by the one in utils
        """
            Check if expression is sourrounded by parenthesis
        """
        if not (expression.startswith("(") and expression.endswith(")")):
            return False
        parenthesis_count = 0
        for i, char in enumerate(expression):
            if char == '(':
                parenthesis_count += 1
            elif char == ')':
                parenthesis_count -= 1
                # If parenthesis are closed before the end, not balanced
                if parenthesis_count == 0 and i != len(expression) - 1:
                    return False
        return parenthesis_count == 0


    def execute_operation(self, operation: str, data: list, index: list, tenant: list, technology: list, start_time: str, end_time: str, token: str, negative: bool = False):
        try:
            # TODO
            results = []
            parsed_query = self.parse_operation(operation, start_time, end_time)
            self.logger.log("debug", "PARSED QUERY:" + str(parsed_query))
            # if data is None: maybe useless
            results = self.search_data(self.evaluate_operation(parsed_query, [], index, tenant, technology, start_time, end_time, negative))
            # print("RESULTS IN EXECUTE OPERATION:" + str(results))
            # TODO maybe useless
            # else:
            #     results = self.search_data(self.evaluate_operation(parsed_query, data, tenant, start_time, end_time))
            if data is not None and "variables" in data:
                # data["data"] = result
                return utils.update_siem_search_result({"data":results,"sort_field":"siem_timestamp","sorted_by":"desc"})
            # return {"type": "table", "data": results, "fields": []}
            return utils.update_siem_search_result({"data":results,"sort_field":"siem_timestamp","sorted_by":"desc"})
        except Exception as e:
            self.logger.log("error", f"Error in execute operation advanced condition {traceback.format_exc()}")
            return data


    def evaluate_operation(self, parsed_expression: str, data: list, index: list, tenant: list, technology: list, start_time: str, end_time: str, negative: bool = False):
        """
            Evaluate expression using intermediate results (data) with parallelism
        """
        results = {}
        lock = threading.Lock()  # Lock to manage access to shared results

        def process_indexer(indexer, ind, ten, tech, negative=False):
            nonlocal results
            self.logger.log("debug", "Indexer:" + str(indexer) + str(indexer["host"]) + str(indexer["port"]) + str(indexer["auth_token"] + " " + str(parsed_expression)))
            try:
                start_request_index_adv_cond = time.time()
                # TODO use the request from the indexsearchmotor to take account the slave_reverse
                wr = WebRequester(indexer["host"], indexer["port"], indexer["auth_token"])
                if self.in_raw:
                    sub_result = json.loads(wr.search_in_raw_data(parsed_expression, ind, ten, start_time, end_time, tech, negative))
                else:
                    sub_result = json.loads(wr.search_index(parsed_expression, ind, ten, start_time, end_time, tech, negative))
                    print("sub_result:" + str(sub_result)[:100])
                self.logger.log("debug", "Time to request indexer adv_cond:" + str(time.time() - start_request_index_adv_cond) + " " + str(parsed_expression))
                start_merging_index_adv_cond = time.time()
                with lock:  # Secured access
                    results = utils.merge_dicts(results, sub_result, "or", self.max_threads)
                self.logger.log("debug","Time to merge indexer adv_cond:" + str(time.time() - start_merging_index_adv_cond))
            except Exception as ex:
                self.logger.log("error", f"Error when requesting indexer: {ex}")

        def process_expression(expr, operator, data, index, tenant, start_time, end_time, technology=None, negative=False):
            """Manage the treatment of sub expressions in parallel """
            sub_result = self.evaluate_operation(expr, data, index, tenant, technology, start_time, end_time, negative)
            with lock:
                nonlocal results
                if results is None:
                    results = sub_result
                else:
                    results = utils.merge_dicts(results, sub_result, operator, self.max_threads)
        try:
            # If expression is a chain, treat each indexer in parallem
            if isinstance(parsed_expression, str):
                print("instance of str : " + str(parsed_expression) + " " + str(index) + " " + str(tenant) + " " + str(technology))
                threads = []
                for indexer in self.indexers:
                    for ind in index:
                        for ten in tenant:
                            if len(technology) > 0:
                                for tech in technology:
                                    # Create a thread for each indexer
                                    thread = threading.Thread(target=process_indexer, args=(indexer, ind, ten, tech, negative))
                                    threads.append(thread)
                                    thread.start()
                            else:
                                thread = threading.Thread(target=process_indexer, args=(indexer, ind, ten, None, negative))
                                threads.append(thread)
                                thread.start()                               
                # Waith the end for all threads
                for thread in threads:
                    thread.join()
                return results
            # If expression is a list, treat depending on the operator
            elif isinstance(parsed_expression, list):
                print("instance of list : " + str(parsed_expression))
                operator = parsed_expression[0]
                if operator == "not":
                    # Reverse the current negative state
                    negative = not negative
                    results = None
                    thread = threading.Thread(
                        target=process_expression,
                        args=(parsed_expression[1], "not", data, index, tenant, start_time, end_time, technology, negative)
                    )
                    thread.start()
                    thread.join()
                    # Test TODO erase this part if it does not work
                    if data is None or len(data) == 0:
                        print("ERROR: No data found")
                        return results
                    else:
                        # return utils.merge_dicts(data, results, "not", self.max_threads)
                        # TODO check if the logic is right
                        return utils.merge_dicts(results, data, "or", self.max_threads)
                elif operator in ("and", "or"):
                    # For "and" / "or", treat all sub expressions in parallel
                    threads = []
                    results = None  # Initi to store results fusioned
                    for expr in parsed_expression[1:]:
                        # Reverse in case of negative true
                        if negative:
                            if operator == "and":
                                operator = "or"
                            elif operator == "or":
                                operator = "and"
                        thread = threading.Thread(
                            target=process_expression,
                            args=(expr, operator, data, index, tenant, start_time, end_time, technology, negative)
                        )
                        threads.append(thread)
                        thread.start()
                    # Wait all threads of sub expression finished
                    for thread in threads:
                        thread.join()
                    return results if results is not None else {}
            else:
                raise ValueError("Invalid expression.")
        except Exception as e:
            print(f"Error during the evaluation of the operation: {e}")
            return {}


    def search_data(self, ids, strategy="by_date", raw=False):
        try:
            results = []
            threads = []
            results_lock = threading.Lock()  # To avoid conflicts during results added
            # Function to maange research on indexer 
            def search_indexer(indexer, indexer_ids):
                try:
                    # TODO use the function at the indexsearchmotor level to use the slave reverse in case of setup
                    wr = WebRequester(indexer["host"], indexer["port"], indexer["auth_token"])
                    start_search_data_ind = time.time()
                    r = wr.search_data(indexer_ids, self.raw)
                    self.logger.log("debug", f"Search data time for indexer {indexer['host']}:{indexer['port']} - {time.time() - start_search_data_ind}")
                    result = json.loads(r)
                    self.logger.log("debug", f"Search data time for indexer jsonloads {indexer['host']}:{indexer['port']} - {time.time() - start_search_data_ind}")
                    mid = time.time()
                    with results_lock:  # Secured access on results table
                        # results.extend(result)
                        results[:] = utils.merge_sorted_results(results, result, "siem_timestamp")
                        self.logger.log("debug", f"Search data results for indexer extend {(time.time() - mid)}")
                except Exception as e:
                    self.logger.log("error", f"Error with indexer {indexer['host']}:{indexer['port']} - {e}")
            start_search_data_adv_cond = time.time()
            # Organisation of indexers by group
            groups = {}
            for indexer in self.indexers:
                group = indexer.get("group")
                if group not in groups:
                    groups[group] = {"primaries": [], "secondaries": []}
                if indexer.get("primary", False) == "true":
                    groups[group]["primaries"].append(indexer)
                else:
                    groups[group]["secondaries"].append(indexer)
            # Repartition of ids by group
            for group_id, indexer_group in groups.items():
                primary_indexers = indexer_group["primaries"]
                secondary_indexers = indexer_group["secondaries"]
                # Regroup indexers (primaries + secondaries) for this group
                all_group_indexers = primary_indexers + secondary_indexers
                # If group has one indexer (primary or secondary), send all ids
                if len(all_group_indexers) == 1:
                    indexer = all_group_indexers[0]
                    thread = threading.Thread(target=search_indexer, args=(indexer, ids))
                    threads.append(thread)
                    thread.start()
                    self.logger.log("debug", "Single indexer group, sending all IDs")
                else:
                    # Dispatch ids according to strategy chosen
                    if strategy == "equitable":
                        # Reparition of ids between indexers
                        total_indexers = len(all_group_indexers)
                        for i, indexer in enumerate(all_group_indexers):
                            split_ids = {}
                            for tenant, tenant_data in ids.items():
                                split_ids[tenant] = {}
                                for date, date_ids in tenant_data.items():
                                    # Split by ids for each indexer
                                    split_ids[tenant][date] = date_ids[i::total_indexers]
                            # print(f"Indexer {indexer['host']}:{indexer['port']} will get {split_ids}")
                            # Create a thread for each indexer with ids assigned
                            thread = threading.Thread(target=search_indexer, args=(indexer, split_ids))
                            threads.append(thread)
                            thread.start()
                    elif strategy == "by_date":
                        # Repartition of ids by date
                        for i, indexer in enumerate(all_group_indexers):
                            split_ids = {}
                            for tenant, tenant_data in ids.items():
                                split_ids[tenant] = {}
                                for j, (date, date_ids) in enumerate(tenant_data.items()):
                                    # Assign entire date for each indexer (alternativelly)
                                    if j % len(all_group_indexers) == i:
                                        split_ids[tenant][date] = date_ids
                            # Create a thread for each indexer with ids 
                            thread = threading.Thread(target=search_indexer, args=(indexer, split_ids))
                            threads.append(thread)
                            thread.start()
                    else:
                        raise ValueError(f"Unknown strategy: {strategy}")
            # Wait all threads ends
            for thread in threads:
                thread.join()
            self.logger.log("debug", f"Time to search data adv_cond: {time.time() - start_search_data_adv_cond}")
            # Return results
            return results
        except Exception as e:
            # TODO add differents error type to give more information
            self.logger.log("error", f"Error during search_data {traceback.format_exc()}")
            # return {"type": "table", "data": [], "fields": []}
            return ue.SIEM_SEARCH_FORMAT.result.update({"errors":["Error during search data"]})


    def all_pages(self):
        return False
    
    def get_required_permissions(self):
        if self.raw:
            return [{"resource":"raw", "type": "operation", "read": True, "write": False}]
        return []
    
    def get_help(self):
        key_normal = self.keywords["normal"]
        key_raw = self.keywords["raw"]
        key_in_raw = self.keywords["in_raw"]
        help = """"""
        if self.in_raw:
            help += f"""
                <!-- Basic in raw Conditions Section -->
                <button class="ui button collapsible">Basic in raw Conditions</button>
                <div class="ui segment collapsed-content">
                <p>Basic in raw conditions are applied at the database level directly level to search any specific regex. No logical operators like <code>AND</code>, <code>OR</code>, or <code>NOT</code> are allowed in this type of condition. 
                <p>Results of this command will be returned as raw logs lines</p>
                This command start with the keyword {key_in_raw}</p>
                <h3>Examples:</h3>
                <pre><code class="hljs">{key_in_raw} session opened</code></pre>
                <pre><code class="hljs">{key_in_raw} s|Sessions\so|Opened|</code></pre>
                <pre><code class="hljs">{key_in_raw} [\w\d]+</code></pre>
                </div>
            """
        elif not self.raw:
            help += f"""
            <!-- Basic Conditions Section -->
            <button class="ui button collapsible">Basic Conditions</button>
                <div class="ui segment collapsed-content">
                <p>Basic conditions are applied at the index level to search specific fields and values. No logical operators like <code>AND</code>, <code>OR</code>, or <code>NOT</code> are allowed in this type of condition. 
                This command start with the keyword {key_normal}.</p>
                <p>You can search with or without specifying fields:</p>
                <ul class="ui list">
                    <li><strong>With fields:</strong> <code>field:value</code></li>
                    <li><strong>Without fields:</strong> <code>Value</code></li>
                </ul>
                <p>Operators available for text fields include:</p>
                <pre><code class="hljs">
                    field:value
                    value
                    *value
                    value*
                    *value*
                    $value$
                    /value/
                </code></pre>
                <h3>Examples:</h3>
                <pre><code class="hljs">{key_normal} name:session opened</code></pre>
                <pre><code class="hljs">{key_normal} session opened</code></pre>
                <pre><code class="hljs">{key_normal} duser:$administrator$</code></pre>
                </div>
                
                <!-- Advanced Conditions Section -->
                <button class="ui button collapsible">Advanced Conditions</button>
                <div class="ui segment collapsed-content">
                    <p>Advanced conditions are used to correlate several basic conditions using logical operators like <code>AND</code>, <code>OR</code>, and <code>NOT</code>.</p>
                    <p>You can also use parentheses to set the priority of operations.</p>
                    <h3>Examples:</h3>
                    <pre><code class="hljs">{key_normal} name:session opened and (duser:$administrator$ or duser:$guest$)</code></pre>
                    <pre><code class="hljs">{key_raw} name:session opened and (duser:$administrator$ or duser:$guest$)</code></pre>
                </div>
                """
        else:
            help += f"""
                <!-- Basic RAW Conditions Section -->
                <button class="ui button collapsible">Basic Raw Conditions</button>
                <div class="ui segment collapsed-content">
                    <p>Basic raw conditions are the same as basic conditions but the results will be returned as raw data.</p>
                    <p>Advanced conditions also applied to this type of condition.</p>
                    <p>The keyword to use is {key_raw}</p>
                    <p>Refer to basic conditions for more information.</p>
                    <h3>Examples:</h3>
                    <pre><code class="hljs">{key_raw} name:session opened</code></pre>
                    <pre><code class="hljs">{key_raw} session opened</code></pre>
                    <pre><code class="hljs">{key_raw} duser:$administrator$</code></pre>
                    </div>"""
        return help