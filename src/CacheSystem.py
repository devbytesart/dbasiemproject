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
document: cache system
"""

from ServiceBase import *
from Configurator import *
from CMDHandler import *
from Logger import *
from datetime import datetime, timezone, timedelta
from Webhook import *
from WebRequester import *
from ParameterLoader import *
import traceback, os, threading, re


class CacheSystem(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            # self.dic_ids => {id:data, id2:data2, ...}
            self.dic_ids = {}
            self.dic_raw_ids = {}
            self.dic_ids_num_data = 0
            self.dic_ids_raw_num_data = 0
            # TODO add store requests and responses query 
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "search_cached_data": self.handle_get_ids, 
                "store_cached_data": self.handle_store_ids, 
                "shutdown": self.handle_shutdown, 
                "retrieve_monitoring": self.handle_retrieve_monitoring
            })
            self.webhook =  Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
        except:
            self.logger.log("error", "Error during initialization of CacheSystem" + str(traceback.format_exc()))

    def load_configuration(self):
        self.config = self.configurator.get_config()
        self.id = self.config["id"]
        ## WEBREQUESTER 
        # TODO use it for commmunication with other cache systems
        self.proxies = self.config["webrequester"]["proxy"]
        self.timeout = self.config["webrequester"]["timeout"]
        self.slave_reverse = self.config["webrequester"].get("slave_reverse")
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
        # Storage
        self.dic_ids_max_data = self.config["storage"]["max_cache_items"]
        self.index = self.config["storage"]["index_name"]

    def _load_stats(self):
        # TODO implement this part
        pass
    
    def _stop_microservices(self):
        try:
            self.logger.log("info",f"Stop microservices {self.id}")
            self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Failed to stop microservices: {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            self.info("info",f"Start microservices {self.id}")
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
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

    def handle_shutdown(self):
        return self._stop_microservices()

    def handle_set_config(self, data):
        # TODO implement the change and reinit of the microservices
        try:
            self.configurator.set_config(data)
            self.load_configuration()
            self._restart_microservices()
        except:
            self.logger.log("error", "Error during handle_set_config of CacheSystem" + str(traceback.format_exc()))

    def handle_store_ids(self, data, raw=False):
        """Store a dictionary of ids and data. Format data : [data0, data1, data2, ...]
        ids in parameter format : [id1, i2,  ...]
        """
        try:
            start_storing_cache = time.time()
            p_data = data.get("data")
            print("p_data : ", str(data["data"])[:100])
            index_name = data.get("index_name")
            raw = data.get("raw")
            if raw:
                dictionary = self.dic_raw_ids
                dictionary_num = self.dic_ids_raw_num_data
            else:
                dictionary = self.dic_ids
                dictionary_num = self.dic_ids_num_data
            if index_name != self.index:
                return False
            for d in p_data:
                # d = json.loads(d)
                if d["id"] not in dictionary and dictionary_num < self.dic_ids_max_data:
                    dictionary[d["id"]] = json.dumps(d)
                    dictionary_num += 1
            # print("dic_ids_num_data : ", self.dic_ids_num_data)
            self.logger.log("error",f"Storing cache time : {time.time() - start_storing_cache}")
            return True
        except Exception as e:
            self.logger.log("error", "Error in handle store ids:" + str(traceback.format_exc()))
            return False

    def handle_get_ids(self, data):
        """Get a dictionary of ids and data
            return found_ids, not_found_ids, data_found
        """
        try:
            start_get_ids_cache = time.time()
            ids = data.get("ids")
            index_name = data.get("index_name")
            raw = data.get("raw")
            if raw:
                dictionary = self.dic_raw_ids   
            else:
                dictionary = self.dic_ids     
            searched_ids = []
            for tenant in ids:
                for timing in ids[tenant]:
                    for d in ids[tenant][timing]:
                        searched_ids.append(d)
            # TODO get data and ids
            # TODO check if index is corresponding to the self.index, if not not registering
            if index_name != self.index or len(searched_ids) == 0:
                return {"found": [], "not_found": searched_ids,  "data": []}
            # TODO check with others instances of CacheSystem if the data is already in the cache
            # TODO threads to search faster in the index
            not_found = []
            found = []
            data_found = []
            for d in searched_ids:
                if d in dictionary:
                    data_found.append(json.loads(dictionary[d]))
                    found.append(d)
                else:
                    not_found.append(d)
            self.logger.log("debug",f"not found : {str(len(not_found))} found : {str(len(found))}")
            self.logger.log("debug",f"time get ids cache: {str(time.time() - start_get_ids_cache)}")
            return {"found":found, "not_found": not_found, "data": data_found}
        except:
            self.logger.log("error", f"Error during handle get ids: {traceback.format_exc()}")
            return {"found": [], "not_found": searched_ids,  "data": []}
    
    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def free_cache(self):
        """Free the cache from the cache system"""
        try:
            self.logger.log("info",f"Freeing cache {self.id}")
            # TODO regularly free the cache depending on the new data arriving
            self.dic_ids = {}
            self.dic_raw_ids = {}
            self.dic_ids_num_data = 0
            self.dic_ids_raw_num_data = 0
        except:
            self.logger.log("error", "Error during free cache:" + str(traceback.format_exc()))
        
if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        client = CacheSystem('cachesystemconfig.json', config_loader.get_config())