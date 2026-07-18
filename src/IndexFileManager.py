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
document: index file manager
"""

import os, traceback, json, threading, re, copy
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from dateutil import parser
import sqlite3, time
# , portalocker
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import Utils as utils
import msgspec
import itertools
import tempfile
import shutil

class IndexFileManager:
    def __init__(self, base_path, index_name, history_path, logger, max_file_size=1024*1024, max_thread=8, max_index_size=1024, read_write=False):
        self.base_path = base_path
        self.index_modification_file = history_path
        self.index_name = index_name
        self.max_thread = max_thread
        self.lock = threading.Lock()
        self.max_index_size = max_index_size
        self.max_file_size = max_file_size
        self.date_format = utils.DEFAULT_DATE_FORMAT
        self.date_precise_format = "%Y-%m-%d %H:%M:%S"
        self.new_file_required = False
        self.suffix = 0
        self.logger = logger
        self.summary_path =  Path(self.base_path) / self.index_name / "primary" / "summary.json"
        self.read_write = read_write


###########################################################
## SECTTION STORE INDEX
##########################################################

    def _get_index_path(self):
        """Send the path of the current indexing files"""
        return Path(self.base_path) / self.index_name / "primary" / "indices" / f"index_{self.suffix}.json"

    def _get_file_size(self, file_path):
        """Return the size of the file or 0 if it doesn't exist."""
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def _split_and_store(self, data):
        """Store data in a new file if the other files have reached the maximum size."""
        try:
            index_dir = Path(self.base_path) / self.index_name / "primary" / "indices"
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            index_path = self._get_index_path()
            print("Index path:", index_path)
            # Find the first file not full with the highest suffix
            while os.path.exists(index_path) and self._get_file_size(index_path) >= self.max_index_size:
                self.suffix += 1
                index_path = self._get_index_path()
            # Update file summary for index, tenant and technology
            self.update_file_summary(data)
            # Check if the file has not reached the maximum size
            if os.path.exists(index_path) and self._get_file_size(index_path) < self.max_index_size:
                try:
                    print("File is not full")
                    # Wait for the file to be available before reading it
                    utils.wait_for_unlock(index_path)
                    # Lock the file before writing
                    utils.lock_file(index_path, True)
                    with open(index_path, 'r+') as f:
                        try:
                            existing_data = json.load(f)
                        except json.JSONDecodeError:
                            print(traceback.format_exc())
                            existing_data = {}
                        # Merge data
                        # TODO erase if not required
                        # existing_data = self.merge_dicts(existing_data, data)
                        existing_data = utils.merge_dicts(existing_data, data, "or", self.max_thread)

                        # Write to temp file first
                        with tempfile.NamedTemporaryFile('w', delete=False, dir=index_dir, prefix='tmp_', suffix='.json') as tmp_file:
                            json.dump(existing_data, tmp_file, indent=None)
                            tmp_name = tmp_file.name

                        # Replace original file with temp file atomically
                        shutil.move(tmp_name, index_path)
                        # # Truncate the file before writing
                        # f.seek(0)
                        # f.truncate()
                        # json.dump(existing_data, f, indent=None)
                    # Unlock the file after writing
                    utils.lock_file(index_path, False)
                    # Add the modification in the modification history
                    utils.add_file_modif_date(self.index_modification_file, index_path)
                finally:
                    utils.lock_file(index_path, False)
            else:
                try:
                    self.logger.log("debug", f"The file {index_path} is full, creating a new file...")
                    index_path = self._get_index_path()
                    # Lock the new file and write the data
                    utils.lock_file(index_path, True)
                    with open(index_path, 'w') as f:
                        json.dump(data, f, indent=None)
                    # Unlock the file after writing
                    utils.lock_file(index_path, False)
                    # Add the modification in the modification history
                    utils.add_file_modif_date(self.index_modification_file, index_path)
                finally:
                    utils.lock_file(index_path, False)
        except Exception:
            self.logger.log("error", f"Error during split and store {traceback.format_exc()}")

    def store_index(self, new_data):
        """Launch the index saving process."""
        if self.read_write:
            # TODO erase the index first
            pass
        self._split_and_store(new_data)


    def update_file_summary(self, data):
        """Update the file summary with the new data."""
        try:
            # Prepare summary for files details
            index_path = str(self._get_index_path())
            if os.path.exists(self.summary_path):
                with open(self.summary_path, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {
                    "index": [],
                    "tenant": [], 
                    "technology": [],
                    "details": {}
                }
            # Add details of the files
            if index_path not in existing_data["details"]:
                existing_data["details"][index_path] = {
                    "tenants": [],
                    "technologies": [],
                    "dates": []
                }
            # Index summary
            if self.index_name not in existing_data["index"]:
                existing_data["index"].append(self.index_name)
            # Tenant summary
            for tenant in data:
                if tenant not in existing_data["tenant"]:
                    existing_data["tenant"].append(tenant)
                if tenant not in existing_data["details"][index_path]["tenants"]:
                    existing_data["details"][index_path]["tenants"].append(tenant)                
                # Technology summary
                for date in data[tenant]:
                    if date not in existing_data["details"][index_path]["dates"]:
                        existing_data["details"][index_path]["dates"].append(date)
                    for technology in data[tenant][date]:
                        if technology not in existing_data["technology"]:
                            existing_data["technology"].append(technology)
                        if technology not in existing_data["details"][index_path]["technologies"]:
                            existing_data["details"][index_path]["technologies"].append(technology)
            utils.lock_file(self.summary_path, True)
            with open(self.summary_path, 'w') as f:
                json.dump(existing_data, f, indent=None)
            utils.lock_file(self.summary_path, False)
            utils.add_file_modif_date(self.index_modification_file, self.summary_path)
        except Exception:
            self.logger.log("error", f"Error during update_file_summary {traceback.format_exc()}")
            utils.lock_file(self.summary_path, False)



###########################################################
## SECTTION INDEX SEARCHING
##########################################################

    def date_in_range(self, date, start_time, end_time, format):
        # date = datetime.strptime(date, self.date_format)
        date = parser.parse(date) 
        if start_time is not None:
            start_time = datetime.strptime(start_time, format)
        if end_time is not None:
            end_time = datetime.strptime(end_time, format)
        if start_time is None and end_time is None:
            return True
        if start_time is None:
            return date <= end_time
        if end_time is None:
            return date >= start_time
        return start_time <= date <= end_time
    
    def search_in_text_value(self, index, value):
        pass
        #TODO

    def search_in_ipv4_value(self, index, value):
        pass
        #TODO

    def search_in_ipv6_value(self, index, value):
        pass
        #TODO
    
    def search_in_geolocation_value(self, index, value):
        pass
        #TODO

    def search_in_number_value(self, index, value):
        pass
        #TODO

    def search_in_date_value(self, index, value, operator=None, negative=False):
        # TODO change operator
        found_ids = []
        parsed_value = datetime.fromisoformat(value)
        try:
            if operator  == "=":
                for k, v in index.items():
                    if datetime.fromisoformat(k) == parsed_value and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            elif operator == ">=":
                for k, v in index.items():
                    if datetime.fromisoformat(k) >= parsed_value and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            elif operator == "<=":
                for k, v in index.items():
                    if datetime.fromisoformat(k) <= parsed_value and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            elif operator == ">":
                for k, v in index.items():
                    if datetime.fromisoformat(k) > parsed_value and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            elif operator == "<":
                for k, v in index.items():
                    if datetime.fromisoformat(k) < parsed_value and not negative:
                        found_ids.extend(v)   
                    elif negative:
                        found_ids.extend(v)
            elif operator == ":":
                for k, v in index.items():
                    if value == "*" and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
        except:
            self.logger.log("error", f"Error during search in date value: {traceback.format_exc()}")
        return found_ids
                
    
    def search_in_value(self, index, value, operator=None, negative=False):
        # TODO change operator
        found_ids = []
        try:
            if "\"" in value or "\'" in value:
                value = value.replace("\"", "").replace("\'", "")
            # search for field == value
            if value in index and not negative:
                found_ids.extend(index[value])
            elif negative or operator == "!:":
                # print("Search in value negative:" + str(value))
                for k, v in index.items():
                    if value != k:
                        found_ids.extend(v)
            # search for field contains value
            elif value[0] == "*" and value[-1] == "*":
                # print("contains value")
                value = value[1:-1]
                for k, v in index.items():
                    if value in k and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            # search for field endwith value
            elif value[0] == "*":
                # print("endwith value")
                value = value[1:]
                for k, v in index.items():
                    if k.endwith(value) and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            # search for field startwith value
            elif value[-1] == "*":
                # print("startwith value")
                value = value[:-1]
                for k, v in index.items():
                    if k.startswith(value) and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            # search for field insensitive value
            elif operator == "$:":
                # print("insensitive value")
                for k, v in index.items():
                    if value.lower() in k.lower() and not negative:
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
            # search for field regex value
            elif value[0] == "/" and value[-1] == "/":
                # print("regex value")
                value = value[1:-1]
                for k, v in index.items():
                    if len(re.findall(value, k)) > 0 and not negative:
                        # print(k)
                        found_ids.extend(v)
                    elif negative:
                        found_ids.extend(v)
        except:
            self.logger.log("error", f"Error during search in value: {traceback.format_exc()}")
        return found_ids
        
    def _divide_request(self, request):
        # TODO change this method to use design pattern
        # TODO find a way to avoid potential error with operator
        # superior or equal
        print("In divide request:" + str(request))
        if ">=" in request:
            # print("In superior or equal")
            res = request.split(">=", 1)
            op = ">="
        # Inferior or equal
        elif "<=" in request:
            # print("In inferior or equal")
            res = request.split("<=", 1)
            op = "<="
        # Strictly Superior
        elif ">" in request:
            # print("In strictly superior")
            res = request.split(">", 1)
            op = ">"
        # Strictly Inferior
        elif "<" in request:        
            # print("In strictly inferior")
            res = request.split("<", 1)
            op = "<"
        # Different
        elif "!:" in request :
            # print("In different")
            res = request.split("!:", 1)
            op = "!:"
        # Case insensitive
        elif "$:" in request:
            # print("In case insensitive")
            res = request.split("$:", 1)
            op = "$:"
        # Inside a range
        elif " in " in request:
            # print("In range")
            res = request.split(" in ", 1)
            op = "in"
        # As format
        # TODO see if it is useful
        # elif " asformat" in request:
        #     print("In asformat")
        #     match = re.search(r'\(([^)]+)\)', request)
        #     if match:
        #         res = match.group(1).split(",",1)
        #         # Return ["fiedname","format,value"]
        #     op = "asformat"
        # Strictly Equal
        elif ":" in request:
            # print("In strictly equal")
            res = request.split(":",1)
            op = ":"
            #If value is *:
            if res[1] == "*":
                op = "**"
        # Default Strictly Equal
        elif request == "*":
            op = "**"
            return None, request, "**"
        else:
            # print("None returned")
            return None, request, None
        return res[0], res[1], op


    def _search_in_index(self, file, request, tenant, start_time=None, end_time=None, technology=None, negative=False):
        try:
            print("Searching in index: ", file, " with request: ", request)
            # with open(file, 'r') as f:
            #     index = json.load(f)  
            with open(file, 'rb') as f:
                file_data = f.read()
            index = msgspec.json.decode(file_data, type=dict)
            # if field is defined, search for field == value
            field, value, operator = self._divide_request(request)
            print("OPERATOR: ", str(operator))
            field = field.strip() if field else None
            value = value.strip() if value else value
            # TODO change start_time and end_time to datetime per day. And keep searching in default timestamps the precise time
            start_time_hour = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime(self.date_format)
            end_time_hour = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").strftime(self.date_format)
            found_ids = {}
            # Browse index tree
            if tenant in index:
                for date, techno_dict in index[tenant].items():
                    # If date exists does not correspond to the period, ignore it
                    # print(str(date) + " " + str(start_time) + " " + str(end_time) + str(self.date_in_range(date, start_time_hour, end_time_hour)))
                    if not self.date_in_range(date, start_time_hour, end_time_hour, self.date_format):
                        continue
                    for tcn, fields_dict in techno_dict.items():
                        # If techno exists and not correspond to the parameter, ignore it
                        if technology and tcn != technology:
                            continue
                        for fld, values in fields_dict.items():
                            # If field is defined and does not correspond to the field, ignore it
                            if field and fld != field:
                                    continue
                            # Search in date
                            # print(index[tenant][date][tcn][fld]["type"], index[tenant][date][tcn][fld])
                            # If op == "**" send all values
                            if operator == "**" and not negative:
                                res = list(itertools.chain(*values.get("values").values()))
                            elif field and "type" in index[tenant][date][tcn][fld] and "timestamp" in index[tenant][date][tcn][fld]["type"]:
                                res = self.search_in_date_value(values.get("values"), value, operator, negative)
                            # Search in value text, keyword
                            else:
                                #res = self.search_in_value(index[tenant][date][tcn][fld]["values"], value, operator, negative)
                                res = self.search_in_value(values.get("values"), value, operator, negative)
                            if res:
                                # found_ids.extend((tenant, date, res))
                                found_ids = utils.merge_dicts_ids(found_ids, {tenant: {date: res}}, self.max_thread)
                            #TODO change it to search with the right type of field (date, ipv4, number...)
            # print(str(request) + ":" + str(found_ids))
            return found_ids
        except Exception:
            self.logger.log("error", f"Error during _search in index: {traceback.format_exc()}")
            return {}


    def select_files(self, tenant, start_time, end_time, technology):
        """ Return the list of files to search in """
        try:
            index_path = os.path.join(self.base_path, self.index_name, "primary", "summary.json")
            files = []
            with open(index_path, 'r') as f:
                data = json.load(f)
            for fil in data["details"].keys():
                if tenant in data["details"][fil]["tenants"]:
                    # files.append(fil)
                    # TODO test if this works
                    if (technology is not None and technology in data["details"][fil]["technologies"]) or technology is None:
                        # files.append(fil)
                        # TODO change start_time and end_time to datetime per day. And keep searching in default timestamps the precise time
                        start_time_hour = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime(self.date_format)
                        end_time_hour = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").strftime(self.date_format)
                        for date in data["details"][fil]["dates"]:
                            if self.date_in_range(date, start_time_hour, end_time_hour, self.date_format):
                                files.append(fil)
            return list(set(files))
        except Exception:
            self.logger.log("error", f"Error during select_files: {traceback.format_exc()}")
            # if file does not exist, return all files
            return [f for f in os.listdir(index_path) if f.endswith('.json')]
            

    def search_index(self, request, tenant, start_time=None, end_time=None, technology=None, negative=False):
        try:
            print("=======Search_index============")
            index_path = os.path.join(self.base_path, self.index_name, "primary", "indices")
            found_ids = {}
            # Get all JSON files concerned by the tenant, techno and period
            files = self.select_files(tenant, start_time, end_time, technology)
            # Filter only JSON files, ignoring .lock files or others
            # = [f for f in os.listdir(index_path) if f.endswith('.json')]
            print("Search index: path:" + str(files))
            if not files:
                return found_ids

            total_files = len(files)
            max_threads = min(self.max_thread, total_files)

            # Ensure chunk size is at least 1
            chunk_size = max(1, (total_files + max_threads - 1) // max_threads)
            file_chunks = [files[i:i + chunk_size] for i in range(0, total_files, chunk_size)]
            print("FILE CHUNKS: " + str(file_chunks))
        
            def worker(file_subset):
                """
                Worker function to process a subset of files.
                """
                local_found_ids = {}
                for file in file_subset:
                    partial_result = self._search_in_index(
                        os.path.join(index_path, file), request, tenant, start_time, end_time, technology, negative
                    )
                    local_found_ids = utils.merge_dicts_ids(local_found_ids, partial_result, self.max_thread)
                return local_found_ids

            def thread_worker(file_subset, results, lock):
                local_result = worker(file_subset)
                sample = str(local_result)[:100]
                print(f"Thread finished processing: {file_subset} -> {sample}")  # DEBUG
                if local_result != {}:
                    print("In local_result")
                    with lock:
                        print("in lock:")
                        results.append(local_result)
                print("res:" + str(results)[:80])

            # Execute threads and collect results
            threads = []
            results = []
            result_lock = threading.Lock()

            # for chunk in file_chunks:
            #     thread = threading.Thread(target=lambda res_list, chunk=chunk: res_list.append(worker(chunk)), args=(results,))
            #     threads.append(thread)
            #     thread.start()

            for chunk in file_chunks:
                print(f"Processing chunk: {chunk}")  # DEBUG
                thread = threading.Thread(target=thread_worker, args=(chunk, results, result_lock))
                threads.append(thread)
                thread.start()
            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            print("Final results:", str(results)[:100])  # DEBUG
            # Merge all results using the utility function
            for result in results:
                with result_lock:
                    found_ids = utils.merge_dicts_ids(found_ids, result, self.max_thread)
            print("found ids :" + str(found_ids)[:100])
            return found_ids
        except RuntimeError:
            self.logger.log("error", f"Runtime Error during search index: {traceback.format_exc()}")
            # Fallback to sequential search in case of a threading issue
            for file in files:
                result = self._search_in_index(os.path.join(index_path, file), request, tenant, start_time, end_time, technology, negative)
                found_ids = utils.merge_dicts_ids(found_ids, result, self.max_thread)
            return found_ids
        except Exception as e:
            self.logger.log("error", f"Unexpected error during search index: {traceback.format_exc()}")
            return found_ids
        finally:
            if 'e' in locals():
                self.logger.log("error", f"Error during search index: {traceback.format_exc()}")
                for thread in threads:
                    thread.join()


    def get_available_tenants(self):    
        """ Read the file containing the list of tenants and technologies """
        return self.read_summary_file("tenant")
        
    def get_available_technologies(self):
        """ Read the file containing the list of tenants and technologies """
        return self.read_summary_file("technology")

    def read_summary_file(self, type):
        """ Read the file containing the list of tenants """
        try:
            with open(self.summary_path, 'r') as f:
                data = json.loads(f.read())
            if type == "tenant":
                return data["tenant"]
            elif type == "technology":
                return data["technology"]
            else:
                return []
        except:
            self.logger.log("error", f"Error reading summary file: {traceback.format_exc()}")
            return []
        
    def list_files_lifecycle(self, days):
        try:
            files = []
            current_time = datetime.now()
            expiration_time = current_time - timedelta(days=days)
            with open(self.summary_path) as f:
                summary = json.load(f)
            summary = summary["details"]
            for file in summary:
                for date in summary[file]["dates"]:
                    if datetime.strptime(date, utils.DEFAULT_DATE_FORMAT) < expiration_time:
                        files.append(file)
            return files
        except Exception as e:
            self.logger.log("error", f"Error listing files: {traceback.format_exc()}")
            return []
        
    def delete_old_index(self, days):
        try:
            if days > 0:
                print("DELETE OLD INDEX VALUES")
                files = self.list_files_lifecycle(days)
                current_time = datetime.now()
                expiration_time = current_time - timedelta(days=days)

                for file in files:
                    try:
                        with open(file, 'r') as f:
                            data = json.load(f)
                    except Exception:
                        self.logger.log("error", f"Error reading file {file}: {traceback.format_exc()}")
                        continue

                    modified = False
                    for tenant, dates in data.items():
                        dates_to_delete = [
                            date for date in list(dates.keys())
                            if datetime.strptime(date, utils.DEFAULT_DATE_FORMAT) < expiration_time
                        ]
                        for date in dates_to_delete:
                            print("index before delete date: ", date)
                            # Check if the date is present in the dictionary
                            if date in data[tenant]:
                                print("index date to delete: ", date)
                                del data[tenant][date]
                            modified = True

                    if modified:
                        try:
                            utils.wait_for_unlock(file)
                            if not utils.lock_file(file, True):
                                time.sleep(0.1)
                                if not utils.lock_file(file, True):
                                    raise RuntimeError(f"Failed to lock the file {file}")

                            with open(file, 'w') as f:
                                json.dump(data, f)
                            utils.lock_file(file, False)
                        except Exception:
                            self.logger.log("error", f"Error writing updated data to file {file}: {traceback.format_exc()}")
                            utils.lock_file(file, False)

                        # Update the summary file (optional and context dependent)
                        try:
                            with open(self.summary_path, 'r') as f:
                                summary = json.load(f)

                            # Filter out deleted dates from summary (if structure allows)
                            for file in summary.get("details", {}):
                                    for date in dates_to_delete:
                                        print("INDEXING DELETING DATE: ", date, " in summary file")
                                        i = summary["details"][file]["dates"].index(date)
                                        summary["details"][file]["dates"].pop(i)

                            utils.wait_for_unlock(self.summary_path)
                            if not utils.lock_file(self.summary_path, True):
                                time.sleep(0.1)
                                if not utils.lock_file(self.summary_path, True):
                                    raise RuntimeError(f"Failed to lock the file {self.summary_path}")

                            with open(self.summary_path, 'w') as f:
                                json.dump(summary, f)
                            utils.lock_file(self.summary_path, False)

                        except Exception:
                            self.logger.log("error", f"Error updating summary file: {traceback.format_exc()}")
                            utils.lock_file(self.summary_path, False)
        except Exception:
            self.logger.log("error", f"Error deleting old data: {traceback.format_exc()}")

                
                







