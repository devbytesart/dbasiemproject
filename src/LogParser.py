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
document: log parser
"""

import json
import socket
import ssl
import sys, os, time
import base64
import importlib
import importlib.resources as pkg_resources
import inspect
import pkgutil
import traceback
import random
import copy
import re
import UtilsIndexing as uindex
import Utils as utils
from datetime import datetime, timezone
from ServiceBase import *
from Configurator import *
from QueueManager import QueueManager
from CMDHandler import *
from Logger import *
from LPParserInterface import LPParserInterface
from LPFilterInterface import LPFilterInterface
from LPAgregatorInterface import LPAgregatorInterface
from LPAnonymizerInterface import LPAnonymizerInterface
from LPCategorizerInterface import LPCategorizerInterface
# from old.LPMapperInterface import LPMapperInterface
from WebRequester import *
from Webhook import *
from ParameterLoader import *


class LogParser(ServiceBase):
    def __init__(self, config_file='logparserconfig.json', config=None):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        # TODO complete the logger infomration
        # self.resource_monitor = ResourceMonitor(self.id)
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            # sys.path.append(os.path.join(os.path.dirname(__file__), self.folder_plugin))
            # self.cmdhandler = CMDHandler({"configure":self.config.set_config, "configuration":self.config.get_config})
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "retrieve_logs": self.handle_retrieve_logs, 
                "retrieve_mapping": self.handle_retrieve_mapping, 
                "shutdown":self.handle_shutdown, 
                "retrieve_monitoring": self.handle_retrieve_monitoring})
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.max_backup_file, self.max_backup_file_size)
            # self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            # self.collector_requester = WebRequester(self.logcollector_host, self.logcollector_port, self.logcollector_token, slave_reverse=self.slave_reverse)
            # Statistics
            self.avg_parse_time = 0
            self.avg_restore_time = 0
            self.count = 0
            self.start_count = time.time()
            self.thread_stats = threading.Thread(target=self._load_stats)
            # self.thread_stats.daemon = True
            self.thread_stats.start()
            self.load_plugins()
            self._start_microservices()
        except:
            self.logger.log("error", f"Error during initialisation of logparser : {traceback.format_exc()}")

    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
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
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        # QUEUE
        self.backup_file = self.config["queue"]["backup_file"]
        self.stats_file = self.config["queue"]["stats_file"]
        self.queue_size = self.config["queue"]["max_queue_size"]
        self.max_backup_file = self.config["queue"]["max_backup_file"]
        self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
        # DELIMITER
        # TODO change this part
        self.delimiter = "$$$BREAK$$$"
        # self.delimiter = self.config["delimiter"]
        self.tenant = self.config["tenant"]
        # PLUGINS
        ## PREFILTER
        self.prefilter_folder = self.config["plugins"]["prefilter_folder"]
        self.prefilter_name = self.config["prefilter"]["name"]
        self.prefilter_filter = self.config["prefilter"]["filter"]
        self.prefilter_out = self.config["prefilter"]["out"]
        ### POSTFILTER
        self.postfilter_folder = self.config["plugins"]["postfilter_folder"]
        self.postfilter_name = self.config["postfilter"]["name"]
        self.postfilter_filter = self.config["postfilter"]["filter"]
        self.postfilter_out = self.config["postfilter"]["out"]
        ## PARSER
        self.parser_folder = self.config["plugins"]["parser_folder"]
        self.parser_name = self.config["parser"]["name"]
        self.parser_technology = self.config["parser"]["technology"]
        ## CATEGORIZER
        self.categorizer_folder = self.config["plugins"]["categorizer_folder"]
        self.categorizer_name = self.config["categorizer"]["name"]
        ## AGREGATOR
        self.agregator_folder = self.config["plugins"]["agregator_folder"]
        self.agregator_name = self.config["agregator"]["name"]
        ## ANONYMIZER
        self.anonymizer_folder = self.config["plugins"]["anonymizer_folder"]
        self.anonymizer_name = self.config["anonymizer"]["name"]
        self.anonymizer_fields = self.config["anonymizer"]["fields"]
        ## MAPPER User in parser
        # self.mapper_folder = self.config["plugins"]["mapper_folder"]
        # self.mapper_name = self.config["mapper"]["name"]
        ## WEBREQUESTER
        self.proxies = self.config["webrequester"]["proxy"]
        self.timeout = self.config["webrequester"]["timeout"]
        self.slave_reverse = self.config["webrequester"].get("slave_reverse")
        # LOG COLLECTOR
        if "host" in self.config["logcollector"] and "port" in self.config["logcollector"] and "auth_token" in self.config["logcollector"]:
            self.logcollector_host = self.config["logcollector"]["host"]
            self.logcollector_port = self.config["logcollector"]["port"]
            self.logcollector_token = self.config["logcollector"]["auth_token"]
            self.logcollector_size = self.config["logcollector"]["size"]
        else:
            self.running = False


    def _stop_threads_services(self):
        try:
            self.running = False
            self.main_thread.join()
            self.logger.log("info",f"Stop threads services parser {self.id}")
        except:
            self.logger.log("error", f"Error during stop of logparser : {traceback.format_exc()}")


    def _start_threads_services(self):
        try:
            self.running = True
            self.main_thread = threading.Thread(target=self.run)
            # self.main_thread.daemon = True
            self.main_thread.start()
            self.logger.log("info",f"Start thrads services parser {self.id}")
        except:
            self.logger.log("error", f"Error during start of logparser : {traceback.format_exc()}")


    def _stop_microservices(self):
        try:
            print("STOP MICRO SERVICES")
            # Cut the incoming of data from logcollector
            # self.running = False
            self._stop_threads_services()
            print("running false")
            # self.main_thread.Stop()
            # self.main_thread.join()
            # Wait for the queue to be empty
            # TODO find a way to stop the queue manager or make it wait for the queue to be empty or send the file
            # Stop the webhook
            # Arrêter le webhook
            # TODO troubleshoot this part. The stopping of the webhook stop the container
            # if hasattr(self, 'webhook') and self.webhook:
            self.webhook.stop()
            self.logger.log("info",f"Stop microservices weebhook stopped {self.id}")
            # self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Error during stopping microservices : {traceback.format_exc()}")
            return False
        
    def _start_microservices(self):
        try:
            print("START MICRO SERVICES")
            self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.max_backup_file, self.max_backup_file_size) 
            self.load_plugins()   
            self.collector_requester = WebRequester(self.logcollector_host, self.logcollector_port, self.logcollector_token, self.timeout, self.proxies, slave_reverse=self.slave_reverse)
            self._start_threads_services()
            # self.running = True
            # self.main_thread = threading.Thread(target=self.run)
            # # self.main_thread.daemon = True
            # self.main_thread.start()
            self.logger.log("info",f"All services started parser {self.id}")
            return True
        except:
            self.logger.log("error", f"Error during starting microservices : {traceback.format_exc()}")
            return False

    def _restart_microservices(self):
        print("RESTART MICRO SERVICES")
        # Restart the logger
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size)
        # Restart others microservices
        try:
            stopped = self._stop_microservices()
            # Waiting the port to be free
            time.sleep(1)
            if stopped:
                return self._start_microservices()
            else:
                self.logger.log("error", "Error during stopping microservices")
                return False
        except:
            self.logger.log("error", f"Error during restart of logparser : {traceback.format_exc()}")
            return False

    def _load_stats(self):
        while True:
            try:
                stats = {
                    "name": "statistics_monitoring",
                    "type": "logparser_statistics",
                    "avg_parse_time": self.avg_parse_time,
                    "avg_restore_time": self.avg_restore_time,
                    "avg_lp_eps": self.count / (time.time() - self.start_count),
                }
                stats.update(self.queue_manager.get_stats())
                self.logger.log("debug", stats)
                # Resources monitor container
                stats_res = {
                    "type": "logparser_resources"
                }
                # stats_res.update(self.resource_monitor.get_container_info())
                self.logger.log("info", stats_res)
                self.count = 0
                self.start_count = time.time()
                time.sleep(10)
            except:
                self.logger.log("error", f"Error during loading statistics : {traceback.format_exc()}")

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def handle_shutdown(self):
        return self._stop_microservices()

    def handle_set_config(self, data):
        try:
            self.configurator.set_config(data)
            self.load_configuration()   
            # Restart microservices 
            return self._restart_microservices()     
        except:
            self.logger.log("error", "Error setting configuration:" + traceback.format_exc())
            return False

    def load_plugins(self):
        try:
            # PREFILTER
            self.prefilter = self.load_plugin(self.prefilter_folder,self.prefilter_name,LPFilterInterface)
            # PARSER
            self.parser = self.load_plugin(self.parser_folder,self.parser_name,LPParserInterface)
            # POSTFILTER
            self.postfilter = self.load_plugin(self.prefilter_folder,self.prefilter_name,LPFilterInterface)
            # CATEGORIZER
            self.categorizer = self.load_plugin(self.categorizer_folder,self.categorizer_name,LPCategorizerInterface)
            # AGREGATOR
            # TODO
            # self.agregator = self.load_plugin(self.agregator_folder,self.agregator_name,LPAgregatorInterface)
            # ANONYMIZER
            self.anonymizer = self.load_plugin(self.anonymizer_folder,self.anonymizer_name,LPAnonymizerInterface)
            # MAPPER
            # TODO
            # self.mapper = self.load_plugin(self.mapper_folder,self.mapper_name,LPMapperInterface)  
            self.logger.log("debug",f"Plugins parser loaded {self.id}")
        except:
            self.logger.log("error", "Error loading plugins:" + traceback.format_exc())

    def handle_retrieve_logs(self, size):
        try:
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

    def merge_mapping(self, dict1, dict2):
        merged = {}
        # For default_timestamp, we keep the first one
        merged["default_timestamp"] = dict1.get("default_timestamp") or dict2.get("default_timestamp")
        # Fusion "fields"
        merged_fields = dict1.get("fields", {}).copy()
        merged_fields.update(dict2.get("fields", {}))  # override duplicata
        merged["fields"] = merged_fields
        return merged

    def handle_retrieve_mapping(self, data):
        try:
            # TODO find a better way to do this
            if self.parser_name == "Multiple":
                mapping = {}
                for parser in self.parser:
                    mapping = self.merge_mapping(mapping, parser.createMap())
                return mapping
            return self.parser.createMap()
        except:
            self.logger.log("error",f"Error while retrieving mapping: {traceback.format_exc()}")
            return None


    def load_plugin(self, folder_plugin, plugin_name, abstract_plugin_class):
        def is_path(path_str):
            return (
                path_str.startswith("/") or
                path_str.startswith(".") or
                os.path.sep in path_str
            )

        def import_module_from_path(path):
            module_name = os.path.splitext(os.path.basename(path))[0]
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
            raise ImportError(f"Cannot import module from path {path}")

        def list_plugin_files(folder):
            if is_path(folder) and os.path.isdir(folder):
                try:
                    files = os.listdir(folder)
                    return [
                        os.path.splitext(f)[0]
                        for f in files
                        if f.endswith(".py") and not f.startswith("__")
                    ]
                except Exception as e:
                    raise ImportError(f"Error during listing of files in the folder {folder}: {e}")
            else:
                try:
                    spec = importlib.util.find_spec(folder)
                    if spec is None or not spec.origin:
                        raise ImportError(f"Impossible to locate module {folder}")
                    package_path = os.path.dirname(spec.origin)
                    files = os.listdir(package_path)
                    return [
                        os.path.splitext(f)[0]
                        for f in files
                        if f.endswith(".py") and not f.startswith("__")
                    ]
                except Exception as e:
                    raise ImportError(f"Error during listing of files of module {folder}: {e}")

        try:
            if plugin_name == "Multiple":
                modules = []
                plugin_files = list_plugin_files(folder_plugin)

                # Sort alphabetically and place defaultParser at the end
                plugin_files.sort()
                if "DefaultParser" in plugin_files:
                    plugin_files.append(plugin_files.pop(plugin_files.index("DefaultParser")))

                for plugin in plugin_files:
                    if is_path(folder_plugin):
                        full_path = os.path.join(folder_plugin, f"{plugin}.py")
                        module = import_module_from_path(full_path)
                    else:
                        module = importlib.import_module(f"{folder_plugin}.{plugin}")

                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, abstract_plugin_class) and obj is not abstract_plugin_class:
                            modules.append(obj())
                return modules

            else:
                # Simple case : uniq plugin
                if is_path(folder_plugin):
                    full_path = os.path.join(folder_plugin, f"{plugin_name}.py")
                    if not os.path.isfile(full_path):
                        raise FileNotFoundError(f"Plugin file not found: {full_path}")
                    module = import_module_from_path(full_path)
                else:
                    module = importlib.import_module(f"{folder_plugin}.{plugin_name}")

                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, abstract_plugin_class) and obj is not abstract_plugin_class:
                        return obj()

                raise ImportError(f"No valid plugin class found in {plugin_name}.")

        except ModuleNotFoundError as e:
            raise ImportError(f"The module {plugin_name} has not been found.") from e
        except FileNotFoundError as e:
            raise ImportError(f"File not found for plugin {plugin_name}.") from e


    def prepare_id(self):
        try:
            # TODO change it
            #id = (str(time.time()) + str(random.random())).replace(".","")
            id = uindex.create_random_id()
            return id
        except:
            self.logger.log("error",f"Error while preparing id: " + {traceback.format_exc()})
            return None
    
    def prepare_raw_log(self, data):
        try:
            raw = {"data" : {"raw": "","parsed" : {}}}
            raw["data"]["raw"] = base64.b64encode(data.encode('utf-8')).decode('utf-8')
            return raw
        except:
            self.logger.log("error",f"Error while preparing raw log: {traceback.format_exc()}")
            return None
    
    def enrich_log(self, parsed_data, data, id):
        try:
            # print(type(data))
            # data
            data["data"]["parsed"] = parsed_data
            #  prefilter
            data["data"]["parsed"]["prefilter"] = self.prefilter_name
            #  parser
            data["data"]["parsed"]["parser"] = self.parser_name
            #  categorizer
            data["data"]["parsed"]["categorizer"] = self.categorizer_name
            #  agregator
            data["data"]["parsed"]["agregator"] = self.agregator_name
            #  anonymizer
            data["data"]["parsed"]["anonymizer"] = self.anonymizer_name
            #  mapper Used in parser
            # data["data"]["parsed"]["mapper"] = self.mapper_name
            #  postfilter
            data["data"]["parsed"]["postfilter"] = self.postfilter_name
            # timestamp of the reception
            data["data"]["parsed"]["parserReceivedTime"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
            # Device Type
            data["data"]["parsed"]["technology"] = self.parser_technology
            # tag
            # TODO
            # Tenant 
            data["data"]["parsed"]["tenant"] = self.tenant
            # id
            data["data"]["parsed"]["id"] = id
            return data
        except Exception as e:
            self.logger.log("error",f"Error while enriching log: {traceback.format_exc()}")
            return None

    def run(self):
        while self.running:
            try:
                if not self.queue_manager.isFull():
                    # retrieve logs from logcollector
                    data_log = self.collector_requester.retrieve_logs(self.logcollector_size)
                    # TODO erase this
                    # with open("log.txt", "a") as f:
                    #     f.write(str(data_log) + "\nBREAK\n")
                    if data_log is not None and data_log != "" and data_log != "\n":
                        # Split with delimiter
                        # data_splitted = re.split(self.delimiter, data_log)
                        data_splitted = data_log.split(self.delimiter)
                        # result_splitted = [''.join(data_splitted[i:i+2]) for i in range(1, len(data_splitted)-1, 2)]
                        # for data in result_splitted:
                        for data in data_splitted:
                            # TODO find a better way to do this
                            if data is not None and data.strip() != "":
                                data = data.strip()
                                print("DATA:" + str(data))
                                # Clean the data with strip(! without this, bug in the parsing)
                                self.count += 1
                                # prefilter
                                if self.prefilter.filter(data, self.prefilter_filter, self.prefilter_out, self.logger):
                                    # compute id
                                    id = self.prepare_id()
                                    raw_log = self.prepare_raw_log(data)
                                    # Verify parser
                                    # If multiple
                                    used_parser = None
                                    if self.parser_name == "Multiple":
                                        for parser in self.parser:
                                            if parser.verify(data, self.logger):
                                                used_parser = parser
                                                break
                                    else:
                                        used_parser = self.parser
                                    # Send data to parser
                                    parsed_data = used_parser.parse(data, self.logger)
                                    # MAPPING NAME AND VERSION
                                    # PARSER NAME AND VERSION
                                    enriched_data = self.enrich_log(parsed_data, raw_log, id)
                                    # CATEGORIZATION
                                    categorized_data = self.categorizer.categorize(enriched_data, self.logger)
                                    # ANONYMIZATION
                                    anonymized_data = self.anonymizer.anonymize(categorized_data, self.anonymizer_fields, self.logger)
                                    # TODO validate the format json
                                    # TODO agg, post filter... 
                                    # TODO for agregator, enqueue in another one. Other system for agregation
                                    # TODO add default fields
                                    # print(final_data)
                                    # print(final_data)
                                    # TODO add to queue
                                    # TODO to change with post data filter
                                    final_data = anonymized_data
                                    print("FINAL DATA:" + str(final_data))
                                    # print("before enqueue")
                                    self.queue_manager.enqueue(json.dumps(final_data).encode("utf-8"))
                                    # print("data added to queue: " + str(self.queue_manager.get_size()))
                # TODO add this parameter to the config
                time.sleep(0.5)
            except Exception as e:
                self.logger.log("error", f"Error during the process: {traceback.format_exc()}")


if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        client = LogParser('logparserconfig.json', config_loader.get_config())


# problem to resolve -> lost of dat if exception during the process. 
# Shutdown properly the process