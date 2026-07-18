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
document: master coordinator
"""

from ServiceBase import *
from Webhook import *
from CMDHandler import *
from WebRequester import *
from Configurator import *
import time, threading, json, os, traceback, re
from ParameterLoader import *
from PrivilegesManager import *
from Logger import *
import copy
import sys
import Utils as utils
import jwt

class MasterCoordinator(ServiceBase):
    def __init__(self, config_file, config, primary, secret): 
        # Configuration
        # TODO add logger in the class
        self.primary = primary
        self.secret = secret
        print("SELF.SECRET: " + self.secret)
        print("file: " + config_file)
        self.configurator = Configurator(config_file, config)
        mcjson = self.configurator.find_all_matching_parents({"type":"mastercoordinator","primary":self.primary})
        print("MC: " + str(mcjson[0]))
        self.conf = self.configurator.get_config(mcjson[0])
        print("configuration:" + str(self.conf))
        self.load_configuration()
        # load logger
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            # Secondaries coordinators
            self.sec_coords = []
            # Slaves coordinators
            self.slave_coords = {}
            # Authenticators
            self.authenticators = {}
            # Privileges Manager
            self.privileges_manager = PrivilegesManager(self.id, self.storage_path, self.logger)
            self.privileges_manager.initialize_global_privileges(None)
            # Cmd Handler
            self.cmdhandler = CMDHandler({#"configure":self.handle_set_config, 
                                          "configuration":self.configurator.handle_get_configuration, 
                                          "get_global_configuration": self.handle_get_config,
                                          "set_global_configuration": self.handle_set_config,
                                          "shutdown": self.handle_shutdown, 
                                          "retrieve_monitoring": self.handle_retrieve_monitoring,
                                          "get_privileges":self.handle_get_global_privileges, 
                                          "set_privileges":self.handle_set_global_privileges
                                          })
            # Webhook
            self.webhook = Webhook(self.host, self.port, self.cmdhandler.handle_json, self.auth_token, self.certfile, self.keyfile)
            # Contact secondary coordinators
            self.send_configuration_to_secondary_coordinators()
            # Contact slave coordinators
            self.send_configuration_to_slave_coordinators()
            # Send privileges
            self.send_privileges_to_authenticators()
            # Run
            self.run_coord = True
            self.run()
        except:
            self.logger.log("error", f"Error during starting services {traceback.format_exc()}")

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def _stop_microservices(self):
        # Stop webhook
        try:
            self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Failed to stop webhook: {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            self.webhook = Webhook(self.host, self.port, self.cmdhandler.handle_json, self.auth_token, self.certfile, self.keyfile)
            self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            self.privileges_manager = PrivilegesManager(self.id, self.storage_path, self.logger)
            self.privileges_manager.initialize_global_privileges(None)
            return True
        except:
            self.logger.log("error", f"Failed to start webhook: {traceback.format_exc()}")
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

    def load_configuration(self):
        """Load the global configuration"""
        # COORDINATOR PART
        try:
            self.id = self.conf["id"]
            self.primary = self.conf["primary"]
            self.host = self.conf["webhook"]["host"]
            self.port = self.conf["webhook"]["port"]
            self.auth_token = self.conf["webhook"]["auth_token"]
            self.certfile = self.conf["webhook"]["certs"]["certfile"]
            self.keyfile = self.conf["webhook"]["certs"]["keyfile"]
            # Monitoring
            self.monitoring_log_level = self.conf["logger"]["log_level"]
            self.monitoring_log_path = self.conf["logger"]["log_path"]
            self.monitoring_max_queue_size = self.conf["logger"]["max_queue_size"]
            self.monitoring_max_file = self.conf["logger"]["max_file"]
            self.monitoring_max_file_size = self.conf["logger"]["max_file_size"]
            self.monitoring_enable_print = utils.convert_param_type(self.conf["logger"]["enable_print"], bool)
            self.monitoring_enable_queue = utils.convert_param_type(self.conf["logger"]["enable_queue"], bool)
            self.monitoring_enable_file = utils.convert_param_type(self.conf["logger"]["enable_file"], bool)
            # Storage
            self.storage_path = self.conf["storage"]["path"]
        except:
            print(traceback.format_exc())
            return
    
    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None
        
    def handle_shutdown(self, data):
        # TODO implement this part
        pass

    def send_configuration_to_secondary_coordinators(self):
        """Contact the secondary coordinator to set the configuration"""
        try:
            if self.primary:
                # TODO this part is not implemented yet
                for sec_coord in self.configurator.find_all_matching_parents({"type":"mastercoordinator", "primary":False}):
                    coord = self.configurator.get_config(sec_coord)
                    # TODO send the configuration to the secondary coordinator
        except:
            print(traceback.format_exc())
            return
            

    def send_configuration_to_slave_coordinators(self):
        """Contact the slave coordinator to set the configuration"""
        try:
            if self.primary:
                for slave in self.configurator.get_config(["infrastructure","slavecoordinators"]):
                    self.logger.log("info",f"Master send configuration to {slave['id']}")
                    print(slave)
                    new_configuration = copy.deepcopy(slave)
                    print(self.configurator.elements)
                    self.configurator.replace_references(new_configuration, self.configurator.elements)
                    print("NEW CONFIGURATION: " + str(new_configuration))
                    self.slave_coords[slave["id"]] = WebRequester(new_configuration["webhook"]["host"], new_configuration["webhook"]["port"], new_configuration["webhook"]["auth_token"])
                    # TODO temp
                    self.slave_coords[slave["id"]].configure(["infrastructure"], new_configuration)
                    # TODO send the configuration to the slave coordinator
        except:
            print(traceback.format_exc())

    def send_privileges_to_authenticators(self):
        """ Contact the authenticators to set the privileges"""
        try:
            if self.primary:
                print("SENDING PRIVILEGES TO AUTHENTICATORS")
                for slave in self.configurator.get_config(["infrastructure","slavecoordinators"]):
                    for authenticator in slave["sub-infrastructure"]["authenticators"]:
                        try:
                            self.logger.log("info",f"Master send privileges to {authenticator['id']}")
                            # Send the new privileges to the authenticator
                            new_privileges = copy.deepcopy(self.privileges_manager.get_global_privileges(authenticator["id"]))
                            self.configurator.replace_references(new_privileges, self.configurator.elements)
                            wr = WebRequester(authenticator["webhook"]["host"], authenticator["webhook"]["port"], authenticator["webhook"]["auth_token"])
                            self.authenticators[authenticator["id"]] = wr
                            # Authenticate the user
                            # TODO put the authentication elsewhere maybe ?? 
                            token =  wr.sign_in("siem_system", self.secret)
                            if token is None or token == "" or token == "null":
                                print("MUST create the user")
                                wr.set_privileges(token, new_privileges)
                                # User not initialized, must create the user
                                if wr.sign_up("siem_system", self.secret):
                                    token = wr.sign_in("siem_system", self.secret)
                                else:
                                    self.logger.log("error", f"Failed to create the user: {traceback.format_exc()}")
                                    return False
                            try:
                                print("TOKEN:", token)
                                # if token is not None and token != "" and token != "null":
                                # TOKEN is send in chain. Replace "" at the beginning and the end of the string
                                    # decoded = jwt.decode(token[1:-1], "secret", algorithms=["HS256"])
                                    # print("DECODED:", decoded)
                            except jwt.ExpiredSignatureError:
                                self.logger.log("error", f"Failed to decode token expired: {traceback.format_exc()}")
                            except jwt.InvalidTokenError as e:
                                self.logger.log("error", f"Invalid token:{traceback.format_exc()}")
                            print("GLOBAL PRIVILEGES:", str(new_privileges))
                            wr.set_privileges(token, new_privileges)
                        except:
                            self.logger.log("error", f"Failed to send privileges to authenticator: {traceback.format_exc()}")
            return True
        except:
            print(traceback.format_exc())
            return False

    def handle_get_global_privileges(self, request):
        """ Return the global privileges json file """
        try:
            if self.primary:
                token = json.loads(request.get("session_token", None))
                if self._check_permissions(token, [{"resource":"global_privileges", "type": "file", "read":True, "write":False}]):
                    return self.privileges_manager.get_global_privileges()
            return False
        except:
            self.logger.log("error", f"Error during get global privileges : {traceback.format_exc()}")
            return False


    def handle_set_global_privileges(self, request):
        """ Change the global privileges and forward to the authenticators """
        try:
            if self.primary:
                token = json.loads(request.get("session_token", None))
                if self._check_permissions(token, [{"resource":"global_privileges", "type":"file", "read":True, "write":True}]):
                    if self.privileges_manager.handle_set_global_privileges(request):
                        self.send_privileges_to_authenticators()
            return True
        except:
            print(traceback.format_exc())
            return False

    def _load_stats(self):
        # TODO implement this part
        pass

    def handle_get_config(self, request):
        """Handle the get configuration command"""
        try:
            print("MASTER HANDLE GET CONFIGURATION:" + str(request))
            token = json.loads(request.get("session_token", None))
            if token is not None:
                authenticator = token["authenticator"]
                token_data = token["token"]
                # Careful with the answer, it is in json format not boolean
                if json.loads(self.authenticators[authenticator].check_permissions(token_data, [{"resource":"global_configuration", "type":"file", "read":True, "write":False}])):
                    print("TOKEN IS VALID")
                    return self.configurator.get_config()
                else: 
                    print("TOKEN IS NOT VALID")
                    return {}
        except:
            print(traceback.format_exc())
            return {}

    def handle_set_config(self, request):
        """Handle the set configuration command"""
        try:
            print("MASTER HANDLE SET CONFIGURATION:" + str(request))
            token = json.loads(request.get("session_token", None))
            print("type of config:", str(type(request.get("configuration", None))))
            config = request.get("configuration", None)
            if self._check_permissions(token, [{"resource":"global_configuration", "type":"file", "read":True, "write":True}]):
                print("TOKEN IS VALID FOR SET CONFIG")
                self.configurator.set_config({"configuration":config, "path_list":[]})
                # Copy the new configuration file to the storage
                # TODO change the backup (must be done from the configurator directly)
                config_version = self.configurator.config_data["version"]
                copy_path = os.path.join(self.storage_path, "backup_configuration", f"configuration_{config_version}.json")
                utils.create_folders(copy_path)
                self.configurator.save_config(copy_path)
                self.configurator.interpret_config(self.configurator.config_data)
                # Interpret the references
                self.send_configuration_to_secondary_coordinators()
                self.send_configuration_to_slave_coordinators()
                return True
            return False
        except:
            print(traceback.format_exc())
            return False

    def _check_permissions(self, token, permissions_required):
        if token is not None:
            authenticator = token.get("authenticator")
            token_data = token.get("token")
            return json.loads(self.authenticators[authenticator].check_permissions(token_data, permissions_required))
        return False

    def run(self):
        """Main loop of the coordinator"""
        while self.run_coord:
            print("in run")
            # TODO wait for a command
            time.sleep(1)
            
    def command_handler(self, data):
        print("in command handler " + str(data))

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config() and config_loader.is_primary() and config_loader.get_secret():
        coordinator = MasterCoordinator('globalConfig.json', config_loader.get_config(), config_loader.is_primary(), config_loader.get_secret())