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
document: log collector
"""

from ServiceBase import *
from Listener import *
from CMDHandler import *
from Webhook import *
from QueueManager import *
from Configurator import *
from Logger import *
from ParameterLoader import *
import threading
import time
import os, sys, re


class LogCollector(ServiceBase):
    def __init__(self, config_file='logcollectorConfig.json', configuration = None):
        self.configurator = Configurator(config_file, configuration)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        # self.resource_monitor = ResourceMonitor(self.id)
        try:
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.backup_max_file, self.max_backup_file_size, b"$$$BREAK$$$")
            # self.logger = Logger(self.id, self.log_collector_type, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            self.cmdhandler = CMDHandler({
                "configure":self.handle_set_config, 
                "configuration":self.configurator.get_config,
                "retrieve_logs": self.handle_retrieve_logs,
                "shutdown": self.handle_shutdown, 
                "retrieve_monitoring": self.handle_retrieve_monitoring
                })
            # self.webhook =  Webhook(
            #     self.webhook_host, 
            #     self.webhook_port, 
            #     self.cmdhandler.handle_json, 
            #     self.webhook_token, 
            #     self.webhook_certfile,
            #     self.webhook_keyfile)
            # Statistics
            self.avg_enqueue_time = 0
            self.avg_dequeue_time = 0
            self.avg_file_save_time = 0
            self.avg_file_restore_time = 0
            self.count = 0
            self.start_count = time.time()
            self.thread_stats = threading.Thread(target=self._load_stats)
            self.thread_stats.daemon = True
            # self.start_threads()
            self.thread_stats.start()
            if self.log_collector_type == "receiver":
                self.receiver_listener = Listener(self.receiver_host, self.port_receiver, self.handle_receiver, self.proto_receiver)
                self.receiver_listener.start()
            elif self.log_collector_type == "file_reader":
                self.process_file_by_delimiter(self.file_reader_path,  self.file_reader_delimiter)
            # start microservice
            self._start_microservices()
        except:
            self.logger.log("error", f"Error during initialisation of logcollector : {traceback.format_exc()}")

    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
        # TYPE LOG COLLECTOR
        self.log_collector_type = self.config["collector_type"]
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
        # QUEUE
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        self.backup_file = self.config["queue"]["backup_file"]
        self.backup_max_file = self.config["queue"]["max_backup_file"]
        self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
        self.stats_file = self.config["queue"]["stats_file"]
        # RECEIVER
        if self.log_collector_type == "receiver":
            self.receiver_host = self.config["receiver"]["host"]
            self.proto_receiver = self.config["receiver"]["protocol"]
            self.port_receiver = self.config["receiver"]["port"]
            self.listener_timeout = self.config["receiver"]["timeout"]
            self.receiver_certfile = self.config["receiver"]["certs"]["certfile"]
            self.receiver_keyfile = self.config["receiver"]["certs"]["keyfile"]
            self.receiver_delimiter = bytes(self.config["receiver"].get("delimiter","\n"), "utf-8")
        # FILE READER (read file once)
        if self.log_collector_type == "file_reader":
            self.file_reader_path = self.config["file_reader"]["path"]
            self.file_reader_delimiter = self.config["file_reader"]["delimiter"]

    
    def _stop_microservices(self):
        try:
            if self.log_collector_type == "receiver":
                self.receiver_listener.stop()
            # Wait for the queue to be empty
            # TODO find a way to stop properly the queeue manager or send the cache file
            # thread = threading.Thread(target=self.queue_manager.wait_for_empty_queue)
            # thread.daemon = True  
            # thread.start()
            # thread.join(timeout=120)
            # if thread.is_alive():
            #     self.logger.log("error", "Queue did not empty in the expected time.")
            #     return False
            self.webhook.stop()
            self.logger.log("info",f"Stop logcollector microservice")
            return True
        except:
            self.logger.log("error", f"Error during restart of logcollector :  {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.backup_max_file, self.max_backup_file_size, b"$$$BREAK$$$")
            if self.log_collector_type == "receiver":
                self.receiver_listener = Listener(self.receiver_host, self.port_receiver, self.handle_receiver, self.proto_receiver)
            elif self.log_collector_type == "file_reader":
                self.process_file_by_delimiter(self.file_reader_path, self.file_reader_delimiter)
            self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
            self.logger.log("info",f"Start logcollector micoservice")
            return True
        except:
            self.logger.log("error", f"Error during restart of logcollector : {traceback.format_exc()}")
            return False

    def _restart_microservices(self):
        # Restart the logger
        try:
            stopped = self._stop_microservices()
            # Waiting the port to be free
            if stopped:
                return self._start_microservices()
            else:
                self.logger.log("error", f"Error during restart of logcollector : {traceback.format_exc()}")
                return False
        except:
            self.logger.log("error", f"Error during restart of logcollector : {traceback.format_exc()}")
            return False

    def _load_stats(self):
        # TODO get value and create the statistique log
        # TODO complete resource monitoring
        # TODO add value from the queue manager
        while True:
            try:
                # Statistics logcollector
                stats = {
                    "name" : "statistics_monitoring",
                    "type":"logcollector_statistics"
                    # "avg_lc_enqueue_time": float(self.avg_enqueue_time),
                    # "avg_lc_dequeue_time": float(self.avg_dequeue_time),
                    # "avg_lc_file_save_time": float(self.avg_file_save_time),
                    # "avg_lc_file_restore_time": float(self.avg_file_restore_time),
                    # "avg_lc_eps": float(self.count / (time.time() - self.start_count))
                }
                stats.update(self.queue_manager.get_stats())
                # TODO statistics are wrong to correct + stats dict generate decimal that create errors
                # self.logger.log("debug", stats)
                self.count = 0
                self.start_count = time.time()
                time.sleep(10)
            except:
                self.logger.log("error", f"Error during statistics : " + {traceback.format_exc()})

    def handle_receiver(self, conn, data):
        try:
            start_time = time.time()
            self.count += 1
            for line in re.split(self.receiver_delimiter, data):
                if self.queue_manager.enqueue(line):
                    self.avg_enqueue_time += float((time.time() - start_time) / 2)
            # TODO check if error in here. If not erase the 2 following lines
            # else:
            #     file_time = time.time() - start_time
        except:
            self.logger.log("error", f"Failed to enqueue data: {traceback.format_exc()}")

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

    def handle_shutdown(self):
        try:
            # Stop the services receiver listener and wait for the queue to be empty
            self.receiver_listener.stop()
            thread = threading.Thread(target=self.queue_manager.wait_for_empty_queue)
            thread.start()
            thread.join()
            # Stop the running services
            self.thread_stats.join()
            return True
        except:
            self.logger.log("error", f"Failed to shutdown: {traceback.format_exc()}")
            return False

    def handle_retrieve_logs(self, data):
        try:
            start_time = time.time()
            elements = self.queue_manager.dequeue(data["size"])
            self.avg_dequeue_time += float((time.time() - start_time) / 2)
            return elements
        except:
            self.logger.log("error", f"Failed to dequeue data: {traceback.format_exc()}")
            return None
        
    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None
        
    def process_file_by_delimiter(self, file_path, delimiter):
        print("DELIMITER:  " + str(delimiter))
        is_line_delimiter = delimiter in ('\\\\n', '\\\\r\\\\n')
        print("is line delimiter: "+str(is_line_delimiter))
        if is_line_delimiter:
            with open(file_path, 'rb') as f:
                for line in f:
                    # Each line already ends with the delimiter (if present)
                    self.queue_manager.enqueue(line)
        else:
            buffer = []
            delimiter_bytes = delimiter.encode('utf-8')
            with open(file_path, 'rb') as f:
                for line in f:
                    while delimiter_bytes in line:
                        part, line = line.split(delimiter_bytes, 1)
                        buffer.append(part)
                        full_block = b''.join(buffer)
                        self.queue_manager.enqueue(full_block)
                        buffer = []
                    buffer.append(line)
                # End of file
                if buffer:
                    self.queue_manager.enqueue(b''.join(buffer))

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        log_collector = LogCollector("logcollectorConfig.json", config_loader.get_config())
