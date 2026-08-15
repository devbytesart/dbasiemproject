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
document: SOAR
"""

from ServiceBase import *
from Webhook import *
from CMDHandler import *
from WebRequester import *
from Configurator import *
from Logger import *
from TaskManager import *
from ParameterLoader import *
from UtilsCrypto import *
from SOARCommandLoader import *
from SOARVault import *
import Utils as utils
import UtilsIndexing as utindex
import traceback
import threading
import time
import inspect
import shlex
import json
import re


class SOAR(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            self.cmdhandler = CMDHandler({
                "configure":self.handle_set_config, 
                "configuration":self.configurator.get_config,
                "retrieve_logs": self.handle_retrieve_logs,
                "retrieve_monitoring": self.handle_retrieve_monitoring,
                "retrieve_mapping": self.handle_retrieve_mapping,
                "shutdown": self.handle_shutdown,
                "soar_command": self.handle_soar_command,
                "soar_add_command": self.handle_add_command,
                "get_commands_suggestions": self.handle_suggestions,
                "soar_load_history": self.handle_load_history,
                "soar_erase_history": self.handle_erase_history,
                # "soar_load_variables": self.handle_load_variables,
                "get_available_vault_instances": self.handle_get_available_vault_instances,
                "get_help": self.handle_get_help
            })
            # Create Encryption
            if not os.path.exists(self.encryption_key_path) and not os.path.exists(self.encryption_iv_path):
                try:
                    utils.create_folders(self.encryption_key_path)
                    Encryption.generate_key(self.encryption_key_path)
                    Encryption.generate_iv(self.encryption_iv_path)
                except:
                    self.logger.log("error", f"Error while generating encryption keys {traceback.format_exc()}")
            self.encryptor = Encryption(self.encryption_algorithm, self.encryption_key_path, self.encryption_iv_path)
            # Integration Vault
            self.integration_vault = SOARVault(self.integration_vault_path, self.logger, self.encryption_algorithm, self.encryption_key_path, self.encryption_iv_path)
            # Build functions
            self.builtin_commands = "SOARBuiltinCommands"
            self.command_loader = None
            # self.commands = {}
            # self.history = []
            self.variables = {"next_id": 0}
            self.running = True
            self._start_microservices()
        except:
            self.logger.log("error", "Error while initializing the SOAR", traceback.format_exc())


    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
        self.index = []
        # LOGGER
        self.monitoring_log_level = self.config["logger"]["log_level"]
        self.monitoring_log_path = self.config["logger"]["log_path"]
        self.monitoring_max_queue_size = self.config["logger"]["max_queue_size"]
        self.monitoring_max_file = self.config["logger"]["max_file"]
        self.monitoring_max_file_size = self.config["logger"]["max_file_size"]
        self.monitoring_enable_print = utils.convert_param_type(self.config["logger"]["enable_print"], bool)
        self.monitoring_enable_file = utils.convert_param_type(self.config["logger"]["enable_file"], bool)
        self.monitoring_enable_queue = utils.convert_param_type(self.config["logger"]["enable_queue"], bool)
        # WEBHOOK
        self.webhook_host = self.config["webhook"]["host"]
        self.webhook_port = self.config["webhook"]["port"]
        self.webhook_token = self.config["webhook"]["auth_token"]
        self.webhook_certfile = self.config["webhook"]["certs"]["certfile"]
        self.webhook_keyfile = self.config["webhook"]["certs"]["keyfile"]
        self.max_queue_size = self.config["queue"]["max_queue_size"]  
        # ENCRYPTION
        self.encryption_algorithm = self.config["encryption"]["algorithm"]
        self.encryption_key_path = self.config["encryption"]["key_path"]
        self.encryption_iv_path = self.config["encryption"]["iv_path"]
        # INTEGRATION 
        self.integration_vault_path = self.config["integration"]["vault_path"]
        ## WEBREQUESTER
        self.proxies = self.config["webrequester"]["proxy"]
        self.timeout = self.config["webrequester"]["timeout"]
        self.slave_reverse = self.config["webrequester"].get("slave_reverse") 
        # QUEUE
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        self.backup_file = self.config["queue"]["backup_file"]
        self.max_backup_file = self.config["queue"]["max_backup_file"]
        self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
        # STORAGE
        self.storage_path = self.config["storage"]["path"]
        self.max_file_size = self.config["storage"]["max_file_size"]
        # self.index_name = self.config["storage"]["index_name"]
        # self.index_size = self.config["storage"]["index_size"]
        # self.index_saving_frequency = self.config["storage"]["index_saving_frequency"]
        self.max_threads = self.config["storage"]["max_threads"] 
        # COMMANDS 
        self.command_loader_folder = self.config["commands"]["path"]
        # AUTHENTICATION
        # TODO table of authenticators
        self.authenticatorsReq = None
        if "authenticator" in self.config and "id" in self.config["authenticator"]:
            self.authenticators_id = self.config["authenticator"]["id"]
            self.authenticators_host = self.config["authenticator"]["host"]
            self.authenticators_port = self.config["authenticator"]["port"]
            self.authenticators_auth_token = self.config["authenticator"]["auth_token"]
            self.authenticatorsReq = WebRequester(self.authenticators_host, self.authenticators_port, self.authenticators_auth_token) 
        # INDEX SEARCH MOTOR
        self.indexsearchmotorReq = None
        if "indexsearchmotor" in self.config and "id" in self.config["indexsearchmotor"]:
            self.indexsearchmotor_id = self.config["indexsearchmotor"]["id"]
            self.indexsearchmotor_host = self.config["indexsearchmotor"]["host"]
            self.indexsearchmotor_port = self.config["indexsearchmotor"]["port"]
            self.indexsearchmotor_auth_token = self.config["indexsearchmotor"]["auth_token"]
            self.indexsearchmotorReq = WebRequester(self.indexsearchmotor_host, self.indexsearchmotor_port, self.indexsearchmotor_auth_token)
            # TASK MANAGER index, tenant
            self.task_index = self.config["task"]["index"]
            self.task_tenant = self.config["task"]["tenant"]
            self.task_technology = self.config["task"]["technology"]
            self.task_creds = self.config["task"]["credentials"]

    def handle_shutdown(self):
        return self._stop_microservices()
    
    def _load_stats(self):
        # TODO load stats from storage
        pass

    def handle_retrieve_monitoring(self, data):
        # TODO maybe factorise this function in the base class ?
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def handle_retrieve_logs(self, size):
        # TODO factorise this function in the base class ?
        try:
            index = size.get("index", None)
            # Add index in the SOAR to limit the list of index available
            if index and index not in self.index:
                self.index.append(index)
            # Using bytearray to improve performance
            elements = bytearray(b"[") 
            size = int(size["size"])
            elements_count = 0
            for _ in range(size):
                dequeued_element = self.queue_manager.dequeue(1)
                if not dequeued_element:
                    break
                # Add , if not first element
                if elements_count > 0:
                    elements.extend(b",") 
                # Add current element
                elements.extend(dequeued_element)
                elements_count += 1
            if elements_count > 0:
                elements.extend(b"]")  # Close the array
                return bytes(elements)  # Return as bytes
            else:
                return None
        except Exception as e:
            self.logger.log("error",f"Error while retrieving logs: {traceback.format_exc()}")
            # TODO: Reinsert data in queue in case of error
            return None

    def _stop_microservices(self):
        try:
            self.command_loader = []
            # self.history = []
            # self.variables = {"next_id" : 0}
            self.webhook.stop()
            self.running = False
            self.run_thread.stop()
            self.run_thread.join()
            return True
        except:
            self.logger.log("error", "Error while stopping the webhook", traceback.format_exc())
            return False
        
    def _start_microservices(self):
        try:
            # self.load_function_from_folder(self.builtin_commands)
            # self.load_function_from_folder(self.command_loader_folder)
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.max_backup_file, self.max_backup_file_size)
            self.command_loader = CommandLoader(self.builtin_commands, self.command_loader_folder, self.integration_vault, self.logger, self.queue_manager, self.authenticatorsReq, self.indexsearchmotorReq, self.task_creds, self.task_index, self.task_tenant, self.task_technology)
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            # self.task_manager = TaskManager(self.storage_path, self.logger, self.max_threads)
            self.running = True
            self.run_thread = threading.Thread(target=self.run)
            self.run_thread.start()
            return True
        except:
            self.logger.log("error", "Error while starting the webhook", traceback.format_exc())
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
        
    def handle_set_config(self, data):
        """Handle set configuration request"""
        # TODO implement this part for microservices
        try:
            self.configurator.set_config(data)
            self.load_configuration()
            return self._restart_microservices()
        except:
            self.logger.log("error", f"Failed to set configuration: {traceback.format_exc()}")
            return False


    def handle_soar_command(self, data):
        try:
            return self.command_loader.execute_commands_soar(data)
        except:
            self.logger.log("error", f"Failed to execute commands: {traceback.format_exc()}")
            return []


    def handle_add_command(self, data):
        """Handle add task request"""
        # TODO implement this part for microservices
        try:
            return self.command_loader.set_command(data)
        except:
            self.logger.log("error", f"Failed to add command: {traceback.format_exc()}")
            return False


    def handle_retrieve_mapping(self, data):
        """Handle retrieve mapping request"""
        # TODO change the mapping method
        return {
           "fields": {
                "id": {
                    "type": "string",
                }, 
                "technology": {
                    "type" : ["keyword"]
                }, 
                "tenant": {
                    "type" : ["keyword"]
                },
                "index": {
                    "type" : ["keyword"]
                },
                "name": {
                    "type" : ["keyword"]
                },
                "type": {
                    "type" : ["keyword"]
                }, 
                "dashboard_id": {
                    "type" : ["keyword"]
                },
                "report_id": {
                    "type" : ["keyword"]
                },
                "siem_timestamp": {
                    "type" : "timestamp",
                    "timezone": "Europe/Paris",
                    "format": "%Y-%m-%d %H:%M:%S.%f"
                }, 
                "parserReceivedTime": {
                    "type" : "timestamp",
                    "timezone": "Europe/Paris",
                    "format": "%Y-%m-%d %H:%M:%S.%f"
                }
            }            
        }


    def handle_load_history(self, data):
        """"Handle load history request"""
        try:
            # TODO: test the permissions
            session_token = data.get("session_token", "")
            filter = data.get("filter", {})
            return self.history
        except Exception:
            self.logger.log("error", f"Failed to handle load history request: {traceback.format_exc()}")
            return []


    def handle_erase_history(self, data):
        """Handle erase history request"""
        try:
            print("erase history")
            # TODO: test the permissions
            session_token = data.get("session_token", "")
            filter = data.get("filter", {})
            if filter and "id" in filter:
                print("erase history with id")
                # Clear only specific entries
                ids_to_delete = set(filter["id"])
                self.history[:] = [entry for entry in self.history if entry.get("id") not in ids_to_delete]
                return self.history
            else:
                print("erase history without id")
                # Clear all entries
                self.history.clear()
                # TODO test if must create a erase_variable or let it there
                self.variables.clear()
                self.variables["next_id"] = 0
            return self.history
        except Exception:
            self.logger.log("error", f"Failed to handle erase history request: {traceback.format_exc()}")
            return {"message": "Failed to erase history"}


    def handle_suggestions(self, data):
        """Handle suggestions request"""
        try:
            print("Received suggestions request:", str(data))
            # Get the last command after the ";"
            user_input = data.get("input", "")
            last_command = user_input.split(";")[-1]
            if not last_command:
                all_commands = [
                    {
                        "name": cmd,
                        "description": self.command_loader.commands[cmd].get("description", "")
                    }
                    for cmd in self.command_loader.commands.keys()
                ]
                return all_commands

            parts = last_command.split()
            print("Parts:", str(parts))
            command_name = parts[0].strip()
            print("Command name:", command_name)

            # Step 1 : Suggestions of commands
            if len(parts) == 1 and command_name not in self.command_loader.commands.keys():
                print("Suggesting commands...")
                return [
                    {
                        "name": cmd,
                        "description": self.command_loader.commands[cmd].get("description", "")
                    }
                    for cmd in self.command_loader.commands
                    if cmd.startswith(command_name)
                ]

            # Step 2 : Suggestions of parameters
            if command_name in self.command_loader.commands.keys():
                print("Suggesting parameters for command: " + command_name)
                command = self.command_loader.commands[command_name]
                param_defs = command.get("params", [])
                print("Param definitions:", str(param_defs))

                already_provided = {p.split("=")[0] for p in parts[1:] if "=" in p}
                print("Already provided:", str(already_provided))

                last_token = parts[-1]
                partial_key = last_token if "=" not in last_token else ""
                print("Partial key:", partial_key)

                suggestions = []
                for param in param_defs:
                    pname = param.get("name")
                    if pname not in already_provided and (partial_key == command_name or pname.startswith(partial_key)):
                        suggestion = {
                            "name": pname,
                            "type": param.get("type", ""),
                            "description": param.get("description",""),
                            "default": param.get("default", None),
                            "required": param.get("required", False)
                        }
                        suggestions.append(suggestion)

                print("Suggestions:", str(suggestions))
                return {
                    "command": {
                        "name": command.get("name"),
                        "description": command.get("description", "")
                    },
                    "parameters": suggestions
                }
            return []

        except Exception:
            self.logger.log("error", f"Failed to handle suggestions: {traceback.format_exc()}")
            return []

    def handle_get_available_vault_instances(self, data):
        """Get a list of available vault instances"""
        # TODO: test the permissions
        instances = []
        for vault_name in self.integration_vault.list_keys():
            instances.append(vault_name["id"])
        return instances

    def handle_get_help(self, data):
            """ Provide help for all commands loaded on the SOAR """
            try:
                # 1. Inject search bar at the beginning of the help section
                help = """
                    <div style="margin-bottom: 15px; width: 100%;">
                    <input type="text" placeholder="Filter commands ..." 
                        oninput="
                            var filterText = this.value.toLowerCase();
                            var blocks = document.querySelectorAll('.command-block');
                            blocks.forEach(function(block) {
                                var cmdName = block.getAttribute('data-name').toLowerCase();
                                block.style.display = cmdName.includes(filterText) ? '' : 'none';
                            });
                        "
                        style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;">
                    </div>
                """
                # 2. Generate list commands
                for command_name in self.command_loader.commands.keys():
                    command = self.command_loader.commands[command_name]
                    param_defs = command.get("params", [])
                    help += f'<div class="command-block" data-name="{command_name}">'
                    help += """<button class="ui button collapsible">""" + command_name + """</button>
                                <div class="ui segment collapsed-content">"""
                    help += str(command["description"].replace("\n","<br/>")) + "<br/>"
                    help += "<b>parameters</b><br/>"
                    json_structure = json.dumps(param_defs, indent=4).replace(" ", "&nbsp;").replace("\n", "<br/>")
                    help += f"<pre style='white-space: pre-wrap'><code>{json_structure}</code></pre><br/></div>"
                    help += '</div>' 
                return help
            except:
                self.logger.log("error",f"Failed to load help {traceback.format_exc()}")
                raise 

    def run(self):
        while self.running:
            time.sleep(1)

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        log_collector = SOAR("soar.json", config_loader.get_config())
