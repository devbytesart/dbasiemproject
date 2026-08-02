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
document: siem_commands
"""

import traceback
from typing import Any
from UtilsCrypto import *
import Utils as utils
import UtilsIndexing as utindex
import json, base64, time


##############################################################
###     SIEM PART
##############################################################

def siem_search(self: Any, query: str, index: list, tenant: list, technology: list= [], instance: str=None, start_time: str="2000-01-01 00:00:00", end_time: str="2500-01-01 00:00:00", current_id: str="soar", all_pages: bool=False, token: str=None):
    """
    Search for events in the SIEM system with indexsearchmotor instance
    ex: !search <field>:<value> | !counts by <field> | !order by <field> asc | !render pie by field over count
    params: 
    - instance: str => instance of the SIEM system
    - query: str => query to search
    - index: list => list of indices to search
    - tenant: list => list of tenants to search
    - technology: list => list of technologies to search (None)
    - start_time: str => start time of the search (format: YYYY-MM-DDT HH:MM:SS)
    - end_time: str => end time of the search (format: YYYY-MM-DDT HH:MM:SS)
    - token : str => token of the user if instance vault is not set
    """
    try:
        if self.indexsearchmotor is None or self.authenticator is None:
            return []
        # Print query and parameter
        # print("Query: ", query)
        # print("Indices: " + str(indices))
        # print("Tenants: " + str(tenants))
        # print("Technologies: " + str(technologies))
        # print("Start time: " + start_time)
        # print("End time: " + end_time)
        # Connexion to the authenticator to receive the token
        # print("instance:", str(instance), str(type(instance)))
        #print("vault", str(self.vault), " list", str(self.vault.list_keys()))
        credentials = self.vault.get(instance)
        #print("credentials: ", str(credentials))
        # Get session token
        if instance is None:
            session_token = token
        else:
            session_token = self.authenticator.sign_in(credentials["username"], credentials["password"])
        # Create data
        request = {
            "session_token": session_token,
            "query": query,
            "index": index,
            "tenant": tenant,
            "technology": technology,
            "startTime": start_time,
            "endTime": end_time,
            "current_id": current_id,
            "all_pages": all_pages
        }
        print(str(request))
        # Search
        return self.indexsearchmotor.query_data(request)
        # # get_page
        # res = self.indexsearchmotor.get_page(session_token, "first", 0, 10, current_id, all_pages)
        # print(res)
        # return res
    except:
        raise Exception("Indexsearchmotor instance not found")


def siem_save_log(self:Any, content: dict):
    """
    Set the log of the SIEM system
    The format of the log must be: {data:{parsed:{...}, raw:{...}}}
    params:
    - index: str => index of the log
    - tenant: str => tenant of the log
    - technology: str => technology of the log
    - id: str => id of the log
    """
    try:
        # TODO add format if not respected add parameters
        if self.indexsearchmotor is None or self.authenticator is None:
            raise Exception("Indexsearchmotor or authenticator instance not found")
        # Make researches
        print("Set log.... :" + str(content))
        self.queue.enqueue(json.dumps(content).encode('utf-8'))
        return "Success: Log send to the queue."
    except:
        raise Exception(f"Failed to set log {traceback.format_exc()}")
    

def siem_create_log(self: Any, index: str, tenant: str, technology: str, name: str, params: dict, id: str=None, save: bool=True):
    """ Create a log with information entered in the parameters of the functions 
    params:
    - index: str => index of the log
    - tenant: str => tenant of the log
    - technology: str => technology of the log
    - params: dict => parameters of the log
    - name: str => Name of the log
    - id: str => id of the log
    - save: bool => False or True if the log must be saved or not
    """
    try:
        print("params:" + str(params) + " type:" + str(type(params)))
        params = utils.safe_parse_to_json(params)
        # Create the log
        log = utindex.create_simple_log(index, tenant, technology, name, params, id)
        # Save the log
        if save:
            self.commands["siem_save_log"]["function"](log)
        # self.siem_save_log(log)
        return json.dumps(log)
    except:
        raise Exception(f"Failed to create log {traceback.format_exc()}")


def siem_get_available_indices(self: Any, instance: str=None, token:str=None):
    """
    Get the available indices in the SIEM system
    params:
    - instance: str => instance of the SIEM system
    - token: str => token of the user (must be used if instance empty)
    """
    try:
        if self.indexsearchmotor is None or self.authenticator is None:
            return []
        if instance is None:
            session_token = token
        else:
            # Connexion to the authenticator to receive the token
            credentials = self.vault.get(instance)
            session_token = self.authenticator.sign_in(credentials["username"], credentials["password"])
        # Make researches
        print("Get available indices.... ")
        return self.indexsearchmotor.get_available_indices(session_token)
    except:
        raise Exception("Indexsearchmotor or Authenticator instance not found")
    
def siem_get_available_tenants(self: Any, instance: str=None, token:str=None):
    """
    Get the available tenants in the SIEM system
    params:
    - instance: str => instance of the SIEM system
    - token: str => token of the user (must be used if instance empty)
    """
    try:
        if self.indexsearchmotor is None or self.authenticator is None:
            return []
        if instance is None:
            session_token = token
        else:
            # Connexion to the authenticator to receive the token
            credentials = self.vault.get(instance)
            # Authentication
            session_token = self.authenticator.sign_in(credentials["username"], credentials["password"])
        # Research
        return self.indexsearchmotor.get_available_tenants(session_token)
    except:
        raise Exception("Indexsearchmotor instance not found")
    

def siem_get_available_technologies(self: Any, instance: str=None, token: str=None):
    """
    Get the available technologies in the SIEM system
    params:
    -  instance: str => instance of the vault for index list
    - token: str => token of the user (must be used if instance empty)
    """
    try:
        if self.indexsearchmotor is None or self.authenticator is None:
            return []
        if instance is None:
            session_token = token
        else:
            # Connexion to the authenticator to receive the token
            credentials = self.vault.get(instance)
            # Authentication
            session_token = self.authenticator.sign_in(credentials["username"], credentials["password"])
        # Research
        return self.indexsearchmotor.get_available_technologies(session_token)
    except:
        raise Exception("Indexsearchmotor instance not found")


def siem_generate_report(self:Any, instance:str, name:str, template_name: str, index:list, tenant:list, technology:list="template_report", format_report:str="pdf", portrait:bool=True, save: bool=True, start_time: str="2000-01-01 00:00:00", end_time: str="2500-01-01 00:00:00", current_id: str="soar_report", raw: bool=False):
    # TODO change all the system of template storage index, tenant, ... fix them
    # TODO add token to replace instance
    """ 
    Generate a report based on the template name of the report
    params:
    - instance: str => instance of the vault to access the index that stores the report
    - name: str => name of the report once generated
    - template_name: str => name of the template to get the format of the report
    - index: list => name of the index where to find the template of the report
    - tenant: list => name of the tenant where to find the template of the report
    - technology: list => (template_report by default) name of the technology where to find the template of the report
    - format_report: str => (pdf by default)format of report, pdf, csv ... 
    - portrait: bool => (portrait by default) portrait or landscape format
    - save: bool => (true by default) save or not the report in the index soar
    - start_time: str => (2000-01-01 00:00:00 by default) date of the start for the data research
    - end_time: str => (2500-01-01 00:00:00) date of the end for the data research
    - current_id: str => (soar_report by default) unique id to store the report in memory
    - raw: bool => (false by default) define if soar must return url to download or raw data to in other commands for example
    """
    try:
        # Search widget data
        # TODO add the name of the report in the log
        query = "!search type:report and name:" + template_name
        print("query: ", query)
        res = self.commands["siem_search"]["function"](query, index, tenant, technology, instance, all_pages=True)
        print("siem_generate_report ", str(res))
        # Generate report if data available
        if res != "[]":
            res = json.loads(res)
            if len(res["data"]) > 0:
                report = ""
                # Get widget data from the result
                widgets = json.loads(res.get("data")[0].get("widgets"))
                print("siem_generate_report widgets ", str(widgets))
                # Get session data
                credentials = self.vault.get(instance)
                session_token = self.authenticator.sign_in(credentials["username"], credentials["password"])
                
                # Return report data 
                print(str(session_token))
                print(str(name))
                print(str(index))
                print(str(tenant))
                print(str(technology))
                print(str(format_report))
                print("raw:", str(raw), str(type(raw)))
                print("save:", str(save), str(type(save)))

                results = self.indexsearchmotor.generate_report(session_token, name, widgets, index, tenant, technology, format_report, portrait, start_time, end_time, current_id)
                decoded = results.decode("utf-8").strip('"')
                print("save: ", str(save), str(type(save)))
                if save:
                    print("in save report")
                    params = {
                        "format": format_report,
                        "portrait": portrait,
                        "type": "report",
                        "content": decoded
                    }
                    log = self.commands["siem_create_log"]["function"](index[0], tenant[0], "report", name, params)
                    print("log to save:", str(log))
                    self.queue.enqueue(log.encode("utf-8"))

                # If not raw
                # Return link to report 
                if not raw and save:
                    for attempt in range(3):
                        query = f"!search type:report and name:{name}"
                        res = self.commands["siem_search"]["function"](query, index, tenant, technology, instance)
                        if res != "[]":
                            res = json.loads(res)
                            if len(res["data"]) > 0:
                                # TODO put variable to set the order -1 for last or 0 for last depending on the siem_search order default...
                                report = res.get("data")[-1].get("content")
                        else:
                            time.sleep(attempt * 2)
                    print("siem_generate_report end : ", str(results))
                        
                    return report
                # Else return raw response for email
                return decoded
            else:
                self.logger.log("error", f"Failed to generate report with empty data {traceback.format_exc()}")
                raise
        else:
            self.logger.log("error", f"Failed to load report template {traceback.format_exc()}")
            raise
    except:
        self.logger.log("error", f"Failed to generate report {traceback.format_exc()}")
        raise

def siem_modify_log(self:Any, instance:str, index:str, tenant:str, technology:str, id:str, data:str):
    """
    Retrieve original logs and update data
    params:
    - instance: str => instance of vault to get the log
    - index: str => index where to find and save the data
    - tenant: str => tenant where to find and save the data
    - technology: str => technology where to find and save the data
    - id: str => id of the log to update
    - data: str => new json to update in the log
    """
    try:
        # Retrieve the log
        print(index, tenant, technology)
        query = "!search id:" + id
        print("query: ", query)
        res = self.commands["siem_search"]["function"](query, [index], [tenant], [technology], instance, all_pages=True)
        # Update the log
        print("before res:" + str(res))
        if res != "[]":
            res = json.loads(res)
            print("after json loads")
            if len(res["data"]) > 0:
                # Load new data
                data = json.loads(data)
                print("data apres:" + str(type(res["data"][0])))
                for k,v in data.items():
                    res["data"][0][k] = v
                # Print it just for test
                print("siem_modify result",str(res))
                # Save the log
                self.commands["siem_create_log"]["function"](index, tenant, technology, res["data"][0].get("name","unnamed"),res["data"][0], id)
                # self.commands["siem_save_log"]["function"](res["data"][0])
        # TODO check if res is required
        return res
    except:
        self.logger.log("error", f"Failed to update log: {traceback.format_exc()}")
        raise