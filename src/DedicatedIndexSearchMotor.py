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
document: dedicated index search motor
"""

from ServiceBase import *
from IndexFileManager import *
# from SQLFileManager import *
from DataFileManager import *
from Configurator import *
from CMDHandler import *
from Logger import *
from QueueManager import *
import traceback, os, threading
from datetime import datetime, timezone, timedelta
from Webhook import *
from WebRequester import *
from ParameterLoader import *
import msgspec
import base64

class DedicatedIndexSearchMotor(ServiceBase):
    def __init__(self, config_file, config):
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        try:
            self.to_enqueue = []
            self.to_enqueue_raw = []
            self.cmdhandler = CMDHandler({
                "configure": self.handle_set_config, 
                "configuration": self.configurator.get_config, 
                "search_data": self.handle_search_data, 
                "search_index" : self.handle_search_index, 
                "search_in_raw_data": self.handle_search_in_raw_data,
                "search_raw": self.handle_search_raw, 
                "shutdown": self.handle_shutdown, 
                "get_available_indices": self.handle_get_available_indices, 
                "get_available_tenants": self.handle_get_available_tenants, 
                "get_available_technologies": self.handle_get_available_technologies,
                "retrieve_monitoring": self.handle_retrieve_monitoring
                })
            self._start_microservices()
        except:
            self.logger.log("error", "Error during initialization of DedicatedIndexSearchMotor: " + str(traceback.format_exc()))

    def load_configuration(self):
        self.config = self.configurator.get_config()
        # print(str(self.config))
        self.id = self.config["id"]
        self.primary = self.config["primary"]
        # GROUP
        self.group = self.config["group"]
        ## WEBREQUESTER
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
        self.storage_path = self.config["storage"]["path"]
        self.max_file_size = self.config["storage"]["max_file_size"]
        self.index_name = self.config["storage"]["index_name"]
        self.index_size = self.config["storage"]["index_size"]
        self.index_saving_frequency = self.config["storage"]["index_saving_frequency"]
        self.max_threads = self.config["storage"]["max_threads"]
        # QUEUE
        self.backup_file = self.config["queue"]["backup_file"]
        self.stats_file = self.config["queue"]["stats_file"]
        self.max_queue_size = self.config["queue"]["max_queue_size"]
        self.max_backup_file = self.config["queue"]["max_backup_file"]
        self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
        # CACHE SYSTEM
        self.cache_host = None
        if "host" in self.config["cache"]:
            self.cache_host = self.config["cache"]["host"]
            self.cache_port = self.config["cache"]["port"]
            self.cache_token = self.config["cache"]["auth_token"]
        # History 
        self.history_primary_path = Path(self.storage_path) / self.index_name / "primary" / "history.json"
    # TODO system of caching ids -> data and ids -> raw
    # TODO search in raw logs system

    def _load_stats(self):
        # TODO implement this part
        pass

    def handle_retrieve_monitoring(self, data):
        try:
            return self.logger.retrieve_monitoring(data)
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            return None

    def _stop_microservices(self):
        try:
            # Stop the service collectors 
            self.logger.log("info",f"Stop microservices {self.id}")
            self.stop_threads_services()
            # TODO stop the threads for store data in cache
            # Stop the webhook
            self.webhook.stop()
            return True
        except:
            self.logger.log("error", f"Failed to stop microservices: {traceback.format_exc()}")
            return False

    def _start_microservices(self):
        try:
            self.logger.log("info",f"Start microservices {self.id}")
            self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
            self.index_file_manager = IndexFileManager(self.storage_path, self.index_name, None, self.logger, self.max_file_size)
            self.data_file_manager = DataFileManager(self.storage_path, self.index_name, None, self.logger, self.max_file_size)
            if self.cache_host is not None:
                self.wr = WebRequester(self.cache_host, self.cache_port, self.cache_token, slave_reverse=self.slave_reverse)
            self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.max_backup_file, self.max_backup_file_size)
            self.thread_store_cache_data = threading.Thread(target=self.store_data_in_cache)
            self.thread_store_cache_data.daemon = True
            self.thread_store_cache_data.start()
            # TODO restart the threads for cache data
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
        # TODO implement the changing of microservice configuration
        try:
            self.configurator.set_config(data)
            self.load_configuration()        
        except:
            self.logger.log("error", f"Error during handle set config: {traceback.format_exc()}")

    def handle_search_index(self, request):
        """Search ids in indices for basics searches"""
        try:
            print("handle search index: " + str(request) + ":" + str(type(request)))
            # request = json.loads(request)
            query = request["query"]
            tenant = request["tenant"]
            start_time = request["start_time"]
            end_time = request["end_time"]
            index = request["index"]
            negative = request["negative"]
            technology = request["technology"]
            # If not index concerned
            if self.index_name not in index:
                self.logger.log("debug", "Index not concerned : " + str(index) + str(self.index_name))
                return {}
            self.logger.log("info",{"message":"search query", "s_index":str(index), "s_technology":str(technology), "s_query":str(query),"s_tenant":str(tenant),"s_start_time":str(start_time),"s_end_time":str(end_time)})
            # TODO forward all information from the indexer to retrieve data in the file
            start_index_search = time.time()
            res = json.dumps(self.index_file_manager.search_index(query, tenant, start_time, end_time, technology, negative)).encode('utf-8')
            print("========== time search index : " + str(time.time() - start_index_search))
            return res
        except Exception as e:
            self.logger.log("error","Error while searching in index : " + str(e) + str(traceback.format_exc()))
            return {}
        
    def handle_search_in_raw_data(self, request):
        """Search the regex/query/keyzord in the database directly and return the id"""
        try:
            print("SEARCH IN RAW DATA DEDICATED INDEX SEARCH MOTOR ")
            # TODO factorize with the function search_index
            query = request.get("query")
            tenant = request.get("tenant")
            start_time = request.get("start_time")
            end_time = request.get("end_time")
            index = request.get("index")
            negative = request.get("negative")
            technology = request.get("technology")
            if self.index_name not in index:
                self.logger.log("debug", "Index not concerned : " + str(index) + str(self.index_name))
                return {}
            # TODO the tenant is not take into account for now. Find a way to add some important field in the raw json such as siem_timestamp, techno
            self.logger.log("info",{"message":"Search raw logs", "s_index":str(index), "s_technology":str(technology), "s_query":str(query),"s_tenant":str(tenant),"s_start_time":str(start_time),"s_end_time":str(end_time)})
            return json.dumps(self.data_file_manager.search_in_raw_data(query, tenant, start_time, end_time, technology, negative)).encode('utf-8')
        except Exception as e:
            self.logger.log("error","Error while searching in raw : " + str(e) + str(traceback.format_exc()))
            return {}       

    def handle_search_data(self, request, sort_field="siem_timestamp", sort_type="date"):
        """Search logs in database parsed"""
        try:
            print("HANDLE SEARCH DATA " + str(request)[:100])
            ids = request.get("id")
            raw = request.get("raw")
            print("handle search data : " + str(ids)[:100] + ":" + str(type(ids)) + "index_name : " + str(self.index_name))
            start_handle_search_data = time.time()
            if ids is None:
                return json.dumps([]).encode('utf-8')
            # print("HANDLE SEARCH DATA : " + str(ids) + ":" + str(type(ids)) + "index_name : " + str(self.index_name))
            # If Cache system not active, search in database
            if self.cache_host is None:
                final_res = self.data_file_manager.search_data(ids, raw)
            # If cache system active, search in cache and database
            else:
                # TODO if cache is offline, does not work anymore
                start_get_data_from_cache = time.time()
                results = json.loads(self.wr.search_cached_data(self.index_name, ids, raw))
                print("time to get data from cache : " + str(time.time() - start_get_data_from_cache))
                print("results : " + str(results)[:200])
                found = results["found"]
                # print("found : " + str(found))
                not_found = results["not_found"]
                print("not_found : " + str(not_found)[:200])
                data_not_found = {}
                # Remove the found ids from the not found ids
                start_removing_found_ids = time.time()
                # TODO algo wrong ... add everything
                for tenant, timings in ids.items():
                    data_not_found.setdefault(tenant, {})  # Init tenant if absent
                    for timing_key, ids_list in timings.items():
                        # Init timing_key for the tenant if absent
                        data_not_found[tenant].setdefault(timing_key, [])
                        # Add uniq element not found
                        # data_not_found[tenant][timing_key].extend(id_ for id_ in timing_list if id_ not in found)
                        data_not_found[tenant][timing_key].extend(list(set(ids_list)-set(found if len(found) > 0 else [])))
                        data_not_found[tenant][timing_key] = list(set(data_not_found[tenant][timing_key]))
                print("time to remove found ids : " + str(time.time() - start_removing_found_ids))
                start_find_data_in_db = time.time()
                new_data_found = self.data_file_manager.search_data(data_not_found, raw)
                print("time to find data in db : " + str(time.time() - start_find_data_in_db))
                final_res = results["data"]
                final_res += new_data_found
                # print("data_found : " + str(len(data_found)))
                # TODO use a thread for this part
                start_store_data_in_cache = time.time()
                # self.queue_manager.enqueue(json.dumps(new_data_found).encode("utf-8"))
                # self.to_enqueue = json.dumps(new_data_found).encode("utf-8")
                if raw:
                    # print("DEDICATED SEARCH DATA RAW " + str(final_res))
                    self.to_enqueue_raw = msgspec.json.encode(new_data_found)
                else:
                    # print("DEDICATED SEARCH DATA PARSED " + str(final_res))
                    self.to_enqueue = msgspec.json.encode(new_data_found)
                # self.wr.store_cached_data(self.index_name, new_data_found)
                print("time to store data in cache : " + str(time.time() - start_store_data_in_cache))
                # TODO verify that the request is coming from the indexer and not a user.
                # return self.sql_file_manager.search_data(ids)
                # TODO test this part
            # TODO manage other sort types
            if sort_type == "date":
                start_order_date = time.time()
                # print("final_res : " + str(final_res))
                # TODO find a way to optimise this part (for now most fast way is to order by date)
                if raw:
                    sorted_results = sorted(final_res, key=lambda x: x["id"], reverse=False)
                else:
                    print("TO BE SORTED: " + str(final_res)[:300] + "...")
                    #sorted_results = sorted(final_res, key=lambda x: datetime.strptime(x[sort_field], "%Y-%m-%d %H:%M:%S.%f"), reverse=False)
                    sorted_results = utils.sort_records(final_res, sort_field)
                print("time to order by date : " + str(time.time() - start_order_date))
                print("time to handle search data : " + str(time.time() - start_handle_search_data))
                return sorted_results
            else:
                return final_res
        except Exception as e:
            self.logger.log("error", "Error while searching in database : " + str(e) + str(traceback.format_exc()))
            return []

    def handle_search_raw(self, ids, tenant):
        """Search logs in database raw"""
        try:
            # TODO verify that the request is coming from the indexer and not a user.
            return self.data_file_manager.search_data(ids, True)
        except Exception as e:
            self.logger.log("error", "Error while searching in database : " + str(e) + str(traceback.format_exc()))
            return []

    def store_data_in_cache(self):
        """Store data in cache"""
        while True and self.cache_host is not None:
            try:
                # data = self.queue_manager.dequeue(self.max_queue_size)
                # if data and data != "" and data != {}:
                    # self.wr.store_cached_data(self.index_name, json.loads(data))
                if len(self.to_enqueue) > 0:
                    if self.wr.store_cached_data(self.index_name, json.loads(self.to_enqueue)):
                        self.to_enqueue = {}
                if len(self.to_enqueue_raw) > 0:
                    if self.wr.store_cached_data(self.index_name, json.loads(self.to_enqueue_raw), True):
                        self.to_enqueue_raw = {}
                time.sleep(5)
            except:
                self.logger.log("error", f"Error while storing data in cache : {traceback.format_exc()}")
                time.sleep(1)

    def handle_get_available_indices(self, data):
        """Handle get available indices"""
        # TODO add verification of the user token
        return self.index_name
    
    def handle_get_available_tenants(self, data):
        """Handle get available tenants"""
        # TODO add verification of the user token
        tenants = self.index_file_manager.get_available_tenants()
        print("Tenants : " + str(tenants))
        return tenants 
    
    def handle_get_available_technologies(self, data):
        """Handle get available technologies"""
        # TODO add verification of the user token
        tech = self.index_file_manager.get_available_technologies()
        print("Technologies : " + str(tech))
        return tech


if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():
        client = DedicatedIndexSearchMotor('dedicatedindexesearchmotorconfig.json', config_loader.get_config())   

    