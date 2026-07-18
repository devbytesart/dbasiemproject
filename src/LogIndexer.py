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
document: log indexer
"""

from ServiceBase import *
from WebRequester import *
from Configurator import *
from QueueManager import QueueManager
from CMDHandler import *
from Logger import *
from IndexFileManager import *
# SQLFileManager won't be required
# from SQLFileManager import *
from DataFileManager import *
from Webhook import *
from ParameterLoader import *
import time
import traceback
from datetime import datetime, timezone, timedelta
import os, threading, copy
from pathlib import Path
import Utils as utils

class LogIndexer(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "retrieve_logs": self.handle_retrieve_logs, 
                "retrieve_monitoring": self.handle_retrieve_monitoring,
                "shutdown": self.handle_shutdown, 
                "get_history": self.handle_get_history, 
                "download_data": self.handle_download_data})
            ## Create the index and cache data itself
            self.date_format = utils.DEFAULT_DATE_FORMAT
            self.lock = threading.Lock()
            self.index = {}
            self.cache_parsed_data = {}
            self.cache_raw_data = {}
            self.thread_stop = threading.Event()
            self.index_changed = True
            self.thread = threading.Thread(target=self.save_index)
            # self.thread.start()
            # statistics 
            self.count = 0
            self.count_error = 0
            # Launch the main function
            self.running = True
            self.threads_services = []
            self.thread_services_stop = threading.Event()
            # self._start_threads_services()
            # lifecylce 
            # self.lifecycle_running = True
            # Timing of run
            self.primary_frequency = 0.5
            self.secondary_frequency = 30
            # self.run()
            self._start_microservices()
        except:
            self.logger.log("error", "Error during initialization of LogIndexer" + str(traceback.format_exc()))

    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
        # Writable ? by default only readable index
        self.read_write = utils.convert_param_type(self.config["read_write"]["write"],bool)
        if self.read_write:
                print("read write TRUE")
        else:
            print("read write FALSE")
        # INDEX LIFECYLE
            # lifecycle
        self.lifecycle_frequency = int(self.config["lifecycle"]["frequency"])
            # Encryption
        self.encryption_delay = int(self.config["encryption"]["delay"])
        self.encryption_algorithm = self.config["encryption"]["algorithm"]
        self.encryption_key_path = self.config["encryption"]["key_path"]
        self.encryption_iv_path = self.config["encryption"]["iv_path"]
            # compression
        self.compression_delay = int(self.config["compression"]["delay"])
        self.compression_algorithm = self.config["compression"]["algorithm"]
            # deletion
        self.deletion_delay = int(self.config["deletion"]["delay"])
        # self.primary = self.config["primary"]
        # self.indexer_monitoring = self.config["monitoring"]
        # LOGGER
        self.monitoring_log_level = self.config["logger"]["log_level"]
        self.monitoring_log_path = self.config["logger"]["log_path"]
        self.monitoring_max_queue_size = self.config["logger"]["max_queue_size"]
        self.monitoring_max_file = self.config["logger"]["max_file"]
        self.monitoring_max_file_size = self.config["logger"]["max_file_size"]
        self.monitoring_enable_print = utils.convert_param_type(self.config["logger"]["enable_print"], bool)
        self.monitoring_enable_file = utils.convert_param_type(self.config["logger"]["enable_file"], bool)
        self.monitoring_enable_queue = utils.convert_param_type(self.config["logger"]["enable_queue"], bool)
        # TODO complete the logger information
        # WEBHOOK
        self.webhook_host = self.config["webhook"]["host"]
        self.webhook_port = self.config["webhook"]["port"]
        self.webhook_token = self.config["webhook"]["auth_token"]
        self.webhook_certfile = self.config["webhook"]["certs"]["certfile"]
        self.webhook_keyfile = self.config["webhook"]["certs"]["keyfile"]
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        # Web Requester
        ## WEBREQUESTER
        self.proxies = self.config["webrequester"]["proxy"]
        self.timeout = self.config["webrequester"]["timeout"]
        self.slave_reverse = self.config["webrequester"].get("slave_reverse")
        # TODO authorize several "logparser"
        self.logservices = []
        self._initiate_logservices()
        # print("LOGSERVICES: ", str(self.logservices))
        # Queue
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        self.backup_file = self.config["queue"]["backup_file"]
        self.max_backup_file = self.config["queue"]["max_backup_file"]
        self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
        # Storage
        self.storage_path = self.config["storage"]["path"]
        self.max_file_size = self.config["storage"]["max_file_size"]
        self.index_name = self.config["storage"]["index_name"]
        self.index_size = self.config["storage"]["index_size"]
        self.index_saving_frequency = self.config["storage"]["index_saving_frequency"]
        self.max_threads = self.config["storage"]["max_threads"]
        # History 
        self.history_primary_path = Path(self.storage_path) / self.index_name / "primary" / "history.json"
        self.history_secondary_path = Path(self.storage_path) / self.index_name / "secondary" / "history.json"

    def _initiate_logservices(self):
        """ Initiate the logservices """
        try:
            self.logservices = []
            if "logservices" in self.config:
                for logs in self.config["logservices"]:
                    self.logservices.append({
                                            "id":logs["id"],    
                                            "host":logs["host"], 
                                            "port":logs["port"], 
                                            "auth_token": logs["auth_token"],
                                            "size":logs["size"], 
                                            "primary":logs["primary"], 
                                            "monitoring":logs["monitoring"],
                                            "timeout":logs["timeout"],
                                            "mapping": None, 
                                            "webrequester": None,
                                            "webrequester_bin": None, 
                                            "compressed": None
                                            })
                self.running = True
            else:
                self.running = False
        except:
            self.logger.log("error", f"Error during initiation of LogIndexer {traceback.format_exc()}")


    def _start_threads_services(self):
        """Launch threads for each log service."""
        for log_service_id in range(len(self.logservices)):
            try:
                self.logger.log("info", f"Starting thread for log service " + str(self.logservices[log_service_id]))
                thread = threading.Thread(
                    target=self._initialize_log_service,
                    args=(log_service_id,)
                )
                thread.daemon = True  # Ensures threads exit when the main program exits
                self.threads_services.append(thread)
                thread.start()
            except:
                self.logger.log("error",f"Error during launch logservice {traceback.format_exc()}")

    def _initialize_log_service(self, log_service_id):
        # For mapping
        elem = self.logservices[log_service_id]
        elem["webrequester"] = WebRequester(elem["host"], elem["port"], elem["auth_token"], slave_reverse=self.slave_reverse)
        if elem["primary"]:
            # Get the mapping only if primary
            elem["mapping"] = None
            if not elem["monitoring"]:
                while elem["mapping"] is None:
                    try:
                        self.logger.log("debug", f"Waiting for mapping for service {elem['id']}")
                        elem["mapping"] = json.loads(elem["webrequester"].retrieve_mapping(retry=30))
                    except:
                        self.logger.log("debug",f"Error while retrieving mapping, retrying... for service {elem['id']}")
                        time.sleep(1)
        # Running service run
        # TODO change this part as the webrequester is not dependant of the webhook url
        elem["webrequester_bin"] = WebRequester(elem["host"], elem["port"], elem["auth_token"], slave_reverse=self.slave_reverse)
        elem["compressed"] = WebRequester(elem["host"], elem["port"], elem["auth_token"], slave_reverse=self.slave_reverse)
        self.run(elem)

    def stop_threads_services(self):
        """Stop all threads gracefully."""
        try:
            self.running = False
            self.thread_services_stop.set()
            for thread in self.threads_services:
                thread.join()
            self.logger.log("info", "All threads stopped.")
        except:
            self.logger.log("error", f"Error during closing threads: {traceback.format_exc()}")

    def _load_stats(self):
        # TODO implement this part
        pass

    def _start_index_lifecycle(self):
        try:
            self.lifecycle_running = True
            self.thread_lifecycle = threading.Thread(target=self._index_lifecycle)
            self.thread_lifecycle.start()
        except:
            self.logger.log("error", f"Error during starting lifecycle: {traceback.format_exc()}")

    def _stop_index_lifecycle(self):
        try:
            self.lifecycle_running = False
            self.thread_lifecycle_stop.set()
            self.thread_lifecycle.join()
        except:
            self.logger.log("error",f"Error during stopping lifecycle: {traceback.format_exc()}")

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

    def _stop_microservices(self):
        try:
            # Stop the service collectors 
            self.stop_threads_services()
            # Wait for the queue to be empty
            self._stop_index_lifecycle()
            # thread = threading.Thread(target=self.queue_manager.wait_for_empty_queue)
            # thread.start()
            # thread.join()
            # Stop the webhook
            print("STOP MICROSERVICE WEBHOOK")
            self.webhook.stop()
            print("AFTER STOPPING MICROSERVICES WEBHOOK")
            return True
        except:
            self.logger.log("error", f"Failed to stop microservices: {traceback.format_exc()}")
            return False


    def _start_microservices(self):
        try:
            print("call start microservices")
            self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            self.index_file_manager = IndexFileManager(self.storage_path, self.index_name, self.history_primary_path, self.logger, self.max_file_size, self.max_threads, self.index_size, self.read_write)
            self.data_file_manager = DataFileManager(self.storage_path, self.index_name, self.history_primary_path, self.logger, self.max_file_size, self.max_threads, self.index_size, self.read_write)
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.max_backup_file, self.max_backup_file_size, self.logger)
            self._start_threads_services()
            self._start_index_lifecycle()
            self.thread.start()
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

    def save_index(self):
        while not self.thread_stop.is_set():
            try:
                if self.index_changed:
                    with self.lock:
                        start = time.time()
                        print("Saving index:" + str(len(str(self.index))))
                        self.index_file_manager.store_index(copy.deepcopy(self.index))
                        self.index = {}
                        self.data_file_manager.store_log(copy.deepcopy(self.cache_parsed_data))
                        self.cache_parsed_data = {}
                        self.data_file_manager.store_log(copy.deepcopy(self.cache_raw_data), False)
                        self.cache_raw_data = {}
                        self.index_changed = False
                        print("Index saved: " + str(time.time() - start))
                time.sleep(self.index_saving_frequency)
            except:
                self.logger.log("error", f"Failed to save index: {traceback.format_exc()}")
    
    def stop_saving_index(self):
        try:
            self.thread_stop.set()
            self.thread.join()
        except:
            self.logger.log("error", f"Failed to stop saving index: {traceback.format_exc()}")

    def enrich_log(self, data):
        try:
            print("enrich log data: ", str(data))
            # reception timestamp
            data["data"]["parsed"]["indexerReceivedTime"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
            # index name
            data["data"]["parsed"]["index"] = self.index_name
            return data
        except:
            self.logger.log("error", f"Failed to enrich log: {traceback.format_exc()}")
            return data

    def handle_retrieve_logs(self, data, log_service):
        try:
            # Log enrichment
            enriched_data = self.enrich_log(data)
            # Extract tenant and timing
            ## TENANT
            tenant = data["data"]["parsed"]["tenant"]
            ## TIMING
            # TODO handle when no mapping
            ## Define default timestamp based on mapping (@timestamp)
            if log_service["mapping"] is not None:
                if "default_timestamp" in log_service["mapping"]:
                    default_timestamp = log_service["mapping"]["default_timestamp"]
                    dt_format = log_service["mapping"]["fields"][default_timestamp]["format"]
                    if log_service["mapping"]["default_timestamp"] in data["data"]["parsed"]:
                        timing = self.timestamp_to_datetime(int(data["data"]["parsed"][default_timestamp]),dt_format)
                        # Change rt for formatted value
                        # data["data"]["parsed"][default_timestamp] = timing -> changed to siem_timestamp
                        data["data"]["parsed"]["siem_timestamp"] = timing
                    else:
                        timing = data["data"]["parsed"]["parserReceivedTime"]
                else:
                    timing = data["data"]["parsed"]["parserReceivedTime"]
                data["data"]["parsed"]["siem_timestamp"] = timing
                # Add siem_timestamp in mapping
                # TODO change error between type as table in the mapping and str here
                log_service["mapping"]["fields"]["siem_timestamp"] = {"type": "timestamp", "format": "%Y-%m-%d %H:%M:%S.%f"}
            else:
                timing = data["data"]["parsed"]["siem_timestamp"]
            ## Format timing
            period = datetime.strptime(timing, "%Y-%m-%d %H:%M:%S.%f").strftime(self.date_format)
            # Log storage
            # TODO thread for this function
            # self.sql_file_manager.store_log(enriched_data, tenant, period)
            # Create index
            self.indexing(enriched_data, tenant, period, log_service)
            # Create parsed and raw data
            self.indexing_data(enriched_data, tenant, period)
            # return data
            # TODO maybe not required to return data
            return enriched_data
        except Exception as e:
            self.logger.log("error", f"Failed to handle retrieve logs: {traceback.format_exc()}")
            #TODO send something else

    def indexing_data(self, enriched_data, tenant, period):
        try:
            # Create parsed data
            if tenant not in self.cache_parsed_data:
                self.cache_parsed_data[tenant] = {}
            if period not in self.cache_parsed_data[tenant]:
                self.cache_parsed_data[tenant][period] = {}
            self.cache_parsed_data[tenant][period][enriched_data["data"]["parsed"]["id"]] = enriched_data["data"]["parsed"]
            # Create raw data
            if tenant not in self.cache_raw_data:
                self.cache_raw_data[tenant] = {}
            if period not in self.cache_raw_data[tenant]:
                self.cache_raw_data[tenant][period] = {}
            self.cache_raw_data[tenant][period][enriched_data["data"]["parsed"]["id"]] = enriched_data["data"]["raw"]
        except:
            self.logger.log("error", f"Failed to indexing data: {traceback.format_exc()}")


    def send_info_coordinator(self, data):
        pass

    def timestamp_to_datetime(self, timestamp, format):
        try:
            # If timestamp is big, supose that is Windows timestamp
            if timestamp > 10**12: 
                # Windows timestamp
                # epoch_start = datetime(1601, 1, 1, 0, 0, 0)
                # windows_to_unix_factor = 10**7  # 100 nanosecondes
                # seconds = timestamp / windows_to_unix_factor
                # return datetime.fromtimestamp(seconds,timezone.utc).strftime(format)
                timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp, timezone.utc).strftime(format)
            else:
                # Unix timestamp
                return datetime.fromtimestamp(timestamp,timezone.utc).strftime(format)
        except:
            self.logger.log("error", f"Failed to convert timestamp to datetime: {traceback.format_exc()}")
            return timestamp

    def indexing(self, data, tenant, timing, log_service):
        # format of the index is :
        ## index_name
        ## -> tenant {}
        ## --> Timing {}
        ### ---> DeviceType {}
        ### ---> Fields {}
        #### ----> values {}
        ##### -----> Array of id []
        with self.lock:
            try:
                # print("=======" + str(data))
                # TENANT
                if tenant not in self.index:
                    self.index[tenant] = {}
                # TIMING
                if timing not in self.index[tenant]:
                    self.index[tenant][timing] = {}
                # DEVICE TYPE
                techno = data["data"]["parsed"]["technology"]
                if techno not in self.index[tenant][timing]:
                    self.index[tenant][timing][techno] = {}
                # FIELDS
                # TODO verify that the index mapping is present
                for field, value in data["data"]["parsed"].items():
                    # print(field,value)
                    # Ignore tenant and device type and id as already done before
                    # if field == "id" or field == "tenant" or field == "technology":
                        # continue
                    if log_service["mapping"] is not None:
                        if field in log_service["mapping"]["fields"]:
                            # Create fields
                            if field not in self.index[tenant][timing][techno]:
                                self.index[tenant][timing][techno][field] = {}
                            # Create type fields
                            if "type" in log_service["mapping"]["fields"][field]:
                                self.index[tenant][timing][techno][field]["type"] = log_service["mapping"]["fields"][field]["type"]
                            if "format" in log_service["mapping"]["fields"][field]:
                                self.index[tenant][timing][techno][field]["format"] = log_service["mapping"]["fields"][field]["format"]
                            # Create values
                            if "values" not in self.index[tenant][timing][techno][field]:
                                self.index[tenant][timing][techno][field]["values"] = {}
                            # Add the value in the field
                            # print("value:" + str(value))
                            # print(self.index[tenant][timing][techno][field]["values"])
                            if value not in self.index[tenant][timing][techno][field]["values"]:
                                self.index[tenant][timing][techno][field]["values"][value] = []
                            # Add id in the value.
                            self.index[tenant][timing][techno][field]["values"][value].append(data["data"]["parsed"]["id"])
                    # TODO optimise the code as repetitions
                    else:
                        # Create fields
                        if field not in self.index[tenant][timing][techno]:
                            self.index[tenant][timing][techno][field] = {}
                        if "type" not in self.index[tenant][timing][techno][field]:
                            if field == "siem_timestamp":
                                self.index[tenant][timing][techno][field]["type"] = ["timestamp"]
                            #TODO complete with other important types
                            else:
                                self.index[tenant][timing][techno][field]["type"] = ["keyword"]
                        if "values" not in self.index[tenant][timing][techno][field]:
                            self.index[tenant][timing][techno][field]["values"] = {}
                        if value not in self.index[tenant][timing][techno][field]["values"]:
                            self.index[tenant][timing][techno][field]["values"][value] = []
                        self.index[tenant][timing][techno][field]["values"][value].append(data["data"]["parsed"]["id"])
            except Exception:
                self.logger.log("error", f"Error during indexing: {traceback.format_exc()}")
        # Set variable changed to true
        self.index_changed = True

    def handle_get_history(self, data):
        """ Return the file history of file modification """
        try:
            index_name = data["index_name"]
            if index_name != self.index_name:
                return None
            else:
                # TODO test if folders are created and created in case
                with open(self.history_primary_path) as f:
                    return json.loads(f.read())
        except Exception:
            self.logger.log("error", f"Error during getting history: {traceback.format_exc()}")
            return None
        
    def handle_download_data(self, data):
        """ Return the files of indices and data modified """
        try:
            print("HANDLE DATA:" + str(data))
            index_name = data["index_name"]
            file_path = data["file_path"]
            if index_name != self.index_name:
                self.logger.log("error", f"Error in getting file index_name does not match: {traceback.format_exc()}")
                return None
            else:
                # TODO test if file locked is required
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception:
            self.logger.log("error", f"Error during sending data file : {traceback.format_exc()}")
            return None

    def run(self, log_service):
        while self.running:
            try:
                if log_service["primary"]:
                    # get data from log parser
                    if log_service["monitoring"]:
                        received_data = log_service["webrequester_bin"].retrieve_monitoring(log_service["size"])
                    else:
                        received_data = log_service["webrequester_bin"].retrieve_logs(log_service["size"], self.index_name)
                    if received_data is not None:
                        # print("Received data: " + str(received_data))
                        data = json.loads(received_data)
                        self.logger.log("debug", f"Received data {str(len(data))} for {log_service}")
                        # decode data
                        if data and type(data) == type(list()):
                            for d in data:
                                self.count += 1
                                # print("Counter: " + str(self.count))
                                # print(str(d))
                                # handle the data and perform all actions on logs
                                self.handle_retrieve_logs(d, log_service)
                                # print(enriched_data)
                        # print temp index
                        else:
                            raise Exception("Received data is not a list:" + str(d))
                    # TODO add this parameter in the config file
                    time.sleep(0.5)
                else:
                    # TODO add the copy of the summary.json
                    # If log service is not primary, copy the indices and file in the storage
                    log_service_history = log_service["webrequester"].get_history(self.index_name)
                    if log_service_history is not None:
                        log_service_history = json.loads(log_service_history)
                    print("LOG SERVICE HISTORY - " + str(log_service_history) + "type:" + str(type(log_service_history)))
                    # If history secondary does not exist, create it
                    if not os.path.isfile(self.history_secondary_path):
                        if not os.path.exists(self.history_secondary_path.parent):
                            os.makedirs(self.history_secondary_path.parent)
                        with open(self.history_secondary_path, "w") as f:
                            f.write("{}")
                        history = {}
                    # Open and read the history file
                    else:
                        try:
                            with open(self.history_secondary_path) as f:
                                history = json.loads(f.read())
                        except:
                            history = {}
                    print("History: " + str(history) + "type: " + str(type(history)))
                    # TODO resolve the problem with compare_dicts here
                    modified_files = utils.compare_dicts(history, log_service_history)
                    print("Modified files: " + str(modified_files))
                    # TODO factorise this code
                    for k in modified_files["added"]:
                        to_download = k
                        print("Downloading file: " + to_download)
                        self.download_file(to_download, log_service, log_service_history[k]["checksum"])
                        # Modify the history file
                        utils.add_file_modif_date(self.history_secondary_path, to_download)
                    for k in modified_files["modified"]:
                        if "checksum" in modified_files["modified"][k]["modified"]:
                            to_download = k
                            print("Downloading file: " + to_download + " with checksum: " + log_service_history[k]["checksum"])
                            self.download_file(to_download, log_service, log_service_history[k]["checksum"])
                            # Modify the history file
                            utils.add_file_modif_date(self.history_secondary_path, to_download)
                    for k in modified_files["removed"]:
                        to_remove = k
                        print("Removing file: " + to_remove)
                        # Remove file
                        new_path = Path(self.history_secondary_path.parent) / Path(to_remove).relative_to("/")
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        # Update file 
                        utils.add_file_modif_date(self.history_secondary_path, to_remove, True)
                    # TODO change this timestep to a longer parameter
                    time.sleep(30)
            except Exception as e:
                self.count_error += log_service["size"]
                self.logger.log("error", f"Error during main function run : {traceback.format_exc()}")
                # TODO use constant defined in the config file or in the init
                if log_service["primary"]:
                    time.sleep(self.primary_frequency)
                else:
                    time.sleep(self.secondary_frequency)

    def download_file(self, file_name, log_service, checksum):
        """ Download data file """ 
        try:
            data = log_service["compressed"].download_data(self.index_name, file_name)
            if data is not None:
                new_path = Path(self.history_secondary_path.parent) / Path(file_name).relative_to("/")
                utils.create_folders(new_path)
                with open(new_path, "wb") as f:
                    f.write(data)
                checksum_sec = utils.calculate_checksum(new_path)
                if checksum_sec is None:
                    print("Checksum_sec is None")
                else:
                    print("Checksum_sec: " + str(checksum_sec))
                if checksum_sec is None or checksum_sec != checksum:
                    self.logger.log("error", f"Checksum error for file {new_path}: {traceback.format_exc()}")
        except:
            utils.lock_file(new_path, False)
            self.logger.log("error", f"Error during download file function run : {traceback.format_exc()}")


    def _index_lifecycle(self):
        """ Main function for the index lifecycle """
        try:
            self.logger.log("info", "Starting index lifecycle")
            while self.lifecycle_running:
                # Deletion policy index
                try:
                    self.index_file_manager.delete_old_index(self.deletion_delay)
                except:
                    self.logger.log("error", f"Error during deletion policy index function run : {traceback.format_exc()}")
                # Deletion policy data
                try:
                    print("Deletion policy")
                    self.data_file_manager.delete_old_data(self.deletion_delay)
                except:
                    self.logger.log("error", f"Error during deletion policy data function run : {traceback.format_exc()}")
                # Encrpytion policy
                # TODO implement this part (data)
                # Compression policy
                try:
                    self.data_file_manager.compress_old_data(self.compression_delay, algorithm=self.compression_algorithm)
                except:
                    self.logger.log("error", f"Error during compression policy function run : {traceback.format_exc()}")
                # TODO implement the timesleep with the configuration file
                time.sleep(self.lifecycle_frequency)
        except:
            self.logger.log("error", f"Error during index lifecycle function run : {traceback.format_exc()}")

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():    
        client = LogIndexer('logindexerconfig.json', config_loader.get_config())      