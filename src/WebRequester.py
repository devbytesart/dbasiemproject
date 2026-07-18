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
document: webrequester
"""

import requests
import json
import traceback
import urllib3
import time
import gzip
# import lz4.frame
# import zstandard as zstd
import Utils as utils

requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebRequester:
    def __init__(self, host, port, token, timeout=120, proxy=None, slave_reverse=None):
        # TODO add timeout in configuration for others classes
        self.timeout = timeout
        self.host = host
        self.port = port
        self.token = token
        # self.webhook_url = webhook_url
        self.slave_reverse = None
        # print("SLAVE REVERSE:" + str(slave_reverse) + ":" + str(type(slave_reverse)))
        if slave_reverse is not None and slave_reverse.get("slave_id") != '':
            self.slave_reverse = slave_reverse
            print("Slave Reverse: " + str(slave_reverse))
            self.slave_host = slave_reverse["host"]
            self.slave_port = slave_reverse["port"]
            self.token = slave_reverse["auth_token"]
            # self.slave_webhook_url = f"https://{slave_host}:{slave_port}/webhook"
        # self.webhook_url = f"https://{ip}:{port}/{webhook_url}"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.proxies = {"https": proxy} if proxy is not None else None
        
        
    def shutdown(self, force=False, retry=5):
        """Send a request to close the service"""
        data = {
            "shutdown": {
                "force": force
            }
        }
        return self.send_request("shutdown", data, retry)

#########################################
#
#       requests format
#
##########################################

    def configure(self, path_list, configuration, retry=5):
        """
        Send a request of type "configure" that change the configuration
        path: array of root, child, ... 
        data: configuration to change in the file
        """
        data = {
            "configure": {
                "path_list": path_list,
                "configuration" : configuration
            }
        }
        return self.send_request("webhook", data, retry)
    
    def configuration(self, path=[], data=[], retry=5):
        """
        Send a request of type "configuration" that retrieve the configuration
        path: array of root, child, ...
        """
        data = {
            "configuration": {
                "path" : path,
                "configuration" : data
            }
        }
        return self.send_request("webhook", data , retry)

    def retrieve_logs(self, size, index=None, retry=5):
        """
        Send a request of type "retrieve_log" that retrieve the last size logs
        size: number of logs to retrieve
        """
        data = {
            "retrieve_logs": {
                "size" : size,
                "index": index
            }
        }
        return self.send_request("binary", data, retry)
    
    def retrieve_monitoring(self, size, retry=5):
        """
        Send a request of type "retrieve_log" that retrieve the last size logs
        size: number of logs to retrieve
        """
        data = {
            "retrieve_monitoring": {
                "size" : size
            }
        }
        return self.send_request("binary", data, retry)

    def retrieve_mapping(self, retry=5):
        """
        Send a request of type "retrieve_mapping" that retrieve the mapping
        """
        data = {
            "retrieve_mapping": {}
        }
        return self.send_request("webhook", data, retry)
    
    def query_data(self, query, retry=5):
        """
        Send a request of type "query_data" that retrieve the data
        query: query to search
        """
        data = {
            "query_data": {
                "query" : query
            }
        }
        return self.send_request("webhook", data, retry)
    
    def search_data(self, ids, raw = False, retry=5, is_compressed=True):
        """
        Send a request of type "search_data" that retrieve the data
        query: query to search
        """
        data = {
            "search_data": { 
                "id": ids,
                "raw": raw
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)
    
    def search_in_raw_data(self, query, index, tenant, start_time, end_time, technology=None, negative=False, retry=5, is_compressed=True):
        """ 
        Send a request to the service to search regex directly in raw log
        """
        data = {
            "search_in_raw_data": {
                "query": query, 
                "index": index, 
                "tenant": tenant, 
                "start_time": start_time, 
                "end_time": end_time, 
                "technology": technology, 
                "negative": negative
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)

    def search_cached_data(self, index_name, ids, raw = False, retry=5, is_compressed=True):
        """
        Send a request of type "search_cached_data" that retrieve the data
        query: query to search
        """
        data = {
            "search_cached_data": {
                "index_name" : index_name,
                "ids" : ids, 
                "raw" : raw
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)
    
    def store_cached_data(self, index_name, data, raw = False, retry=5, is_compressed=True):
        """
        Send a request of ids and data to store in the cache
        data : [{id1: data1}, {id2: data2}, ...]
        """
        data = {
            "store_cached_data": {
                "index_name" : index_name,
                "data" : data, 
                "raw" : raw
            }
        }
        return self.send_request("compressed", data, retry, True)
    
    def search_index(self, query, index, tenant, start_time, end_time, technology=None, negative=False, retry=5, is_compressed=True):
        """
        Send a request of type "search_index" that retrieve the index
        query: query to search
        """
        data = {
            "search_index": {
                "query" : query,
                "index" : index,
                "tenant" : tenant,
                "start_time" : start_time,
                "end_time" : end_time,
                "technology" : technology,
                "negative" : negative
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)
    
    def get_page(self, session_token, action, current_page, items_per_page,  current_id = "main", retry=5):
        """
        Send a request of type "get_page" that retrieve the page
        action: action to do (next, previous, first, last)
        search_query: query to search
        data: data to display
        """
        data = {
            "get_page": {
                "session_token" : session_token,
                "action" : action,
                "current_page" : current_page,
                "items_per_page" : items_per_page,
                "current_id" : current_id
            }
        }
        return self.send_request("webhook", data, retry)

    def get_suggestions(self, retry=5):
        """Send requests to receive suggestions for the search query bar"""
        data = {
            "get_suggestions": {}
        }
        return self.send_request("webhook", data, retry)
    
    def get_commands_suggestions(self, commands, retry=5):
        """Send requests to receive suggestions for the search query bar"""
        data = {
            "get_commands_suggestions": {
                "input" : commands
            }
        }
        return self.send_request("webhook", data, retry)

    def get_help(self, retry=5):
        """Send requests to receive help for the search query bar"""
        data = {
            "get_help": {}
        }
        return self.send_request("webhook", data, retry)

    def get_history(self, index_name, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_history": {
                "index_name" : index_name
            }
        }
        return self.send_request("webhook", data, retry)

    def download_data(self, index_name, file_path, retry=5, is_compressed=True):
        """Send requests to receive history for the search query bar"""
        data = {
            "download_data": {
                "index_name": index_name, 
                "file_path": file_path
            }
        }
        return self.send_request("compressed", data, retry, is_compressed=True)

    def get_checksum(self, file, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_checksum": {
                "file": file
            }
        }
        return self.send_request("webhook", data, retry)


    def get_global_configuration(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_global_configuration": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def set_global_configuration(self, session_token, configuration, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "set_global_configuration": {
                "session_token": session_token,
                "configuration": configuration
            }
        }
        return self.send_request("webhook", data, retry)

    def get_privileges(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_privileges": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)

    def set_privileges(self, session_token, privileges, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "set_privileges": {
                "session_token": session_token,
                "privileges": privileges
            }
        }
        return self.send_request("webhook", data, retry)
    
    def sign_in(self, username, password, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "sign_in": {
                "username": username,
                "password": password
            }
        }
        return self.send_request("webhook", data, retry)
    
    def sign_up(self, username, password, email=None, authentication="local", retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "sign_up": {
                "username": username,
                "password": password,
                "email": email, 
                "authentication": authentication
            }
        }
        return self.send_request("webhook", data, retry)
    
    def change_password(self, session_token, username, new_password, retry=5):
        """Send requests to change password of the current user """
        data = {
            "change_password" : {
                "session_token": session_token, 
                "username": username, 
                "new_password": new_password
            }
        }
        return self.send_request("webhook", data, retry)

    def sign_out(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "sign_out": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def check_permissions(self, session_token, permissions_required, retry=5):
        """Send requests to receive history for the search query bar
        By default read only, write should be precised
        ex: permissions: [{"resource":"name", "type":"res_type", "read": True, "write": False}, ...]
        """
        data = {
            "check_permissions": {
                "session_token": session_token,
                "permissions_required": permissions_required, 
            }
        }
        return self.send_request("webhook", data, retry)
    
    def check_username(self, username, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "check_username": {
                "username": username,
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)

    def get_available_indices(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_available_indices": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)

    def get_available_tenants(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_available_tenants": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def get_available_technologies(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_available_technologies": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def get_available_vault_instances(self, session_token, retry=5):
        """Send requests to receive history for the search query bar"""
        data = {
            "get_available_vault_instances": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)

    def reset_research_timeout(self, session_token, retry=5):
        """Send a requests to reset the research timeout for a specific user"""
        data = {
            "reset_research_timeout": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def soar_command(self, session_token, command, id=None, playbook_mode=False, index=None, tenant=None, instance=None, history=None, display=True, retry=5):
        """Send a requests to execute a soar command"""
        data = {
            "soar_command": {
                "session_token": session_token,
                "command": command, 
                "id": id, 
                "playbook_mode": playbook_mode,
                "index": index, 
                "tenant": tenant,
                "vault": instance, 
                "history": history, 
                "display": display
            }
        }
        return self.send_request("webhook", data, retry)
    
    def generate_report(self, session_token, name, widgets, index, tenant, technology, format_report="pdf", portrait=True, start_time=None, end_time=None, page_id=None, retry=5, is_compressed=True):
        """Send a request to the indexsearchmotor to generate a report"""
        data = {
            "generate_report":  {
                "session_token": session_token, 
                "name": name, 
                "widgets": widgets,
                "index": index, 
                "tenant": tenant, 
                "technology": technology, 
                "startTime": start_time, 
                "endTime": end_time, 
                "page_id": page_id,
                "format": format_report,
                "portrait": portrait
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)

    def download_document(self, session_token, doc_id, retry=5, is_compressed=True):
        """Send a request to download document based on the id of the document """
        data = {
            "download_document": {
                "session_token": session_token, 
                "id": doc_id
            }
        }
        return self.send_request("compressed", data, retry, is_compressed)
    
    def soar_load_history(self, session_token, filter=None, retry=5):
        """Send a requests to load the history"""
        data = {
            "soar_load_history": {
                "session_token": session_token,
                "filter": filter
            }
        }
        return self.send_request("webhook", data, retry)
    
    def soar_load_variables(self, session_token, retry=5):
        """Send a requests to load the variables"""
        data = {
            "soar_load_variables": {
                "session_token": session_token
            }
        }
        return self.send_request("webhook", data, retry)
    
    def soar_erase_history(self, session_token, filter=None, retry=5):
        """Send a requests to erase the history"""
        data = {
            "soar_erase_history": {
                "session_token": session_token,
                "filter": filter
            }
        }
        return self.send_request("webhook", data, retry)
    
    def soar_replace_id(self, session_token, origin, final, retry=5):
        """Send a requests to replace an id in the history"""
        data = {
            "soar_replace_id": {
                "session_token": session_token,
                "origin": origin,
                "final": final
            }
        }
        return self.send_request("webhook", data, retry)


###################################################
# 
#   ENCAPSULATION PART
#
##################################################

    def encapsulate_request(self, data, webhook_url, retry=5, is_compressed=False):
        """Encapsulate a request with the necessary fields."""
        return {
            "forwarded_request": {
                "destination": {
                    "host": self.host,
                    "port": self.port,
                    "token": self.token,
                    "webhook_url": webhook_url, 
                    "timeout": self.timeout,
                    "retry": retry,
                    "is_compressed": is_compressed
                },
                "data": data
            }
        }

###################################################
# 
#   SEND REQUESTS PART
#
##################################################



    def send_request(self, webhook_url, data, retry=5, is_compressed=False):
        """Send a request to the webhook server using zstd for compression."""
        time_sleep = 1
        while retry > 0:
            try:
                # TODO check if sufficient with experience
                time_sleep *= 2
                # If the request is forwarded, encapsulate the request
                if self.slave_reverse is not None:
                    # ENCAPSULATE THE REQUEST
                    payload = json.dumps(self.encapsulate_request(data, webhook_url)).encode('utf-8')
                    print("ENCAPSULATED REQUEST")
                    # print(str(payload))
                    # url = self.slave_webhook_url
                    url = f"https://{self.slave_host}:{self.slave_port}/{webhook_url}"
                else:
                    url = f"https://{self.host}:{self.port}/{webhook_url}"
                    payload = json.dumps(data).encode('utf-8')

                # print("URL: " + url)

                # Convert json request to utf-8
                # payload = json.dumps(data).encode('utf-8')
            
                if is_compressed:
                    # Init compressor
                    # Compress and write in file
                    payload = utils.compress_data(payload)
                    self.headers['Content-Encoding'] = utils.COMPRESSION_EXTENSION
                    self.headers['Content-Type'] = 'application/octet-stream'
                else:
                    self.headers['Content-Type'] = 'application/json'

                self.headers['Content-Length'] = str(len(payload))


                # print("POST: "+str(time.time()))
                response = requests.post(
                    url,
                    headers=self.headers,
                    data=payload,
                    timeout=self.timeout,
                    verify=False  # TODO ERASE THIS
                )

                # Treat response
                if response.status_code == 200:
                    if is_compressed and response.headers.get('Content-Encoding') == utils.COMPRESSION_EXTENSION:
                        try:
                            # Decompress response using LZ4
                            start_time_decompressed = time.time()
                            decompressed_data = utils.decompress_data(response.content)  
                            print(f"Decompression time: {time.time() - start_time_decompressed} seconds")
                            if response.headers.get('Content-Type') == 'application/octet-stream':
                                print("Content-Type: application/octet-stream for request")
                                return decompressed_data
                            else:
                                return decompressed_data.decode('utf-8')  # Assumes UTF-8 encoding
                        except Exception as e:
                            print("Error during decompression:", e)
                            return response.text
                    else:
                        return response.text

                elif response.status_code == 404:
                    print("Resource not found (404).")
                    return None
                else:
                    retry -= 1
                    print(f"Request failed: {response.status_code}. Retrying...")
                    time.sleep(time_sleep)  # Wait before retrying
            except Exception as e:
                retry -= 1
                print(f"Error during request: {str(e)}")
                print(traceback.format_exc())
                time.sleep(time_sleep)  # Wait before retrying

        print("Max retries reached. Request failed.")
        return None