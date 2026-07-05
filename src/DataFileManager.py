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
document: data file manager
"""

import os, traceback, json, threading, re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import sqlite3, time, portalocker
from pathlib import Path
import Utils as utils
import msgspec, base64
import ijson
import shutil
import tempfile

BATCH_VARIABLE_NUMBER = 500  # Limit by batch

class DataFileManager:
    def __init__(self, base_path, index_name, history_path, logger, max_file_size=1024*1024, max_thread=8, max_index_size=1024, read_write=False):
        self.base_path = base_path
        self.index_modification_file = history_path
        self.index_name = index_name
        self.max_threads = max_thread
        self.lock = threading.Lock()
        self.max_index_size = max_index_size
        self.max_file_size = max_file_size
        self.suffix = 0
        self.count = 0
        self.date_format = utils.DEFAULT_DATE_FORMAT
        self.count_sql_insert = 0
        self.logger = logger 
        self.read_write = read_write

###########################################################
## SECTTION DATABASE INSERTION INDEX PART
##########################################################


    def create_folder_structure(self, tenant, period):
        """Create folders that respect the structure of the index"""
        folder = Path(self.base_path) / self.index_name / "primary" / tenant / period
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _get_data_path(self, tenant, period, parsed=True):
        """Send the path of the current indexing files"""
        file_name = "parsed" if parsed else "raw"
        return Path(self.base_path) / self.index_name / "primary" / tenant / period / f"{file_name}_{self.suffix}.json"

    def _get_file_size(self, file_path):
        """Return the size of the file or 0 if it doesn't exist."""
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0


    def _split_and_store(self, data, tenant, period, parsed=True):
        """Store data in a new file if the other files have reached the maximum size.
        Use a temp file for safe writing before replacing the original file."""
        data_path = None
        try:
            index_dir = Path(self.base_path) / self.index_name / "primary" / tenant / period
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            data_path = self._get_data_path(tenant, period, parsed)
            # Find the first file not full with the highest suffix
            while os.path.exists(data_path) and self._get_file_size(data_path) >= self.max_file_size:
                self.suffix += 1
                data_path = self._get_data_path(tenant, period, parsed)
            if os.path.exists(data_path):
                utils.wait_for_unlock(data_path)
                utils.lock_file(data_path, True)  # Lock file before processing
                try:
                    with open(data_path, 'r') as f:
                        try:
                            existing_data = json.load(f)
                        except json.JSONDecodeError:
                            self.logger.log("error", f"Error during file opening {data_path} - {traceback.format_exc()}")
                            existing_data = {}
                    # Merge or add data according to read_write flag
                    if not self.read_write:
                        for item in data:
                            if item not in existing_data:
                                existing_data[item] = data[item]
                    else:
                        existing_data.update(data)
                    # Write to a temp file first
                    tmp_fd, tmp_path = tempfile.mkstemp(dir=index_dir, prefix="tmp_", suffix=".json")
                    try:
                        with os.fdopen(tmp_fd, 'w') as tmp_file:
                            json.dump(existing_data, tmp_file, indent=4)
                        # Replace the original file by the temp file atomically
                        shutil.move(tmp_path, data_path)
                        utils.add_file_modif_date(self.index_modification_file, data_path)
                    except Exception:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                        raise
                finally:
                    utils.lock_file(data_path, False)  # Unlock file after processing
            else:
                # File does not exist or is full - create new file safely
                print(f"The file {data_path} is full or does not exist, creating a new file...")
                utils.lock_file(data_path, True)
                try:
                    tmp_fd, tmp_path = tempfile.mkstemp(dir=index_dir, prefix="tmp_", suffix=".json")
                    try:
                        with os.fdopen(tmp_fd, 'w') as tmp_file:
                            json.dump(data, tmp_file, indent=4)
                        shutil.move(tmp_path, data_path)
                        utils.add_file_modif_date(self.index_modification_file, data_path)
                    except Exception:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                        raise
                finally:
                    utils.lock_file(data_path, False)
        except Exception:
            if data_path:
                try:
                    utils.lock_file(data_path, False)
                except Exception:
                    pass
            self.logger.log("error", f"Error during split and store: {traceback.format_exc()}")


    def store_log(self, data, parsed=True):
        """
        Save values in files with multithreading.
        Limit number of active thread to self.max_threads
        """
        threads = []
        active_threads = []
        def store_log_thread(tenant, period, tenant_data):
            """
            Function executed by thread to store logs from a tenant and specific period.
            """
            try:
                self.create_folder_structure(tenant, period)
                self._split_and_store(tenant_data, tenant, period, parsed)
                # Update counter
                with self.lock:
                    self.count += 1
            except Exception:
                self.logger.log("error", f"Error while processing {tenant}/{period} {traceback.format_exc()}")
        # Creation threads for each tenant/period
        for tenant in data:
            for period in data[tenant]:
                tenant_data = data[tenant][period]
                thread = threading.Thread(target=store_log_thread, args=(tenant, period, tenant_data))
                threads.append(thread)
        # Start threads with limitation of active threads
        for thread in threads:
            # While number of actives threads is equal to max_threads, wait
            while len(active_threads) >= self.max_threads:
                # Wait finished threads in the active list
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1) # Pause to avoid CPU overload 
            # Start thread and ajust list of active threads
            thread.start()
            active_threads.append(thread)
        # Wait all threads finished
        for thread in active_threads:
            thread.join()


