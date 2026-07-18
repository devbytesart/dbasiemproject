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
document: authenticator
"""

from ServiceBase import *
# from WebRequester import *
from Configurator import *
from CMDHandler import *
from Webhook import *
from Logger import *
from ParameterLoader import *
from PrivilegesManager import *
import Utils as utils

class Authenticator(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            self.privileges_manager = PrivilegesManager(self.id, self.storage_path, self.logger)
            # Initialize the database of users
            self.privileges_manager.initialize_database()
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "retrieve_monitoring": self.logger.retrieve_monitoring, 
                "shutdown": self.handle_shutdown, 
                "get_privileges": self.privileges_manager.handle_get_local_privileges, 
                "set_privileges": self.privileges_manager.handle_set_local_privileges,
                "sign_in": self.privileges_manager.handle_sign_in, 
                "sign_up": self.privileges_manager.handle_sign_up,
                "sign_out": self.privileges_manager.handle_sign_out, 
                "check_permissions": self.privileges_manager.handle_check_permissions,
                "check_username": self.privileges_manager.handle_check_username,
                "change_password": self.privileges_manager.handle_change_password
                })
            self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
        except:
            self.logger.log("error", f"Failed to initialize authenticator: {traceback.format_exc()}")

    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]    
        # WEB REQUESTER
        # self.proxies = self.config["webrequester"]["proxy"]
        # self.timeout = self.config["webrequester"]["timeout"]
        # self.slave_reverse = self.config["webrequester"].get("slave_reverse")    
        # LOGGER
        self.monitoring_log_level = self.config["logger"]["log_level"]
        self.monitoring_log_path = self.config["logger"]["log_path"]
        self.monitoring_max_queue_size = self.config["logger"]["max_queue_size"]
        self.monitoring_max_file = self.config["logger"]["max_file"]
        self.monitoring_max_file_size = self.config["logger"]["max_file_size"]
        self.monitoring_enable_print = utils.convert_param_type(self.config["logger"]["enable_print"], bool)
        self.monitoring_enable_queue = utils.convert_param_type(self.config["logger"]["enable_queue"], bool)
        self.monitoring_enable_file = utils.convert_param_type(self.config["logger"]["enable_file"], bool)
        # TODO complete the max queue for the logger that is not set in the configuration file
        # WEBHOOK
        self.webhook_host = self.config["webhook"]["host"]
        self.webhook_port = self.config["webhook"]["port"]
        self.webhook_token = self.config["webhook"]["auth_token"]
        self.webhook_certfile = self.config["webhook"]["certs"]["certfile"]
        self.webhook_keyfile = self.config["webhook"]["certs"]["keyfile"]
        # STORAGE 
        self.storage_path = self.config["storage"]["path"]
        # SLAVECOORDINATOR
        self.slave_coordinator_id = self.config["slavecoordinator"]["id"]
        self.slave_coordinator_host = self.config["slavecoordinator"]["host"]
        self.slave_coordinator_port = self.config["slavecoordinator"]["port"]
        self.slave_coordinator_auth_token = self.config["slavecoordinator"]["auth_token"]


    def _stop_microservices(self):
        try:
            # Stop the service collectors 
            self.stop_threads_services()
            # Wait for the queue to be empty
            thread = threading.Thread(target=self.queue_manager.wait_for_empty_queue)
            thread.start()
            thread.join()
            # Stop the webhook
            self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Failed to stop microservices: {traceback.format_exc()}")
            return False


    def _start_microservices(self):
        try:
            self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            self.privileges_manager = PrivilegesManager(self.id, self.storage_path, self.logger)
            # Initialize the database of users
            self.privileges_manager.initialize_database()
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            self._start_threads_services()
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


    def _load_stats(self):
        # TODO implement this part
        pass

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None
        
    def handle_shutdown(self):
        try:
            return self._stop_microservices()
        except:
            self.logger.log("error", f"Failed to shutdown: {traceback.format_exc()}")
            return False

    def handle_set_config(self, data):
        # TODO to complete with restarting the right services
        try:
            # Print configuration
            self.configurator.set_config(data)
            self.load_configuration()
            # Restart receiver listener and webhook
            return self._restart_microservices()
        except:
            self.logger.log("error", f"Failed to set configuration: {traceback.format_exc()}")
            return False 

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        log_collector = Authenticator("authenticatorConfig.json", config_loader.get_config())
