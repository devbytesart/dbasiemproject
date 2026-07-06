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
document: soar_commands
"""

import traceback
from typing import Any
from UtilsCrypto import *
import UtilsIndexing as utindex
import Utils as utils
import json
import time
from datetime import datetime, timezone
import random
import base64
import copy


##############################################################
###     SOAR PART
##############################################################

def soar_test(self: Any):
    """
    Test the SOAR instance
    params:
    - soar: str => SOAR instance
    """
    try:
        print("test soar_test:", str(self.context))
        # print(str(self.commands))  # <- ici tu accèdes bien à self.commands
        print("queue:", str(self.queue.get_size()))
        return "Ok"
    except:
        raise Exception("SOAR instance not found")
    

def soar_reload_functions(self: Any):
    """
    Reload the functions of the SOAR instance
    params: None
    """
    try:
        self.reload()
        return "Functions reloaded"
    except:
        raise Exception("SOAR instance not found")
        

def soar_save_context(self: Any, name: str, index: str, tenant: str, playbook: bool=False, filter: dict=None):
    """
    Save the history of the SOAR instance
    params:
    - name: str => name of the playbook
    - filter: str => filter of the playbook
    """
    try:
        # TODO manager filter
        if filter:
            print("filter exists")
        else:
            # TODO add several playbook data
            # Check if id of playbook in the variables
            _siem_id = None
            if "_siem_id" in self.context["variables"]:
                _siem_id = self.context["variables"]["_siem_id"]
            print("soar_save_context", _siem_id)
            context = {"context": copy.deepcopy(self.context)}
            context_type = "context"
            if playbook:
                context_type = "playbook"
            log = {"data":{"parsed":{
                    "id": (str(time.time()) + str(random.random())).replace(".","") if not _siem_id else _siem_id,
                    "name": name,
                    "index": index,
                    "type": context_type,
                    "tenant": tenant,
                    "technology": "soar",
                    "parserReceivedTime": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "siem_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
                },"raw": base64.b64encode(json.dumps(context).encode('utf-8')).decode('utf-8')}}
            log["data"]["parsed"].update(context)
            if self.context["variables"]["_siem_id"] != "ERROR":
                self.queue.enqueue(json.dumps(log).encode("utf-8"))
                # Wait for the logindexer to save the log
                time.sleep(2)
                print("save queue:", str(self.queue.get_size()))
        return "History saved"
    except:
        raise Exception("Failed to save history")
    

def soar_load_context(self: Any, name: str, index: list, tenant: list, playbook=False, instance: str=None, token: str=None):
    """
    Load the history of the SOAR instance
    params:
    - name: str => name of the playbook
    - tenant: str => tenant of the playbook
    - token: str (None) => token if instance is None
    - instance: str (None) => instance vault to use to have the permissions of the instance 
    """
    # TODO if result == [] and not {"type": "table", ... } -> no right to save the context
    # TODO maybe change the return of search and manage errors in search
    try:
        # Change empty value
        # Check name
        if name is None or name == "" or name == "None" or name == "none" or name == "undefined":
            name = "Main"
        print("New Name: ", str(name))
        # index null
        if index is None or index == "" or index == "None" or index == "none" or index == "undefined":
            index = ["soar"]
        # Tenant null
        if tenant is None or tenant == "" or tenant == "None" or index == "none" or tenant == "undefined":
            tenant = ["soar"]
        # TODO manager filter
        print("soar_load_context name:", str(name))
        print("soar_load_context index:", str(index))
        print("soar_load_context tenant:", str(tenant))
        print("soar_load_context instance:", str(instance))
        # If playbook load playbook
        if playbook:
            query = "!search type:playbook and name:" + name
        # Else load context
        else:
            query = "!search type:context and name:" + name 
        print("soar_load_context query:", query)
        # Transform value in list if required
        if not isinstance(index, list):
            index = [index]
        if not isinstance(tenant, list):
            tenant = [tenant]
        if instance is None:
            res = self.commands["siem_search"]["function"](query, index, tenant, ["soar"], None, "2020-01-01 00:00:00", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), token=token)
        else:
            res = self.commands["siem_search"]["function"](query, index, tenant, ["soar"], instance, "2020-01-01 00:00:00", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        print("soar_load_context res:", str(res))
        # If any results user has the right to load the context
        if res != [] and res != "[]":
            temp = json.loads(res).get("data")
            print("soar_load_context temp:", str(temp))
            if len(temp) > 0:
                self.context.clear()
                self.context.update(temp[-1].get("context", {}))
            else:
                self.commands["soar_erase_context"]["function"](-1)
            print("soar_load_context not null context:", str(self.context))
        # User has no right to load the context
        else:
            self.commands["soar_erase_context"]["function"](-1)
            self.context["variables"]["_siem_id"] = "ERROR"
        return "History loaded"
    except:
        self.logger.log("error", f"Failed to load history {traceback.format_exc()}")
        raise Exception("Failed to load history")


def soar_reset_context(self:Any, reset_next_id = True):
    """ Reset the history answer of the SOAR instance
    params:
    - reset_next_id: bool => reset the next_id
    """
    try:
        print("reset history answer")
        for i in self.context["history"]:
            i["answer"] = []
            i["status"] = "pending"
        if reset_next_id:
            self.context["variables"]["next_id"] = 0
        return "History answer reset"
    except:
        raise Exception("Failed to reset history answer")


def soar_list_playbook(self:Any, instance:str, index: list, tenant:list):
    """ List the playbook on the indexsearchmotor in the index and tenant 
    params:
    - index: list => list of index
    - tenant: list => list of tenant
    """
    try:
        query = "!search type:playbook"
        res = self.commands["siem_search"]["function"](instance, query, index, tenant, ["soar"], "2020-01-01 00:00:00", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        print("res:", str(res))
        result = []
        for r in json.loads(res).get("data"):
            result.append(r.get("name", None))
        print("res:", str(res))
        return result
        # TODO to finish
    except:
        raise Exception("Failed to load history")    


def soar_stop_execution(self: Any):
    """Stop the execution of the current playbook/context
    params: None
    """
    try:
        # Set the variable _running to False
        self.context["variables"]["_running"] = False
        return "Execution stopped"
    except:
        raise Exception("Failed to stop execution")
    
def soar_start_execution(self: Any):
    """Start the execution of the current playbook/context
    params: None
    """
    try:
        # Set the variable _running to True
        self.context["variables"]["_running"] = True
        return "Execution started"
    except:
        raise Exception("Failed to start execution")


def soar_play_context(self: Any, name: str, instance: str, index: str, tenant: str, playbook: bool=False, add_context: bool=True, context_name: str=""):
    """Play the playbook in background
    params:
    - name: str => name of the playbook
    - instance: str => instance of the vault
    - index: str => index where is the playbook
    - tenant: str => tenant where is the playbook
    - playbook: bool => if True, play the playbook, if False, play the context
    - add_context: bool => if True, add the context to the history, if False, don't add the context to the history
    """
    try:
        print("soar_play_history self id:", id(self))
        print("soar play history before context name:", name, " ", instance, " ", str(index), " ", str(tenant))
        print("soar play history after context name", name, " ", instance, " ", str(index), " ", str(tenant))
        print("soar context in soar_play_context:", str(self.context))
        print("Play all the playbook")
        # Plan for incomplete
        incomplete = False
        error_data = ""
        if playbook:
            # siem_id = utindex.create_random_id()
            self.context["variables"]["_siem_id"] = utindex.create_random_id()
            # self.context["variables"]["_siem_id"] = siem_id
            if context_name is None or context_name == "":
                name = name + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            else:
                name = context_name
        else:
            if context_name:
                name = context_name
        self.context["variables"]["_running"] = True
        # else:
            # siem_id = self.context["variables"]["_siem_id"]
        # Launch loop
        print("before loop")
        while self.context["variables"].get("_running", True):
            print("In loop")
            current_id = self.context["variables"].get("next_id", 0) 
            print("current_id:", str(current_id))
            entry = next((e for e in self.context["history"] if e.get("id") == current_id), None)
            print("entry:", str(entry))
            if not entry:
                print(f"No entry found with id {current_id}, stopping.")
                self.context["variables"]["_running"] = False
                break
            if entry.get("status") in ["success", "failed"]:
                print(f"Entry with id {current_id} has status '{entry.get('status')}', stopping.")
                self.context["variables"]["_running"] = False
                break
            print(f"Replaying command with id {entry['id']}")
            try:
                params_updated = {
                    key: utils.replace_var(value, self.context["history"], self.context["variables"]) if isinstance(value, str) else value
                    for key, value in entry["params"].items()
                }
                result = self.commands[entry["name"]]["function"](**params_updated)
                status = "success"
            except Exception as e:
                print("soar_play_context error:", str(e), traceback.format_exc())
                error_data = json.loads(str(e))
                if error_data.get("error") == "INCOMPLETE":
                    self.logger.log("warning", "soar_play_context Form is incomplete: a required field is missing.")
                    result = error_data
                    status = "pending"
                    incomplete = True
                    # Stop the execution
                    self.context["variables"]["_running"] = False
                else:
                    self.logger.log("error", f"Error during function execution {entry}")
                    result = "None"
                    status = "failed"
            # Update the next_entry if next id unchanged
            index_entry = next((i for i, ent in enumerate(self.context["history"]) if ent.get("id") == current_id), None)
            # Test if entry changed
            if self.context["variables"]["next_id"] == current_id and index_entry is not None and index_entry + 1 < len(self.context["history"]):
                print("soar_play_context entry + 1")
                next_entry = self.context["history"][index_entry + 1]
                self.context["variables"]["next_id"] = int(next_entry.get("id"))
            else:
                print("entry not changed")
            print(f"soar_play_context Updated next_id to {self.context['variables']['next_id']}")
            # Update historic
            # TODO add and incomplete if not required to add the log in the context
            if add_context:
                print("soar_play_context add context : ", str(self.context))
                print("soar_play_context add context name : ", str(name))
                utindex.create_soar_history_entry(
                        entry["id"], "soar", entry["name"], entry["params"], result, status, self.context["history"]
                )
                content = {"type": "context", "context": self.context}
                # log = utindex.create_simple_log(index, tenant, "soar", name, content, siem_id)
                log = utindex.create_simple_log(index, tenant, "soar", name, content, self.context["variables"]["_siem_id"])
                self.queue.enqueue(json.dumps(log).encode("utf-8"))
                time.sleep(1)
        # Incomplete ? 
        if incomplete:
            print("soar_play_context Incomplete: " + str(error_data))
            raise Exception(json.dumps(error_data))
        print("history:", str(self.context["history"]))
        return "End of Playbook"
    except Exception as e:
        print("soar_play_context Error: " + str(e))
        error_data = json.loads(str(e))
        if error_data.get("error") == "INCOMPLETE":
            self.logger.log("warning", "soar_play_context Form is incomplete: a required field is missing.")
            raise Exception(json.dumps(error_data))
        else:
            self.logger.log("error", f"Failed to play context {traceback.format_exc()}")
            raise Exception("Failed to launch playbook")


def soar_play_playbook(self: Any, name: str, instance: str, index: str, tenant: str, var_name:str="None"):
    """Play the a sub playbook in background for the current context
    params: 
    - name: str => name of the playbook
    - instance: str => instance vault with the credentials for the playbook
    - index: str => index of the playbook
    - tenant: str => tenant of the playbook
    - var_name: str = >name of the variable to store the context (random if empty)
    """
    try:
        print("soar_play_playbook context:", str(self.context))
        if var_name == "None":
            var_name = name + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            # Search this function in current self.context and change params
            # index_entry = next((i for i, ent in enumerate(self.context["history"]) if ent.get("id") == task_id), None)
            # if index_entry is not None:
            #     self.context["history"][index_entry]["params"]["var_name"] = var_name
        incomplete = False
        with self._temporary_context():
            # Load context if already exist
            self.commands["soar_load_context"]["function"](var_name, instance, index, tenant)
            is_playbook = False
            # We don't change the _running status of the context
            # Load the playbook if context does not exist
            if self.context["history"] == []:
                print("soar_play_playbook context does not exist2,load playbook")
                self.commands["soar_load_context"]["function"](name, instance, index, tenant, True)
                is_playbook = True
            # Set _running to True to play the context and the playbook
            self.context["variables"]["_running"] = True
            # Launch the play_context
            print("soar_play_playbook temporary context:", str(self.context))
            try:
                self.commands["soar_play_context"]["function"](name, instance, index, tenant, is_playbook, True, var_name)  
            except Exception as e:
                # if str(e) == "INCOMPLETE":
                #     incomplete = True
                print("soar_play_playbook in temp context Error: " + str(e))
                error_data = json.loads(str(e))
                if error_data.get("error") == "INCOMPLETE":
                    incomplete = True
            new_context = copy.deepcopy(self.context)
            print("soar_play_playbook new_context:", str(new_context))
        # Return the url to find
        # TODO erase soar_url and use siem_linktype/url
        to_return = {"soar_url": "/soar?index=" + index + "&tenant=" + tenant + "&vault=" + instance + "&history=" + var_name}
        self.context.update({var_name: new_context})
        if incomplete:
            err =  {"error": "INCOMPLETE"}
            err.update(to_return)
            raise Exception(json.dumps(err))
        print("soar_play_playbook context:", str(self.context))
        return to_return
    except Exception as e:
        # if str(e) == "INCOMPLETE":
        print("soar_play_playbook incomplete:", str(e))
        error_data = json.loads(str(e))
        if error_data.get("error") == "INCOMPLETE":
            self.logger.log("warning", "soar_play_playbook Form is incomplete: a required field is missing.")
            raise Exception(json.dumps(error_data))
        else:
            self.logger.log("error", f"Failed to play playbook {traceback.format_exc()}")
            raise Exception("Failed to create context")


def soar_set_context(self:Any, name:str, index: str, tenant:str,  command: str, params: dict, author:str, instance: str=None, command_id: int=None, playbook: bool=False, display=True, token=None):
    """ Add a command to a playbook or a context
    params:
    - name: str => name of the context/playbook
    - instance: str => instance name in the vault to get the credentials
    - index: str => index of the playboook/context
    - tenant: str => tenant of the playbook/context
    - command: str => command name to add/modify in the playbook/context
    - params: dict => parameters of the command
    - author: str => author of the command
    - command_id: int => id of the command in the playbook/context
    - playbook: bool => if True, the command is added to a playbook, else to a context
    - context_name: str => name of the context/playbook
    - display: bool => if display the result in the playbook
    - token: str(None) => Token of the user is instance is empty
    """
    try:

        # TODO add author to the context
        # TODO check if variables are added to the context
        # Check instance
        if instance is None or instance == "" or instance == "None" or instance == "undefined":
            instance = None
        # Check name
        if name is None or name == "" or name == "None" or name == "none" or name == "undefined":
            name = "Main"
        print("New Name: ", str(name))
        # index null
        if index is None or index == "" or index == "None" or index == "none" or index == "undefined":
            index = ["soar"]
        # Tenant null
        if tenant is None or tenant == "" or tenant == "None" or index == "none" or tenant == "undefined":
            tenant = ["soar"]
        # Load context/playbook
        ## If playbook
        if playbook:
            # TODO change token here too
            self.commands["soar_load_context"]["function"](name, instance, index, tenant, True)
        ## else context
        else:
            if token is not None:
                self.commands["soar_load_context"]["function"](name, index, tenant, token=token)
            else:
                self.commands["soar_load_context"]["function"](name, index, tenant, instance=instance)
        # print("soar_set_context context:", str(self.context))
        ## If playbook:
        # TODO find a more clean way to do this
        print("soar_set_context command:", str(command), str(playbook))
        if (playbook and not command.startswith("soar_play_context") \
            and not command.startswith("soar_reset_context") \
            and not command.startswith("soar_erase_context")) \
            or command.startswith("soar_load_context"):
            print("soar_set_context playbook")
            result = []
            status = "pending"
        ## Else if context, execute function
        else:
            try:
                params_updated = {
                    key: utils.replace_var(value, self.context["history"], self.context["variables"]) if isinstance(value, str) else value
                    for key, value in params.items()
                }
                # Launch command
                result = self.commands[command]["function"](**params_updated)
                status = "success"
            except Exception as e:
                print("soar_set_context exception:", str(e))
                error_data = json.loads(str(e))
                if error_data.get("error") == "INCOMPLETE":
                # if str(e) == "INCOMPLETE":
                    self.logger.log("warning", "soar _set_context Form is incomplete: a required field is missing.")
                    result = error_data
                    status = "pending"
                    # Stop the execution
                    self.context["variables"]["_running"] = False
                else:
                    self.logger.log("error", f"Error during function execution {command}")
                    result = f"Error during function execution {command}"
                    status = "failed"

        # Search element with the same id 
        print("soar_set_context command_id:", str(command_id))
        element_index = next((i for i, item in enumerate(self.context["history"]) if item['id'] == command_id), None)
        print("element_index:", str(element_index))

        # TODO test if it works
        # if element_index is not None and self.context["variables"]["_running"] == True:
        if element_index is not None:
            print("Element found at index :", str(element_index))
            if display:
                # Add entry to existing
                context_entry = utindex.create_soar_history_entry(
                    command_id, "soar", command, params, result, status, self.context["history"]
                )
        elif self.context["variables"]["_running"] == False:
        # else:
            # Add a new entry
            if display:
                print("Element not found, add new entry")
                context_entry = utindex.create_soar_history_entry(
                    len(self.context["history"]), "soar", command, params, result, status, self.context["history"]
                )
                print("context_entry:", str(context_entry))
                # self.context["history"].append(context_entry)
            print("self.context:", str(self.context))
        # Save context/playbook
        ## if playbook 
        print("SOAR_BEFORE_SAVE_CONTEXT: ", str(self.context))
        if (playbook and command.startswith("soar_play_context")) or command.startswith("soar_load_context"):
            print("soar_set_context in playbook and soar_play_context command")
            # We don't save the context or the playbook
            return self.context
        elif playbook:
            print("soar_set_context in playbook")
            self.commands["soar_save_context"]["function"](name , index, tenant, True)
        ## else context
        else:
            print("soar_set_context in else context")
            self.commands["soar_save_context"]["function"](name, index, tenant)
        print("soar_set_context: ", str(self.context), str(type(self.context)))
        return self.context
    except:
        self.logger.log("error", f"Failed to set context {traceback.format_exc()}")
        raise Exception("Failed to add task to playbook")


def soar_set_var(self:Any, name:str, value:str):
    """ Set a variable in the soar instance 
    params:
    - name: str => name of the variable
    - value: str => value of the variable
    """
    try:
        self.context["variables"][name] = value
        self.logger.log("info", f"Variable {name} set to {value}")
        return {name: value}
    except:
        raise Exception("Failed to set variable")

def soar_get_var(self:Any, name:str):
    """ Get a variable in the soar instance
    params:
    - name: str => name of the variable
    """
    try:
        return self.context["variables"][name]
    except:
        raise Exception("Failed to get variable")
    
def soar_list_var(self:Any):
    """ List the variables in the soar
    params: None
    """
    try:
        return copy.deepcopy(self.context["variables"])
    except:
        raise Exception("Failed to list vavariables")
    
def soar_erase_var(self:Any, name:str):
    """ Erase a variable in the soar instance
    params:
    - name: str => name of the variable
    """
    try:
        del self.context["variables"][name]
        self.logger.log("info", f"Variable {name} erased")
        return {name: None}
    except:
        raise Exception("Failed to erase variable")
    
def soar_erase_all_var(self: Any):
    """ Erase all the variables in the soar instance
    params: None
    """
    try:
        self.context["variables"].clear()
        self.variables["next_id"] = 0
        self.variables["_running"] = False
        self.logger.log("info", f"All variables erased")
        return "All variables erased"
    except:
        raise Exception("Failed to erase all variables")
    

def soar_set_next_id(self:Any, id:int):
    """ Set the next id for the soar instance
    params:
    - id: int => id of the next entry
    """
    try:
        self.context["variables"]["next_id"] = int(id)
        self.logger.log("info", f"Next id set to {id}")
        return {"next_id": id}
    except:
        raise Exception("Failed to set next id")
    
def soar_get_next_id(self:Any):
    """ Get the next id for the soar instance
    params: None
    """
    try:
        return self.context["variables"]["next_id"]
    except:
        raise Exception("Failed to get next id")
    

def soar_erase_context(self: Any, id: int = -1):
    """Erase the context of the soar instance.
    Parameters:
    - id : int => ID of the context entry to erase. If -1, erase all context.
    """
    try:
        if id != -1:
            history = self.context.get("history", [])
            removed = False
            # Path reversed to avoid index problem
            for i in reversed(range(len(history))):
                if history[i].get("id") == id:
                    del history[i]
                    removed = True
            if removed:
                self.logger.log("info", f"Context {id} erased")
            else:
                self.logger.log("warning", f"Context {id} not found")
        else:
            siem_id = utindex.create_random_id()
            if "variables" in self.context and "_siem_id" in self.context["variables"]:
                siem_id = self.context["variables"].get("_siem_id", siem_id)
            self.context.clear()
            self.context["history"] = []
            self.context["variables"] = {}
            self.context["variables"].update({"next_id": 0})
            self.context["variables"].update({"_running": False})
            self.context["variables"].update({"_siem_id": siem_id})
            self.logger.log("info", "Context cleared")            
            self.logger.log("info", "All context erased")

        return "Context erased"
    except Exception as e:
        raise Exception(f"Failed to erase context: {str(e)}")
    

def soar_swap_ids(self:Any, old_id:int, new_id:int):
    """ Replace the id of the context of the soar instance
    params:
    - old_id: int => id of the context to replace
    - new_id: int => new id of the context
    """
    try:
        # Swap the ids of the origin on temporary id
        for entry in self.context["history"]:
            if entry["id"] == old_id:
                entry["id"] = -1
        # Swap the ids of the final on origin id
        for entry in self.context["history"]:
            if entry["id"] == new_id:
                entry["id"] = old_id
        # Swap the ids of the temporary to new id
        for entry in self.context["history"]:
            if entry["id"] == -1:
                entry["id"] = new_id
        self.logger.log("info", f"Context {id} replaced by {new_id}")
        return {"old_id": old_id, "new_id": new_id}
    except:
        raise Exception("Failed to swap id")
    

def soar_set_id(self:Any, id:int, new_id: int):
    """ Change the id in the historic of the context to a new id
    params:
    - id: int => id of the context to replace
    - new_id: int => new id of the context
    """
    try:
        for entry in self.context["history"]:
            if entry["id"] == id:
                entry["id"] = new_id
        self.logger.log("info", f"Context {id} replaced by {new_id}")
        return {"old_id": id, "new_id": new_id}
    except:
        self.logger.log("error", f"Failed to set id {traceback.format_exc()}")
        raise Exception("Failed to set id")


def soar_formular(self: Any, question: str, type: str="str", answer: str = "", completed: bool = False, mandatory: bool = True):
    """
    Submit a form using only one question
    Raises:
        Exception with JSON if a mandatory field is missing or empty, or if the form is not completed.
    params:
    - question: str => question of the formular 
    - answer: str => answer provided by the user
    - type: str => type of answer waited
    - completed: bool => defined if the formular has been completed or not by the user. If completed, return success else incomplete error.
    - mandatory : bool => define the question as mandatory or not
    """
    try:
        result = {
            "soar_form": {
                "question": question,
                "answer": answer,
                "type": type,
                "mandatory": mandatory
            }
        }

        if mandatory and not str(answer).strip():
            raise Exception(json.dumps({"error": "INCOMPLETE", "result": result}))

        if not completed:
            raise Exception(json.dumps({"error": "INCOMPLETE", "result": result}))

        self.logger.log("info", f"Form submitted successfully: {result}")
        return result

    except Exception as e:
        try:
            error_data = json.loads(str(e))
            if error_data.get("error") == "INCOMPLETE":
                self.logger.log("warning", f"soar_formular Form is incomplete: {error_data}")
                raise Exception(json.dumps(error_data))
        except json.JSONDecodeError:
            self.logger.log("error", f"Unexpected error during form submission: {str(e)} - {traceback.format_exc()}")
            raise


def soar_conditions(self: Any, conditions: str, default: int):
    # TODO add a else params for others possibilities
    """
    Evaluate the conditions with the format "condition1:next_id1,condition2:next_id2"
    params:
    - conditions: str => condition to evaluate (condition1:next_id1,condition2:next_id2)
    - default: int => default next_id if conditions are not respected
    """
    variables = self.context["variables"]

    print("conditions: " + str(conditions))
    for cond_val in conditions.split(","):
        condition, value = cond_val.split(":")

        # Clean spaces
        condition = condition.strip()
        value = value.strip()
        try:
            # Evaluate conditions with using variables
            if eval(condition, {}, variables):
                self.context["variables"]["next_id"] = int(value)
                print(f"Condition succeeded: '{condition}', next_id defined at {value}")
                return "condition: " + value
            else:
                self.context["variables"]["next_id"] = int(default)
                return "default : "+ value
        except Exception as e:
            print(f"Error during the evaluation of the conditions '{condition} {traceback.format_exc()}': {e}")
            raise

def soar_import_context(self:Any, imported:str):
    """
    Import a context or a playbook and save it in the logs
    params:
    - context: dict => context to import and save in the siem
    """
    try:
        print("soar_import_self_context:", str(self.context))
        decoded_context = json.loads(base64.b64decode(imported).decode("utf-8"))
        print("soar_import;", str(base64.b64decode(imported).decode("utf-8")))
        self.context.clear()
        self.context["history"] = decoded_context["history"]
        self.context["variables"] = decoded_context["variables"]
        return "Context imported with success"
    except:
        self.logger.log("error", f"Failed to import SOAR Context {traceback.format_exc()}")
        raise 