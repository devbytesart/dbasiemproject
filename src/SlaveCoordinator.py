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
document: slave coordinator
"""

from ServiceBase import *
from Webhook import *
from CMDHandler import *
from WebRequester import *
from Configurator import *
import time, threading, json, os, traceback, re
from ParameterLoader import *
from DockerManager import *
from ResourcesMonitor import *
from Logger import *
import sys

class SlaveCoordinator(ServiceBase):
    def __init__(self, config_file, config = None): 
        # TODO add logger in the class
        # Configuration
        self.configurator = Configurator(config_file, config)
        self.configuration = config
        mcjson = self.configurator.find_all_matching_parents({"type":"slavecoordinator"})
        self.conf = self.configurator.get_config(mcjson[0])
        self.load_configuration()
        # Logger
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            # Resources monitor
            # TODO loop foreach self.elements
            #self.resources_monitor = ResourceMonitor(self.id, self.logger)
            # Secondaries coordinators
            #self.sec_coords = []
            # Slaves coordinators
            #self.slave_coords = []
            # print("ALL CONFIG:" + str(self.configurator.get_value(None)))
            # Logger 
            # TODO
            # Cmd Handler
            self.cmdhandler = CMDHandler({
                "configure":self.handle_set_config, 
                "configuration":self.configurator.get_config, 
                "shutdown": self.handle_shutdown, 
                "retrieve_monitoring": self.handle_retrieve_monitoring, 
                "forwarded_request":self.handle_forwarded_request, 
                "get_global_configuration": self.handle_get_global_configuration, 
                "set_global_configuration": self.handle_set_global_configuration, 
                "get_privileges":self.handle_get_global_privileges, 
                "set_privileges":self.handle_set_global_privileges
                })
            # Webhook
            #self.webhook = Webhook(self.host, self.port, self.cmdhandler.handle_json, self.auth_token, self.certfile, self.keyfile)
            # Create VM 
            # TODO avoid blocking error when docker not avaible
            #self.docker_manager = DockerManager()
            #self.create_infrastructure()
            # Statistics
            self.resources_monitors = {}
            self.thread_stats = threading.Thread(target=self._load_stats)
            self.thread_stats.daemon = True
            self.thread_stats.start()
            # start microservices
            self._start_microservices()
            # Run
            self.run_coord = True
            self.run()
        except:
            self.logger.log("error",f"Error initializing slave coordinator: {traceback.format_exc()}")


    def load_configuration(self):
        try:
            """Load the global configuration"""
            print("LOADING CONFIGURATION")
            mcjson = self.configurator.find_all_matching_parents({"type":"slavecoordinator"})
            self.conf = self.configurator.get_config(mcjson[0])
            # COORDINATOR PART
            self.id = self.conf["id"]
            self.host = self.conf["webhook"]["host"]
            self.port = self.conf["webhook"]["port"]
            self.auth_token = self.conf["webhook"]["auth_token"]
            self.certfile = self.conf["webhook"]["certs"]["certfile"]
            self.keyfile = self.conf["webhook"]["certs"]["keyfile"]
            self.bridge = self.conf["bridge"]["enabled"]
            # Monitoring
            self.monitoring_log_level = self.conf["logger"]["log_level"]
            self.monitoring_log_path = self.conf["logger"]["log_path"]
            self.monitoring_max_queue_size = self.conf["logger"]["max_queue_size"]
            self.monitoring_max_file = self.conf["logger"]["max_file"]
            self.monitoring_max_file_size = self.conf["logger"]["max_file_size"]
            self.monitoring_enable_print = utils.convert_param_type(self.conf["logger"]["enable_print"], bool)
            self.monitoring_enable_queue = utils.convert_param_type(self.conf["logger"]["enable_queue"], bool)
            self.monitoring_enable_file = utils.convert_param_type(self.conf["logger"]["enable_file"], bool)
            # STORAGE
            self.storage_path = self.conf["storage"]["path"]
            # MASTER COORDINATOR
            # TODO check if the master exists before launch the function
            self.master_coord = []
            # Uses masters to replace mastercoordinators as already used in the configuration and create errors
            print("IN MASTERS COORD INIT BEFORE")
            if "masters" in self.conf and len(self.conf["masters"]) > 0:
                print("IN MASTERS COORD INIT")
                self.master_coord = self.conf["masters"]
                self.master_coord_wb = WebRequester(self.master_coord[0]["host"], self.master_coord[0]["port"], self.master_coord[0]["auth_token"])
        except:
            self.logger.log("error", f"Error loading configuration: {traceback.format_exc()}")

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def _load_stats(self):
        while True:
            # TODO complete the log statistics for slavecoordinator
            stats = {
                "name": "statistics_monitoring",
                "type": "slavecoordinator_monitoring"
            }
            # Resources monitoring
            # TODO troubleshoot this part, Decimal crash the SOAR
            # for res_mon in self.resources_monitors:
            #     try:
            #         self.logger.log("info", self.resources_monitors[res_mon].get_container_info())
            #     except:
            #         self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            time.sleep(10)

    def _stop_microservices(self):
        try:
            # Stop the resources monitor
            self.resources_monitor.stop()
            # Stop the webhook
            self.webhook.stop()        
            self.logger.log("info",f"Stop microservices Slavecoordinator {self.id}")
            return True
        except:
            self.logger.log("error", f"Failed to stop webhook: {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            # Restart the logger
            self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            # Start the webhook
            self.webhook = Webhook(self.host, self.port, self.cmdhandler.handle_json, self.auth_token, self.certfile, self.keyfile)
            # self.docker_manager = DockerManager()
            self.docker_manager = DockerManager(self.bridge)
            self.create_infrastructure()           
            # Monitoring
            self.resources_monitors = {}
            self.resources_monitor = ResourceMonitor(self.id, self.logger)
            self.logger.log("info",f"Microservices started {self.id}")
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

    def handle_shutdown(self):
        return self._stop_microservices()

    def _create_docker(self, sub_conf, command_file):
        """Create a docker container"""
        try:
            print("subconfiguration: " + str(sub_conf))
            image_name = sub_conf["image"]
            image_tag = sub_conf["id"]
            ports = {}
            host_ip = ""
            if "webhook" in sub_conf:
                ports[str(sub_conf["webhook"]["port"]) + "/tcp"] = sub_conf["webhook"]["port"]
            if "receiver" in sub_conf:
                ports[str(sub_conf["receiver"]["port"]) + "/" + str(sub_conf["receiver"]["protocol"]).lower()] = sub_conf["receiver"]["port"]
            if "webserver" in sub_conf:
                ports[str(sub_conf["webserver"]["port"]) + "/tcp"] = sub_conf["webserver"]["port"]
            if "volumes" in sub_conf:
                volumes = sub_conf["volumes"]
            else :
                volumes = {}
            command = "python " + command_file + " -i '" + json.dumps(sub_conf).replace("\\","\\\\") + "'"
            self.logger.log("info",f"Create docker : {image_name} - {image_tag}")
            self.docker_manager.create_container(image_name, image_tag, ports, volumes, command)
            return True
        except:
            self.logger.log("error", f"Error creating docker container: {traceback.format_exc()}")
            return False

    def _identify_command(self, elem):
        """Identify the command and execute it"""
        try:
            if elem == "logcollector":
                return "LogCollector.py"
            elif elem == "logparser":
                return "LogParser.py"
            elif elem == "logindexer":
                return "LogIndexer.py"
            elif elem == "cachesystem":
                return "CacheSystem.py"
            elif elem == "dedicatedindexsearchmotor":
                return "DedicatedIndexSearchMotor.py"
            elif elem == "indexsearchmotor":
                return "IndexSearchMotor.py"
            elif elem == "searchinterface":
                return "SearchInterface.py"
            elif elem == "userinterface":
                return "UserInterface.py"
            elif elem == "authenticator":
                return "Authenticator.py"
            elif elem == "soar":
                return "SOAR.py"
        except:
            self.logger.log("error", f"Error identifying command: {traceback.format_exc()}")
            return None

    def create_infrastructure(self):
        """With the configuration create the infrastructure"""
        print("Creating infrastructure...")
        try:
            for cons in self.configuration["infrastructure"]["sub-infrastructure"]:
                for con in range(0,len(self.configuration["infrastructure"]["sub-infrastructure"][cons])):
                        sub_conf = self.configuration["infrastructure"]["sub-infrastructure"][cons][con]
                        self._create_docker(sub_conf, self._identify_command(sub_conf["type"]))
        except:
            self.logger("error", f"Error creating infrastructure: {traceback.format_exc()}")
    
    def handle_set_config(self, data):
        """Handle the configuration"""
        try:
            print("HANDLE SET CONFIG IN SLAVE COORDINATOR")
            print("OLD ELEMENTS: " + str(self.configurator.elements))
            self.configurator.set_config(data)
            self.configurator.interpret_config(self.configuration)
            self.configuration = self.configurator.get_config()
            self.load_configuration()
            # TODO decomment this part to restart the microservices if the slavecoordinator is concerned
            # self._restart_microservices()
            print("NEW ELEMENTS: " + str(self.configurator.elements))
            removed, added, modified = self.configurator.compare_elements()
            self.action_on_removed(removed)
            self.action_on_added(added)
            self.action_on_modified(modified)
            # TODO decomment this part to create the infrastructure again
            # self.create_infrastructure()
        except:
            self.logger.log("error", f"Error handling set config: {traceback.format_exc()}")

    def action_on_removed(self, data):
        """Handle the removed elements"""
        try:
            # TODO create this function
            # TODO change the priority of elements and wait for the closure before starting the new one
            print("Removed: " + str(data))
            for d in data:
                # Get old elements as the elements is removed in the new configuration
                elem = self.configurator.old_elements[d]
                print("REMOVED ELEMENT: " + str(elem))
                if "webhook" in elem:
                    wr = WebRequester(elem["webhook"]["host"], elem["webhook"]["port"], elem["webhook"]["auth_token"])
                elif "webserver" in elem:
                    wr = WebRequester(elem["webserver"]["host"], elem["webserver"]["port"], elem["webserver"]["auth_token"])
                shut = wr.shutdown()
                # TODO add in task the shutdown of the container
                # TODO wait for the closure of the container
                # TODO wait the return shut and add in task
                # if not shut:
                #     time.sleep(30)
                self.docker_manager.remove_container(d, False)
                self.resources_monitors[d] = None
        except:
            self.logger.log("error", f"Error handling removed elements: {traceback.format_exc()}")

    def action_on_added(self, data):
        """Handle the added elements"""
        # TODO create this function
        try:
            print("Added: " + str(data))
            for d in data:
                # TODO change the priority of elements and wait for the closure before starting the new one
                self._create_docker(self.configurator.elements[d], self._identify_command(self.configurator.elements[d]["type"]))
                self.resources_monitors[d] = ResourceMonitor(d, self.logger)
            # TODO change the method create infrastructure to simplify the code
            # self._create_docker(s, self._identify_command(data, )
        except:
            self.logger.log("error", f"Error handling added elements: {traceback.format_exc()}")


    def action_on_modified(self, data):
        """Handle the modified elements"""
        for mod in data:
            for mod_key in mod[1]:
                try:
                    elem = self.configurator.elements[mod[0]]
                    print("mod0: " + str(elem))
                    # Determine which type of micro service it is
                    if "webhook" in elem:
                        t = "webhook"
                    elif "webserver" in elem:
                        t = "webserver"
                    else:
                        self.logger.log("error", "Unknown server type")
                        continue
                    print("MOD_KEY:" + str(mod_key))
                    if "port" in mod_key or "host" in mod_key or "id" in mod_key:
                        # Check if the container is running
                        container_id = elem.get("id")
                        # If container exists, remove it
                        if self.docker_manager.container_exists(container_id):
                        # Check if the container has been correctly removed
                            if not self.docker_manager.remove_container(container_id):
                                self.logger.log("error", f"Failed to remove container {container_id}")
                        # Check if port is in use
                        port = elem[t]["port"]
                        if utils.check_port_in_use(port):
                            self.logger.log("error", f"Port {port} is already in use")
                            continue
                        # Create the new container
                        self._create_docker(elem, self._identify_command(elem["type"]))
                    else:
                        # Test if an old auth_token already exists
                        if "auth_token" in self.configurator.old_elements[mod[0]][t]:
                            auth_token = self.configurator.old_elements[mod[0]][t]["auth_token"]
                        else:
                            auth_token = self.configurator.elements[mod[0]][t]["auth_token"]
                        # Configure the server with the new configuration
                        wr = WebRequester(elem[t]["host"], elem[t]["port"], auth_token)
                        print("Before configure")
                        thread_task = threading.Thread(target=wr.configure, args=(None, elem))
                        thread_task.start()
                        print("After configure")
                except Exception:
                    self.logger.log("error", f"Error handling modified: {traceback.format_exc()}")


    def handle_forwarded_request(self, request):
        """ Forward the request to a service in the cluster """
        # TODO this function will not work. Should find a way to do it properly
        try:
            print("IN HANDLE FORWARDED REQUEST")
            print("REQUEST: " + str(request))
            destination = request.get("destination")
            host = destination.get("host")
            port = destination.get("port")
            token = destination.get("token")
            webhook_url = destination.get("webhook_url")
            timeout = destination.get("timeout")
            retry = destination.get("retry", 5)
            is_compressed = destination.get("is_compressed", False)
            data = request.get("data")
            print("DATA IN FORWARDED REQUEST: " + str(data) + ":" + str(type(data)))
            #TODO find another way for the web request url 
            wr = WebRequester(host, port, token, timeout)
            # wr = WebRequester(webhook_url, token, host, port, timeout)
            # TODO find another way to check the method (GET or POST)
            # TODO Resolve the problem with the compression
            result = wr.send_request(webhook_url, data, retry, is_compressed)
            print("RESULT: " + str(result))
            try:
                # TODO find a better way to do this
                return json.loads(result)
            except:
                self.logger.log("error", f"Error handling forward request: {traceback.format_exc()}")
                return result
        except:
            self.logger.log("error", f"Error handling forward request: {traceback.format_exc()}")
            return None
        
    #TODO determine if it is the right way to do it
    def handle_get_global_configuration(self, request):
        print("Get global configuration from slave coordinator")
        session_token = request["session_token"]
        # TODO test if the user is authorized to get the configuration
        # return json.loads(self.master_coord_wb.configuration())
        return json.loads(self.master_coord_wb.get_global_configuration(session_token))
    
    def handle_set_global_configuration(self, request):
        session_token = request.get("session_token")
        configuration = request.get("configuration")
        # TODO test if the user is authorized to set the configuration
        # return self.master_coord_wb.configure(None, request["configuration"])
        return self.master_coord_wb.set_global_configuration(session_token, configuration)
    
    #TODO to be replaced by forward_request when this function will be implemented
    def handle_get_global_privileges(self, request):
        session_token = request.get("session_token")
        # TODO test if the user is authorized to get the configuration
        return json.loads(self.master_coord_wb.get_privileges(session_token))

    #TODO to be replaced by forward_request when this function will be implemented
    def handle_set_global_privileges(self, request):
        session_token = request.get("session_token")
        privileges = request.get("privileges")
        # TODO test if the user is authorized to set the configuration
        return self.master_coord_wb.set_privileges(session_token, privileges)
    
    def run(self):
        """Main loop of the coordinator"""
        while self.run_coord:
            try:
                # TODO wait for a command
                time.sleep(1)
            except:
                self.logger.log("error", f"Error running coordinator: {traceback.format_exc()}")

    def command_handler(self, data):
        print("in command handler " + str(data))

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        coordinator = SlaveCoordinator("localConfig.json", config_loader.get_config())