###########################################################
## SECTTION SEARCH IN DATABASE INDEX PART
##########################################################



    def _list_json_files(self, dir_path, prefix):
        """
        List of JSON files in a folder that start with a specific prefix
        """
        if not os.path.exists(dir_path):
            return []
        return [
            os.path.join(dir_path, file)
            for file in os.listdir(dir_path)
            # if file.startswith(prefix) and file.endswith(".json")
            if file.startswith(prefix) and ".json" in file
        ]


    def search_in_files(self, current_time, tenant, file_prefix, ids, raw=False):
        """
        Search Ids in all JSON files corresponding in a folder
        """
        found_ids = []
        hour_str = current_time.strftime(self.date_format)
        dir_path = os.path.join(self.base_path, self.index_name, "primary", tenant, hour_str)
        # List all corresponding file
        json_files = self._list_json_files(dir_path, file_prefix)
        if not json_files:
            print(f"No files found in {dir_path} with prefix {file_prefix}.")
            return found_ids
        try:
                id_set = set(ids)
                for json_file in json_files:
                    try:
                        # TODO change this part in order to not need to modify the history
                        # Make an uncompress, unencrypted copy of the file
                        u_file, is_compressed = utils.uncompress_file_with_copy(json_file)
                        # TODO add encryption part
                        # ue_file = utils.decrypt_file(u_file, self.index_modification_file)
                        # Open the file and read it
                        with open(u_file, 'rb') as f:
                            # Browse pair key/value at root level
                            for key, value in ijson.kvitems(f, ""):
                                if key in id_set:
                                    if raw:
                                        found_ids.append({
                                            "id": key,
                                            "encoding": "base64",
                                            "raw_log": utils.process_base64_to_html_safe(value)
                                        })
                                    else:
                                        found_ids.append(value)
                        # Erase the file after reading it
                        if is_compressed:
                            # Erase the folder parent which is temporary
                            parent_folder = Path(u_file).parent
                            # Delete parent folder
                            shutil.rmtree(parent_folder)
                    except Exception:
                        self.logger.log("error", f"Error while processing the file {json_file} - {traceback.format_exc()}")
        except Exception:
            self.logger.log("error", f"Error during file search in {dir_path} -  {traceback.format_exc()}")
        self.logger.log("debug", f"Found {len(found_ids)} IDs in {dir_path} with prefix {file_prefix}.")
        return found_ids


    def search_data(self, data_json, raw=False):
        """
        Main search in JSON files depending on IDs
        Limitation number of active threads with self.max_threads
        """
        found_ids = []
        print("Search data: " + str(data_json)[:50] + "...")
        grouped_data = defaultdict(list)

        # Return list of data if data are invalids
        if not data_json or len(data_json) == 0:
            return []

        try:
            # Parse data if not a dictionary 
            data = json.loads(data_json) if not isinstance(data_json, dict) else data_json

            # Group data per tenant and date
            for tenant in data:
                for date in data[tenant]:
                    date_obj = date if isinstance(date, datetime) else datetime.strptime(date, self.date_format)
                    grouped_data[(tenant, date_obj)].extend(data[tenant][date])

            file_prefix = "raw" if raw else "parsed"
            threads = []
            active_threads = []

            # Function of researches executed per each threads
            def search_in_files_thread(date, tenant, file_prefix, ids, raw=False):
                start_search_in_file_thread = time.time()
                result = self.search_in_files(date, tenant, file_prefix, ids, raw)
                if result:
                    with self.lock:
                        found_ids.extend(result)
                self.logger.log("debug", f"Search in files time for : {str(date)} - " + str(time.time() - start_search_in_file_thread))

            # Create and start thread for each group (tenant, date)
            start_search_time = time.time()
            for (tenant, date), ids in grouped_data.items():
                thread = threading.Thread(target=search_in_files_thread, args=(date, tenant, file_prefix, ids, raw))
                threads.append(thread)

            # Limit number of active threads
            for thread in threads:
                while len(active_threads) >= self.max_threads:
                    # Update list of active threads with deleting finished one
                    active_threads = [t for t in active_threads if t.is_alive()]
                    time.sleep(0.1)  # Pause to limit overload of CPU

                # Start the thread and add active threads
                thread.start()
                active_threads.append(thread)

            # Wait end of all threads
            for thread in active_threads:
                thread.join()

            self.logger.log("debug", "Search in files time: " + str(time.time() - start_search_time))
            return found_ids

        except RuntimeError:
            print(traceback.format_exc())
            # In case of error, perform a search without threads
            for (tenant, date), ids in grouped_data.items():
                found_ids.extend(self.search_in_files(date, tenant, file_prefix, ids, raw))
        finally:
            return found_ids
        

    def search_in_raw_data(self, query, tenant, start_time, end_time, technology, negative):
        """Search in files the value of the query."""
        found_ids = defaultdict(lambda: defaultdict(list))
        file_prefix = "raw"
        if not query or len(query) == 0:
            return {}
        try:
            # Build path of tenant
            tenant_path = os.path.join(self.base_path, self.index_name, "primary", tenant)
            # List all folders in tenant folder
            if not os.path.exists(tenant_path):
                self.logger.log("debug", f"DataFileManafer Path not found: {tenant_path}")
                return {}
            # Convert start_time and end_time in datetime objects
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S") if start_time else None
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") if end_time else None
            for date_folder in os.listdir(tenant_path):
                date_path = os.path.join(tenant_path, date_folder)
                # Verify if folder correspond to a valid date
                if not os.path.isdir(date_path):
                    continue
                try:
                    folder_date = datetime.strptime(date_folder, utils.DEFAULT_DATE_FORMAT)
                except ValueError:
                    self.logger.log("debug", f"DataFileManager Invalid date folder: {date_folder}")
                    continue
                # Check if date is inside the interval
                if (start_dt and folder_date < start_dt) or (end_dt and folder_date > end_dt):
                    continue
                # List JSON files with specified prefix
                json_files = self._list_json_files(date_path, file_prefix)
                for file_path in json_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            # Search with regex
                            for item in data:
                                item_id = item
                                content = base64.b64decode(data[item]).decode("utf-8")

                                if re.search(query, content):
                                    if negative:
                                        # Verify that query does not correspond
                                        if not re.search(query, content):
                                            found_ids[tenant][date_folder].append(item_id)
                                    else:
                                        found_ids[tenant][date_folder].append(item_id)
                    except Exception as e:
                        self.logger.log("error", f"Error reading file {file_path}: {e}")
            return found_ids
        except Exception as e:
            self.logger.log("errro", f"Error during search in raw logs {traceback.format_exc()}")
            return {}
        
    def list_files_lifecycle(self, days, isjson=True):
        """ list all files where the date is older than the days parameter 
            Data here are encrypted or compressed or deleted.
            If the file is encrypted and access, it will be decrypted and stay unencrypted until the function lifecylce is relaunched
        """
        try:
            files = []
            # Get current date
            current_date = datetime.now()
            # Compute expiration date
            expiration_date = current_date - timedelta(days=days)
            print("expiration_date: ", str(expiration_date))
            # Browse folders in the folders of tenant
            base_folder = os.path.join(self.base_path, self.index_name, "primary")
            print("base path: ", base_folder)
            # Erase the non tenants folders
            list_tenants = os.listdir(base_folder)
            list_tenants.remove("summary.json")
            list_tenants.remove("history.json")
            list_tenants.remove("indices")
            for tenant_folder in list_tenants:
                tenant_path = os.path.join(base_folder, tenant_folder)
                print("tenant_path: ", str(tenant_path))
                if os.path.isdir(tenant_path):
                    for date_folder in os.listdir(tenant_path):
                        date_path = os.path.join(tenant_path, date_folder)
                        if os.path.isdir(date_path):
                            # Check if folder is a valid folder
                            try:
                                folder_date = datetime.strptime(date_folder, utils.DEFAULT_DATE_FORMAT)
                                # print("folder_date: ", str(folder_date))
                            except ValueError:
                                self.logger.log("debug", f"DataFileManager Invalid date folder: {date_folder}")
                                continue
                        # Check if date inside the interval
                        if folder_date < expiration_date:
                            print("date_path inferior: ", str(date_path))
                            lf = os.listdir(date_path)
                            if isjson:
                                lff = [f for f in lf if f.lower().endswith('.json')]
                            else:
                                lff = [f for f in lf]
                            for l in lff:
                                abs_f = os.path.join(date_path, l)
                                # print("abs_f:", str(abs_f))
                                files.append(abs_f)
            print("files: ", str(files))
            return files
        except:
            self.logger.log("error", f"Error during listing files for lifecycles {traceback.format_exc()}")


    def delete_old_data(self, days):
        print("DELETE days: ", str(days))
        if days > 0:
            files = self.list_files_lifecycle(days, isjson=False)
            for file in files:
                try:
                    print("file to remove: ", str(Path(file).parent))
                    # Delete in history the file path (must be done before the folde erased or the history file is not updated)
                    utils.add_file_modif_date(self.index_modification_file, file, True)
                    # Remove the folder
                    shutil.rmtree(Path(file).parent)
                except Exception as e:
                    self.logger.log("error", f"Error during delete old data {traceback.format_exc()}")


    def encrypt_old_data(self, days, key_path, algorithm):
        if days > 0:
            with open(key_path, "rb") as key_file:
                key = key_file.read()
            files = self.list_files_lifecycle(days)
            for file in files:
                try:
                    utils.encrypt_file(file, key, algorithm)
                except Exception as e:
                    self.logger.log("error", f"Error during encrypt old data {traceback.format_exc()}")
                    

    def compress_old_data(self, days, algorithm):
        if days > 0:
            files = self.list_files_lifecycle(days)
            for file in files:
                try:
                    utils.compress_file(file, self.index_modification_file, algorithm)
                except Exception as e:
                    self.logger.log("error", f"Error during compress old data {traceback.format_exc()}")