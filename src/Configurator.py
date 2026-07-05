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
document: configurator
"""

import json
import os
import threading
import time
import traceback
from datetime import datetime
import copy

class Configurator:
    def __init__(self, config_file, configuration):
        self.config_file = config_file
        if configuration is None:
            self.config_data = self._load_config()
        else:
            self.config_data = configuration
            with open(self.config_file, 'w') as file:
                json.dump(self.config_data, file, indent=4)
        self.old_elements = {}
        self.elements = {}
        # self.config_data = self._load_config()
        self.interpret_config(self.config_data)
        self.run = False
        self.t = None
        self.old_config_data = {}
        
    # TODO change the _save_config for this new one
    def save_config(self, new_path):
        # TODO add backup from here
        with open(new_path, "w") as file:
            json.dump(self.config_data, file, indent=4)

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                return json.load(file)
        else:
            return {}

    def _save_config(self):
        with open(self.config_file, 'w') as file:
            json.dump(self.config_data, file, indent=4)

    def get_config(self, path_list=None, data=None):
        try:
            # If data is none, use the current config data
            if data is None or len(data) == 0:
                data = self.config_data
            # If config is empty, return all the configuration
            if path_list is None or len(path_list) == 0:
                return data
            # If config is str or int, return the value
            if isinstance(data, str) or isinstance(data, int):
                return data[path_list]
            # If config is list, search for the right key
            elif isinstance(data, type(list())):
                for key in range(len(data)):
                    if key == path_list[0]:
                        return self.get_config(path_list[1:], data[key])
            else:
                # If the config is a dict, search in the corresponding key
                return self.get_config(path_list[1:], data[path_list[0]])
        except:
            print(traceback.format_exc())
            return

    def set_value(self, path_list, value):
            try:
                if path_list is None or len(path_list) == 0:
                    self.config_data = value
                    return
                else:
                    data = self.config_data
                    for keys in path_list:
                        if isinstance(keys, dict):
                            return self.set_value(path_list[1:], data[keys])
                        elif isinstance(keys, list):
                            for key in keys:
                                if path_list[0] == key:
                                    return self.set_value(path_list[1:], data[key])
                        else:
                            self.config_data[keys] = value
                print(self.config_data)
            except (KeyError, IndexError, TypeError):
                print(f"Invalid path: {path_list}")

    def find_all_matching_ids(self, key_value_pairs):
        results = []
        self._recursive_find_matching(self.config_data, key_value_pairs, [], results, return_type='id')
        return results

    def find_all_matching_parents(self, key_value_pairs):
        results = []
        self._recursive_find_matching(self.config_data, key_value_pairs, [], results, return_type='parent')
        return results

    def _recursive_find_matching(self, data, key_value_pairs, path, results, return_type):
        if isinstance(data, dict):
            if all(k in data and data[k] == v for k, v in key_value_pairs.items()):
                if return_type == 'id' and 'id' in data:
                    results.append(data['id'])
                elif return_type == 'parent':
                    print(str(path))
                    results.append(path)
            for key, value in data.items():
                self._recursive_find_matching(value, key_value_pairs, path + [key], results, return_type)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                self._recursive_find_matching(item, key_value_pairs, path + [index], results, return_type)
    

    def start(self):
        if not self.run:
            self.run = True
            self.t = threading.Thread(target=self.monitor_config_file)
            self.t.start()
            return self.t

    def stop(self):
        print("Stopping threads...")
        if self.run:
            self.run = False
            if self.t:
                self.t.join()
                self.t = None
        print("Threads stopped.")

    def monitor_config_file(self):
        # Method to monitor the config file for changes and reload if necessary
        while self.run:
            new_config_data = self._load_config()
            if new_config_data != self.config_data:
                print("Configuration file has changed, reloading...")
                self.config_data = new_config_data
            time.sleep(5)

    def set_config(self,config):
        """ Verify the configuration and save it. """
        try:
            path_list = config["path_list"]
            config = config["configuration"]
            print("in set_config: " + str(config))
            if self.verify_config(config):
                self.old_config_data = copy.deepcopy(self.config_data)
                self.set_value(path_list, config)
                if "version" in self.config_data:
                    self.config_data["version"] += 1
                if "last_modified" in self.config_data:
                    self.config_data["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_config()
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return False

    def handle_get_configuration(self, request):
        """In case of web request with webrequester, return the configuration"""
        try:
            path = request["path"]
            data = request["configuration"]
            return self.get_config(path, data)
        except:
            print(traceback.format_exc())
            return None
    

    def interpret_config(self, config):
        """Interpret and store elements of the configuration and change references"""
        # configuration = copy.deepcopy(config)
        if len(self.elements) > 0:
            self.old_elements = self.elements
        self.elements = {}
        try:
            if "infrastructure" in config:
                # search for master coordinator
                if "mastercoordinators" in config["infrastructure"]:
                    for master in config["infrastructure"]["mastercoordinators"]:
                        self.elements[master["id"]] = master
                if "slavecoordinators" in config["infrastructure"]:
                    for slave in config["infrastructure"]["slavecoordinators"]:
                        self.elements[slave["id"]] = slave
                    for el in config["infrastructure"]["slavecoordinators"]:
                        if "sub-infrastructure" in el:
                            config = el
                            # self.elements = {}
                            for keys in el["sub-infrastructure"]:
                                for key in el["sub-infrastructure"][keys]:
                                    self.elements[key["id"]] = key
                elif "sub-infrastructure" in config["infrastructure"]:
                    config = config["infrastructure"]["sub-infrastructure"]
                    # self.elements = {}
                    for keys in config:
                        for key in config[keys]:
                            self.elements[key["id"]] = key
            print("ELEMENTS:" + str(self.elements))
        except:
            print(traceback.format_exc())
        

    def replace_references(self, configuration, elements):
        # TODO test this part.
        def explorer(dico):
            for cle, valeur in dico.items():
                # If value is a dictionary, explore recursively
                if isinstance(valeur, dict):
                    explorer(valeur)
                elif isinstance(valeur, list):
                    for i, item in enumerate(valeur):
                        if isinstance(item, dict):
                            explorer(item)
                # If value is string with &ref, replace with element value
                elif isinstance(valeur, str) and valeur.startswith('&'):
                    print("FOUND REFERENCE: " + valeur)
                    element_id = valeur[1:]  # Remove the '&' to obtain the element ID
                    if element_id in elements:
                        print("DICO:" + str(dico) + " cle:" + str(cle))
                        print(elements[element_id])
                        if "id" in elements[element_id]:
                            dico["id"] = elements[element_id]["id"]  # Replace the string with the element value
                        if "host" in elements[element_id]["webhook"]:
                            dico["host"] = elements[element_id]["webhook"]["host"]
                        if "port" in elements[element_id]["webhook"]:
                            dico["port"] = elements[element_id]["webhook"]["port"]
                        if "protocol" in elements[element_id]["webhook"]:
                            dico["protocol"] = elements[element_id]["webhook"]["protocol"]
                        # if "certs" in elements[element_id]["webhook"]:
                        #     dico["certs"] = elements[element_id]["webhook"]["certs"]
                        if "auth_token" in elements[element_id]["webhook"]:
                            dico["auth_token"] = elements[element_id]["webhook"]["auth_token"]
                        if "size" in elements[element_id]["webhook"]:
                            dico["size"] = elements[element_id]["webhook"]["size"]
                        if "primary" in elements[element_id]:
                            dico["primary"] = elements[element_id]["primary"]
                        if "group" in elements[element_id]:
                            dico["group"] = elements[element_id]["group"]
                        # TODO add more references
                    break
        explorer(configuration)

    def compare_dicts(self, old_data, new_data, parent_keys=[]):
        """
        Recursively compares two structures (which can be dicts, lists, or scalar values) and returns
        the keys or indices that have been modified.
        
        :param old_data: The old structure (can be a dict, list, int, str, etc.).
        :param new_data: The new structure (can be a dict, list, int, str, etc.).
        :param parent_keys: A list of keys or indices to track the path to the modified values.
        :return: A list of modified keys or paths (as tuples of keys/indices).
        """
        modified_keys = []
        # Case where both old_data and new_data are dictionaries
        if isinstance(old_data, dict) and isinstance(new_data, dict):
            # Gather all unique keys from both dictionaries
            all_keys = set(old_data.keys()).union(new_data.keys())
            for key in all_keys:
                old_value = old_data.get(key, None)
                new_value = new_data.get(key, None)
                # Recursively compare if both values are dicts, lists, or simple values
                if old_value != new_value:
                    modified_keys.extend(self.compare_dicts(old_value, new_value, parent_keys + [key]))
        # Case where both old_data and new_data are lists
        elif isinstance(old_data, list) and isinstance(new_data, list):
            # If the length of the lists differs, the entire list is considered modified
            if len(old_data) != len(new_data):
                modified_keys.append(tuple(parent_keys))
            else:
                # Compare lists element by element
                for i, (old_item, new_item) in enumerate(zip(old_data, new_data)):
                    if old_item != new_item:
                        modified_keys.extend(self.compare_dicts(old_item, new_item, parent_keys + [i]))
        # Case where old_data and new_data are of simple types (int, str, etc.)
        else:
            # If values are different, register the path as modified
            if old_data != new_data:
                modified_keys.append(tuple(parent_keys))
        return modified_keys


    def _compare_elements(self, old_ids, new_ids, old_config_data, config_data):
        """Compare sub configuration"""
        removed_elements = []
        added_elements = []
        modified_elements = []

        # Éléments deleted
        removed_ids = old_ids - new_ids
        for element_id in removed_ids:
            removed_elements.append(element_id)

        # Éléments added
        added_ids = new_ids - old_ids
        for element_id in added_ids:
            added_elements.append(element_id)

        # Éléments modified
        modified_ids = new_ids - removed_ids - added_ids

        print("modified_ids: " + str(modified_ids))
        print("old_ids: " + str(old_ids))
        print("new_ids: " + str(new_ids))
        print("removed_ids: " + str(removed_ids))
        print("added_ids: " + str(added_ids))
        # common_ids = old_ids.intersection(modified_ids)
        for element_id in modified_ids:
            old_element = old_config_data[element_id]
            new_element = config_data[element_id]
            modified_keys = self.compare_dicts(old_element, new_element)
            if modified_keys:
                modified_elements.append((element_id, modified_keys))
        return removed_elements, added_elements, modified_elements

    def compare_elements(self):
        """
        Compare `self.old_config_data` and `self.config_data` and trigger actions 
        in case of adding, deletion or modification of an element
        """
        removed = []
        added = []
        modified = []
        # Compare infrastructure
        old_ids = set(self.old_elements)
        new_ids = set(self.elements)
        removed, added, modified = self._compare_elements(old_ids, new_ids, self.old_elements, self.elements)
        return removed, added, modified


    def verify_config(self, config):
        # Check for the required structure and necessary keys in the configuration
        print("in verify_config")
        # TODO verify the config
        return True