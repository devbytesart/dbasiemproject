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
document: index search motor
"""

from ServiceBase import *
from Configurator import *
from CMDHandler import *
from Logger import *
from datetime import datetime, timezone, timedelta
from Webhook import *
from WebRequester import *
import traceback, os, threading, re
from collections import defaultdict
from OperationBase import *
from OperationCount import *
from OperationProject import *
from OperationRender import *
from OperationVariable import *
from OperationAdvancedCondition import *
from OperationTransform import *
from OperationOrder import *
from ParameterLoader import *
from ReportManager import *
import UtilsEnum as uenum
import uuid, re

class IndexSearchMotor(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "query_data": self.handle_search_data, 
                "get_page": self.get_page, 
                "get_suggestions": self.handle_get_suggestions, 
                "shutdown": self.handle_shutdown, 
                "get_available_indices": self.handle_get_available_indices, 
                "get_available_tenants": self.handle_get_available_tenants, 
                "get_available_technologies": self.handle_get_available_technologies, 
                "get_help": self.handle_get_help, 
                "reset_research_timeout": self.handle_reset_research_timeout,
                "generate_report": self.handle_generate_report,
                "download_document": self.handle_download_document,
                "retrieve_monitoring": self.handle_retrieve_monitoring
                })
            #self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            # Store result final and intermediate results
            # self.data_store = {}
            # self.current_id = 0
            # For the counts part
            self.lock = threading.Lock()  # Utilisé pour protéger l'accès au dictionnaire partagé
            self.global_count_dict = defaultdict(int)  # Dictionnaire partagé entre les threads
            #self.operations = [OperationAdvancedCondition(self.indexers, int(self.max_threads/3)), OperationAdvancedCondition(self.indexers, int(self.max_threads/3), True), OperationCount(int(self.max_threads/3)), OperationProject(), OperationRender(), OperationVariable(self, int(self.max_threads/3)), OperationTransform()]
            self.current_page = 0
            self.last_result = {}
            # Document
            self.documents = {}
            # Timeout for researches
            # TODO add the timeout researches in the configuration file
            self.timeout_search = 300
            self.last_results_timeout = {}
            self.timeout_thread = threading.Thread(target=self._watch_timeouts)
            self.timeout_thread.start()
            self._start_microservices()
            # Statistics
            # TODO statistics
        except:
            self.logger.log("error", f"Error during initialization of IndexSearchMotor {traceback.format_exc()}")


    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
        self.max_threads = self.config["max_threads"]
        # WEB REQUESTER
        self.proxies = self.config["webrequester"]["proxy"]
        self.timeout = self.config["webrequester"]["timeout"]
        self.slave_reverse = self.config["webrequester"].get("slave_reverse", None)
        print(self.slave_reverse)
        # LOGGER
        self.monitoring_log_level = self.config["logger"]["log_level"]
        self.monitoring_log_path = self.config["logger"]["log_path"]
        self.monitoring_max_queue_size = self.config["logger"]["max_queue_size"]
        self.monitoring_max_file = self.config["logger"]["max_file"]
        self.monitoring_max_file_size = self.config["logger"]["max_file_size"]
        self.monitoring_enable_print = utils.convert_param_type(self.config["logger"]["enable_print"], bool)
        self.monitoring_enable_queue = utils.convert_param_type(self.config["logger"]["enable_queue"], bool)
        self.monitoring_enable_file = utils.convert_param_type(self.config["logger"]["enable_file"], bool)
        # WEBHOOK
        self.webhook_host = self.config["webhook"]["host"]
        self.webhook_port = self.config["webhook"]["port"]
        self.webhook_token = self.config["webhook"]["auth_token"]
        self.webhook_certfile = self.config["webhook"]["certs"]["certfile"]
        self.webhook_keyfile = self.config["webhook"]["certs"]["keyfile"]
        # AUTHENTICATOR
        self.authenticatorsReq = None
        if "authenticator" in self.config and "id" in self.config["authenticator"]:
            self.authenticators_id = self.config["authenticator"]["id"]
            self.authenticators_host = self.config["authenticator"]["host"]
            self.authenticators_port = self.config["authenticator"]["port"]
            self.authenticators_auth_token = self.config["authenticator"]["auth_token"]
            self.authenticatorsReq = WebRequester(self.authenticators_host, self.authenticators_port, self.authenticators_auth_token, slave_reverse=self.slave_reverse)
        # DEDICATED INDEX SEARCH MOTOR
        self.indexers = self.config["indexers"]

    def _stop_microservices(self):
        try:
            # Stop the webhook
            self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Failed to stop microservices: {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            # Start the webhook
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            # Careful to the order of operator which is very important
            # TODO find a way to not be dependant of the order
            self.operations = [OperationAdvancedCondition(self.indexers, self.logger, int(self.max_threads/3), True, True), OperationAdvancedCondition(self.indexers, self.logger, int(self.max_threads/3), True), OperationAdvancedCondition(self.indexers, self.logger, int(self.max_threads/3)), OperationCount(int(self.max_threads/3)), OperationOrder(int(self.max_threads/3)), OperationProject(), OperationRender(), OperationVariable(self, int(self.max_threads/3)), OperationTransform()]
            # Reporting
            self.report_manager = ReportManager(self.logger, self, self.authenticatorsReq)
            return True
        except:
            self.logger.log("error", f"Failed to start microservices: {traceback.format_exc()}")
            return False

    def _restart_microservices(self):
        try:
            stopped = self._stop_microservices()
            if stopped:
                return self._start_microservices()
            else:
                return False
        except:
            self.logger.log("error", f"Failed to restart microservices: {traceback.format_exc()}")
            return False

    def _watch_timeouts(self):
        """Thread that watch and clean expired data."""
        while True:
            time.sleep(5)  
            # Check every 5 seconds
            current_time = time.time()
            with self.lock:
                to_delete = []
                for user_id, last_time in self.last_results_timeout.items():
                    elapsed_time = current_time - last_time
                    if elapsed_time >= self.timeout_search:
                        to_delete.append(user_id)
                    else:
                        self.last_results_timeout[user_id] += elapsed_time  # Update
                for user_id in to_delete:
                    # delete search results
                    del self.last_result[user_id]
                    del self.last_results_timeout[user_id]
                    # if user_id in self.documents:
                    #     del self.documents[user_id]
                    # TODO Find a way to delete documents after a amount of time

    def handle_reset_research_timeout(self, data):
        """Reset the research timeout counter for a user."""
        try:
            token = json.loads(data.get("session_token"))
            user_id = token.get("user_id")
            with self.lock:
                self.last_results_timeout[user_id] = time.time()
                print(str(self.last_results_timeout))
            return True
        except:
            self.logger.log("error", f"Failed to reset research timeout: {traceback.format_exc()}")
            return False

    def _load_stats(self):
        # TODO implement this part
        pass

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def handle_set_config(self, data):
        """Set the configuration of the index search motor"""
        # TODO implement change of configuration on microservices
        try:
            self.configurator.set_config(data)
            self.load_configuration()
        except:
            self.logger.log("error", f"Failed to set configuration: {traceback.format_exc()}")
            return None

    def handle_shutdown(self):
        #TODO implement shutdown
        pass

    def _check_permissions(self, token, indices, tenants, technologies):
        """Check permissions for user indices, tenants, technologies and return only the elements where the user has permissions
        return error if none permissions """
        if not self.authenticatorsReq or token.get("authenticator") != self.authenticators_id:
            # TODO return error for the userinterface
            self.logger.log("warning", f"Error during check permissions, authenticators not defined or does not correspond to the configured one in index search motor.")
            return None, None, None
        token_data = token.get("token")
        # Check indices
        authorized_indices = []
        for index in indices:
            if json.loads(self.authenticatorsReq.check_permissions(token_data, [{"resource": index, "type": "index", "read": True, "write": False}])):
                authorized_indices.append(index)
        # Check tenants
        authorized_tenants = []
        for tenant in tenants:
            if json.loads(self.authenticatorsReq.check_permissions(token_data, [{"resource": tenant, "type": "tenant", "read": True, "write": False}])):
                authorized_tenants.append(tenant)
        # Check for technologies
        # TODO change this part
        authorized_technologies = technologies
        # TODO this part. If one or several technologies are defined. The user is limited to these only, if not all are authorized.
        if len(authorized_indices) == 0 or len(authorized_tenants) == 0:
            self.logger.log("warning", f"User does not have any permissions on the required indices or tenants")
            return None, None, None
        else:
            return authorized_indices, authorized_tenants, authorized_technologies

    def handle_search_data(self, request, current_id="main"):
        #Version 2.0 of handle_search_data
        """Search logs to return"""
        try:
            print("handle_search_data request :", str(request))
            # TODO verify authorization of access
            # TODO fields must be join by _ and not by space
            # TODO interprets request
            # TODO change tenant and period
            if not self.authenticatorsReq:
                self.logger.log("warning", f"No token set in the user query: {self.id} - {current_id}")
                return []
            print("after check authenticator")
            request = request.get("query")
            query = request.get("query")
            current_id = request.get("current_id", "main")
            print("INDEXSEARCH QUERY DATA: " + current_id)
            self.last_result[current_id] = None
            print("request:" + str(request) + " " + str(type(request)) + ": " + str(request["query"]))
            token = json.loads(request.get("session_token"))
            token_data = token.get("token")
            index = request["index"]
            tenant = request["tenant"]
            all_pages = request.get("all_pages", False)
            print("all_pages:" + str(all_pages) + " " + str(type(all_pages)))
            # TODO this part is not implemented
            technologies = request.get("technology", None)
            print("technologies:" + str(technologies) + " " + str(type(technologies)))
            index, tenant, technologies = self._check_permissions(token, index, tenant, technologies)
            if index is None or tenant is None:
                # Return None as the user has no permissions on these requests
                return [] 
            start_time = request["startTime"]
            if not start_time:
                start_time = (datetime.now(timezone.utc) - timedelta(days=99999)).strftime("%Y-%m-%d %H:%M:%S")
            end_time = request["endTime"]
            if not end_time:
                end_time = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            # query = request["query"]
            start_action = time.time()
            res = self.interpretRequest(query, index, tenant, technologies, start_time, end_time, token_data, current_id=current_id, all_pages=all_pages)
            self.logger.log("debug", f"Time to interpret request data: {time.time() - start_action}")
            return res
        except:
            self.logger.log("error", f"Error during handle search data: {traceback.format_exc()}")
            return []
            # TODO handle error
    
    def interpretRequest(self, request: str, index: list, tenant: list, technology: list, start_time: str, end_time: str,token : str, delimiter = "|", current_id="main", all_pages=False):
        """
        Interpret requests data and execute corresponding operations
        Results of each operation are used as entry in next part.
        If request does not contains '|', it is evaluate directly.
        """
        try:
            start_interpret_request = time.time()
            operations = request.split(delimiter)
            last_result = None  # Init last_result to contain results of each operation
            last_operation = None
            for operation in operations:
                print("operation: " + str(operation))
                operation = operation.strip()  # Delete spaces
                # TODO add search in operation
                for o in self.operations:
                    if o.identify_operation(operation):
                        # Check permissions
                        required_permissions = o.get_required_permissions()
                        if len(required_permissions) > 0:
                            if not json.loads(self.authenticatorsReq.check_permissions(token, required_permissions)):
                                # Users does not have the permission to execute this operation
                                self.logger.log("warning", f"User does not have the permission to execute this operation: {operation}")
                                return []
                        print("operation: " + str(o) + " after permissions checked. technology: " + str(technology))
                        start_operation = time.time()
                        last_result = o.execute_operation(operation, last_result, index, tenant, technology, start_time, end_time, token)
                        print("Time operation: " + str(o) + ":" + str(time.time() - start_operation))
                        last_operation = o
                        break
            # Return last result after execution of each operations
            #  return last_result
            # Manage previous variables
            self.logger.log("debug", f"Time to interpret request operations: {time.time() - start_interpret_request}")
            # print("LAST RESULTS:" + str(last_result))
            # print(ue.SIEM_SEARCH_FORMAT.result.value)
            self.last_result[current_id] = last_result
            self.last_results_timeout[current_id] = time.time()
            # For update
            enrichment = {"indices":index, "tenants":tenant, "technologies":technology, "request": request}
            if last_result and last_result["type"] == "table":
                copy = self.get_page({"session_token":token, "action": "first", "current_page": 0, "number_of_items": last_operation.all_pages()}, all_pages, current_id)
                copy.update(enrichment)
            else:
                copy = last_result
                copy.update(enrichment)
            return copy
        except Exception as e:
            self.logger.log("error", f"Error during request interpretation: {traceback.format_exc()}")
            print(f"{traceback.format_exc()}")
            return []  # In case of error, return empty list and an error message 

    def get_page(self, data, all_items=False, current_id="main"):
        """ Return the current page"""
        try:
            start_get_page = time.time()
            action = data["action"]
            session_token = data["session_token"]
            current_id = data.get("current_id", current_id)
            print("GET PAGE CURRENT ID :" + str(current_id))
            print("all pages:" + str(all_items) + " " + str(type(all_items)))

            #Verify username
            # TODO change this one. Main should be erased.
            if current_id != "main" and "_" in current_id:
                # TODO change this part as the _ can be problematic
                # user_id = current_id.rsplit("_",1)[0]
                user_id, p_id = utils.parse_current_id(current_id)
                try:
                    if not json.loads(self.authenticatorsReq.check_username(user_id, session_token)):
                        self.logger.log("error", f"{user_id} is not allowed to access this page")
                        return []
                except Exception as e:
                    self.logger.log("error", f"Error during check username from indexsearchmotor: {traceback.format_exc()}")
                    return []

            # print("DATA RECEIVED:" + str(data))
            if "current_page" in data:
                current_page = int(data["current_page"])
            if all_items:
                print("ALL ITEMS: " + str(all_items))
                items_per_page = len(self.last_result[current_id]["data"])
                print("ITEMS PER PAGE: " + str(items_per_page))
            elif "items_per_page" in data:
                # print("ITEMS PER PAGE from parameter")
                items_per_page = int(data["items_per_page"])
            else:
                # print("items per page by default")
                items_per_page = 10

                        # Sorted by
            sorted_by = None
            sort_field = None
            if "sort_field" in data:
                sort_field = data["sort_field"]
            if "sorted_by" in data:
                sorted_by = data["sorted_by"]

            # Variables
            variables = {}
            if "variables" in self.last_result[current_id]:
                variables = self.last_result[current_id]["variables"]

            data = self.last_result[current_id]["data"]
            # print("LAST RESULTS CURRENT ID:" + str(data))
            fields = []
            if self.last_result[current_id]["fields"] and len(self.last_result[current_id]["fields"]) > 0:
                fields = self.last_result[current_id]["fields"]
            else:
                for d in data:
                    # for f in json.loads(d).keys():
                    for f in d.keys():
                        if f not in fields:
                            fields.append(f)
            # Get action received by the frontend
            if action == 'next':
                current_page += 1
            elif action == 'previous':
                current_page = max(0, current_page - 1)
            elif action == 'first':
                current_page = 0
            elif action == 'last':
                current_page = len(data) // items_per_page
            elif action == 'change_page_size':
                current_page = 0
            else:
                if action == 'go_to_page':
                    pass

            # Pagination
            start = current_page * items_per_page
            end = start + items_per_page
            paginated_data = data[start:end]

            print("before create link")
            print("after insert")

            for page in paginated_data:
                print("after page")
                for f, v in page.items():
                    try:
                        # File type list to treat
                        file_types = [uenum.SIEM_File_Type.pdf, uenum.SIEM_File_Type.csv]
                        if isinstance(v, str):
                            v_clean = v.strip().strip('"')
                            print("In f,v:", str(v_clean), str(type(v_clean)))
                            for file_type in file_types:
                                prefix = f"{uenum.SIEM_Field_Format.file.value}/{file_type.value}:"
                                # Regex : prefix followed by base64 (A-Z, a-z, 0-9, +, /, =)
                                pattern = re.escape(prefix) + r"[A-Za-z0-9+/=]+"
                                if re.search(pattern, v_clean):
                                    print("INSIDE")
                                    rand_id = str(uuid.uuid4())
                                    print("RAND:", rand_id)
                                    # Stockage 
                                    self.documents[rand_id] = v_clean
                                    print("self doc ad")
                                    # Replace by a link
                                    prefix_url = f"{uenum.SIEM_Field_Format.link.value}/{uenum.SIEM_File_Type.url.value}:"
                                    page[f] = re.sub(pattern, f"{prefix_url}/downloads?id={rand_id}", v_clean)
                                    print("changed for :" + rand_id)
                                    break  # Exit when format is found
                    except Exception:
                        self.logger.log("debug", f"Error during data transformation: {traceback.format_exc()}")
                        print(f"Error during data transformation: {traceback.format_exc()}")

            print("after create link file")

            # Reforward data to the waited format per datatable            
            response = {
                "type": "table",
                "data": paginated_data,
                "fields": fields, 
                "items_per_page": items_per_page,
                "total_pages": (len(data) // items_per_page) + 1,
                "total_items": len(data),
                "start_index": start,
                "end_index": end,
                "current_page": current_page,
                "sorted_by": sorted_by,
                "sort_field": sort_field,
                "variables": variables
            }

            # Update self last result timeout 
            self.last_results_timeout[current_id] = time.time()

            self.logger.log("debug", f"Get page in {time.time() - start_get_page} seconds")
            print("RESPONSE GET PAGE:" + str(len(response["data"])))
            # print("RESPONSE GET PAGE:" + str(self.last_result))
            return response
        except:
            self.logger.log("error", f"Error during get_page {traceback.format_exc()}")
            return []
            # TODO handle error


    def handle_get_suggestions(self, data):
        """ Return the current page
            data ignored here
        """
        # TODO propose suggestions from the data
        try:
            suggestions = []
            for operation in self.operations:
                    suggestion = operation.get_suggestions()
                    print("SUGGESTION:" + str(suggestion) + str(type(suggestion)))
                    if suggestion:
                        suggestions += suggestion
            return suggestions
        except:
            self.logger.log("error", f"Error during get suggestions: {traceback.format_exc()}")
            return []
    
    def _get_av(self, type, data):
        """ Function to simplify the get_availables indices, tenants, technologies """
        try:
            results = []
            token = json.loads(data.get("session_token"))
            token_data = token.get("token")
            for indexer in self.indexers:
                wr = WebRequester(indexer.get("host"), indexer.get("port"), indexer.get("auth_token"), slave_reverse=self.slave_reverse)
                if type == "indices":
                    ind = json.loads(wr.get_available_indices(token_data))
                    if ind and json.loads(self.authenticatorsReq.check_permissions(token_data, [{"resource": ind, "type": "index", "read": True, "write": False}])):
                        results.append(ind)
                elif type == "tenants":
                    ten = json.loads(wr.get_available_tenants(token_data))
                    # print("TENANT:" , str(ten) , " " , str(type(ten)))
                    for t in ten:
                        # print("TENANT T:" , str(t))
                        if json.loads(self.authenticatorsReq.check_permissions(token_data, [{"resource": t, "type": "tenant", "read": True, "write": False}])):
                            results.append(t)
                elif type == "technologies":
                    tech = json.loads(wr.get_available_technologies(token_data))
                    # print("TECH:" , str(tech) , " " , str(type(tech)))
                    for te in tech:
                        # print("TECH T:" , str(te))
                        if json.loads(self.authenticatorsReq.check_permissions(token_data, [{"resource": te, "type": "technology", "read": True, "write": False}])):
                            results.append(te)
            print("RESULTS:" , str(list(set(results))))
            return list(set(results))
        except:
            self.logger.log("error", f"Error during get_available_indices: {traceback.format_exc()}")
            return []

    def handle_get_available_indices(self, data):
        """ Return the availables indices from the dedicated index search motor connected
        according to the user's permissions """
        return self._get_av("indices", data)
    
    def handle_get_available_tenants(self, data):
        """ Return the availables tenants from the dedicated index search motor connected
        according to the user's permissions """
        return self._get_av("tenants", data)
        
    def handle_get_available_technologies(self, data):
        """ Return the availables technologies from the dedicated index search motor connected
        according to the user's permissions """
        return self._get_av("technologies", data)
    
    def handle_generate_report(self, data):
        """ Generate the report and return the report"""
        try:
            # Get info from data json
            print("HANDLE GENERATE REPORT:", str(data))
            token = json.loads(data.get("session_token"))
            token_data = token.get("token")
            # index = data.get("index")
            # tenant = data.get("tenant")
            format_report = data.get("format","pdf")
            # Check user permissions
            # permissions_required = []
            # for ind in index:
            #     permissions_required.append({"resource": ind, "type": "index", "read": True, "write": False})
            # for ten in tenant:
            #     permissions_required.append({"resource": ten, "type": "tenant", "read": True, "write": False})
            # TODO add maybe technology
            # TODO add permissions to export report ??? 
            # if json.loads(self.authenticatorsReq.check_permissions(token_data, permissions_required)):
            report = self.report_manager.generate_report(data, token)
            print("report:",str(report))
            return report
        except:
            self.logger.log("error", f"Failed to generate report {traceback.format_exc()}")
            return None


    def handle_download_document(self, data):
        """Return the base64 document with prefix (pdf or csv) stored in self.documents"""
        try:
            print("download doc data:", str(data), str(type(data)))
            doc_id = data.get("id", None)
            token = json.loads(data.get("session_token"))
            token_data = token.get("token")

            if doc_id is None or doc_id not in self.documents:
                print("doc_id not in self.documents", str(doc_id))
                return None

            # TODO: check permissions of user with token_data
            document = self.documents.get(doc_id, "")
            print("get document:", str(document))

            # Here, we do not decode, we send the chain with the prefix
            # Example: "file/pdf:BASE64DATA..." ou "file/csv:BASE64DATA..."
            if any(
                document.startswith(f"{uenum.SIEM_Field_Format.file.value}/{ft.value}:")
                for ft in [uenum.SIEM_File_Type.pdf, uenum.SIEM_File_Type.csv]
            ):
                return document

            print("Unknown document format")
            return None

        except Exception:
            self.logger.log("error", f"Failed to download document: {traceback.format_exc()}")
            return None



    def handle_get_help(self, data):
        """ Return the help of the index search motor """
        help = """
            <p>Welcome to the query help page! This guide will help you understand how to create queries for search purposes.</p>
            <p><strong>Please follow the instructions below to build complex queries using different operations and filters.</strong></p>

            <!-- Operations Section -->
            <button class="ui button collapsible">Operations</button>
            <div class="ui segment collapsed-content">
                <p>The search bar allows you to perform different operations on search results. Operations are executed sequentially and separated by a pipe `|`.</p>
                <p>The following operations are available:</p>
                <ul class="ui list">
                    <li>Basic</li>
                    <li>Advanced</li>
                    <li>Select</li>
                    <li>Project</li>
                    <li>Counts By</li>
                    <li>Order by</li>
                    <li>Render</li>
                    <li>Transform</li>
                    <li>Variable</li>
                </ul>
                <p>Each operation processes the result of the previous one, building up to the final result. Not all operations can be combined freely.</p>
                <p>Here are some valid sequences:</p>
                <pre><code class="hljs">Basic operation | select operation</code></pre>
                <pre><code class="hljs">Basic operation | project operation</code></pre>
                <pre><code class="hljs">Basic operation | counts operation | render operation</code></pre>
                    </div>
            """
        for operation in self.operations:
            help += operation.get_help()
        return help

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():    
        indexsearchmotor = IndexSearchMotor('indexsearchmotorconfig.json',config_loader.get_config())