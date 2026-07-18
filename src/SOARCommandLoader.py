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
document: soar command
"""

import types
from datetime import datetime
import sys
import os
import importlib.util
from types import FunctionType
import inspect
import json
import traceback
from TaskManager import TaskManager
from contextlib import contextmanager
from contextvars import ContextVar
import copy
import re
import Utils as utils
import UtilsIndexing as utindex
import asyncio
import time

class CommandLoader:
    _context_var = ContextVar("context", default={})

    def __init__(self, builtin_folder_path, customer_folder_path, vault, logger, queue, authenticator=None, indexsearchmotor=None, creds=None, index=None, tenant=None, technology=None):
        self.builtin_folder_path = builtin_folder_path
        self.custom_folder_path = customer_folder_path
        self.commands = {}
        self.vault = vault
        self.logger = logger
        self.queue = queue
        self.authenticator = authenticator
        self.indexsearchmotor = indexsearchmotor
        # TODO add index, tenant and technologies in the task scheduler
        self.task_scheduler = TaskManager(self.commands, self.logger, self.queue, creds, index, tenant, technology)
        self.reload()
        # TODO Wait for the system to be online (dedicated index search motor not implemented...)
        # TODO load the task and schedule it
        for i in range(5):
            if self.task_scheduler.init_scheduled_task():
                self.logger.log("info", "Init scheduled task succeeded")
                break
            time.sleep(i)
            

    def reload(self):
        self.commands.clear()
        self.task_scheduler.commands = self.commands
        self.load_folder()

    def load_folder(self):
        # Load the builtin commands
        for filename in os.listdir(self.builtin_folder_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                file_path = os.path.join(self.builtin_folder_path, filename)
                self._load_file(file_path)
        # Load the customer commands
        if os.path.isdir(self.custom_folder_path):
            for filename in os.listdir(self.custom_folder_path):
                if filename.endswith(".py") and not filename.startswith("__"):
                    file_path = os.path.join(self.custom_folder_path, filename)
                    self._load_file(file_path)

    def _load_file(self, path):
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            self.logger.log("error", f"Error during module loading '{module_name}': {traceback.format_exc()}")
            return

        for name, obj in vars(module).items():
            if isinstance(obj, FunctionType):
                try:
                    func_file = os.path.abspath(obj.__code__.co_filename)
                    if func_file == os.path.abspath(path):
                        # bound_method = types.MethodType(obj, self)
                        bound_method = types.MethodType(obj, self)
                        self.commands[name] = {
                            "name": name,
                            "function": bound_method,
                            "params": self._extract_params(obj),
                            "description": obj.__doc__ or ""
                        }
                except Exception as e:
                    self.logger.log("error", f"Failed to load function '{name}': {e}")

    def _extract_params(self, func):
        """
        Format of parameters:
        - param: type => description
        """
        params = []

        # Analyse docstring 
        doc = func.__doc__ or ""
        param_descriptions = {}

        # Research of section "params:" in the docstring
        match = re.search(r"params:\s*(.*)", doc, re.DOTALL | re.IGNORECASE)
        if match:
            lines = match.group(1).splitlines()
            for line in lines:
                line = line.strip()
                if not line.startswith("-"):
                    continue
                # Ex: - param: type => description
                m = re.match(r"-\s*(\w+)\s*:\s*([\w\[\], ]+)\s*=>\s*(.+)", line)
                if m:
                    name, typ, desc = m.groups()
                    param_descriptions[name] = {
                        "type": typ.strip(),
                        "description": desc.strip()
                    }

        for name, param in inspect.signature(func).parameters.items():
            if name == "self":
                continue

            # Type priority from annotation, else from docstring, else "str"
            if param.annotation != inspect.Parameter.empty:
                if isinstance(param.annotation, str):
                    param_type = param.annotation
                elif hasattr(param.annotation, "__name__"):
                    param_type = param.annotation.__name__
                else:
                    param_type = str(param.annotation)
            elif name in param_descriptions:
                param_type = param_descriptions[name]["type"]
            else:
                param_type = "str"

            param_info = {
                "name": name,
                "type": param_type,
                "description": param_descriptions.get(name, {}).get("description", "")
            }

            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default

            params.append(param_info)

        return params



    def execute_from_json(self, json_str):
        data = json.loads(json_str)
        name = data["name"]
        params_list = data.get("params", [])
        
        if name not in self.commands:
            raise ValueError(f"Fonction '{name}' introuvable.")
        
        func_info = self.commands[name]
        func = func_info["function"]
        param_defs = func_info.get("params", [])

        for param_dict in params_list:
            full_args = {}
            for p in param_defs:
                pname = p["name"]
                if pname in param_dict:
                    full_args[pname] = param_dict[pname]
                elif "default" in p:
                    full_args[pname] = p["default"]
                else:
                    raise ValueError(f"Missing required parameter: {pname}")
            
            func(**full_args)

    @property
    def context(self):
        return self._context_var.get()
    
    @contextmanager
    def _temporary_context(self):
        # Create a new context isolated for this call
        token = self._context_var.set(copy.deepcopy(self.context))
        try:
            yield self
        finally:
            self._context_var.reset(token)  # Restore old context


    def parse_named_arguments(self, parts):
        args = {}
        for part in parts:
            if '=' not in part:
                raise ValueError(f"Invalid argument format: '{part}' (expected key=value)")
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            # Clean quotes (simples of double)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            args[key] = value
        return args

    def execute_commands_soar(self, data, new=False):
        """Handle SOAR command(s) with named parameters and type conversion"""
        try:
            with self._temporary_context():
                print(str(data))
                session_token = data["session_token"]
                raw_query = data["command"]
                command_id = data.get("id", None)
                index = data.get("index", None)
                tenant = data.get("tenant", None)
                #TODO check permissions of the user to use the vault credentials
                instance = data.get("vault", None)
                history_name = data.get("history", None)
                display = data.get("display", True)
                # If playbook_mode == True, don't execute commands
                playbook_mode = data.get("playbook_mode", False) 
                # id = len(self.history) if command_id is None else command_id
                author = json.loads(session_token).get("username", "Unknown")
                print("command_id:", str(command_id))
                commands = raw_query.split(";")
                print("commands:", str(commands))
                results = []
                print("handle_soar_command self id:", id(self))
                for cmd_str in commands:
                    cmd_str = cmd_str.strip()
                    if not cmd_str:
                        continue
                    try:
                        # Extraire le nom de commande (le premier mot sans égal)
                        # Extract command name (first word without =)
                        match = re.match(r'^(\S+)', cmd_str)
                        if match:
                            command_name = match.group(1)
                            rest = cmd_str[match.end():].strip()
                        else:
                            raise ValueError("No command name found.")
                        # Regex to compute piars key=value or key={...}
                        pattern = r'''
                            \w+=".*?"       # key="value with space"
                            |               # ou
                            \w+=\{.*?\}     # key={...}
                            |               # ou
                            \w+=\S+         # key=value simple
                        '''
                        param_parts = re.findall(pattern, rest, re.VERBOSE)
                        if command_name not in self.commands:
                            raise ValueError(f"Unknown command '{command_name}'")
                        cmd_info = self.commands[command_name]
                        func = cmd_info["function"]
                        # Get waited type and default value from signature
                        sig = inspect.signature(func)
                        expected_params = {}
                        default_values = {}
                        for name, param in sig.parameters.items():
                            if name == "self":
                                continue
                            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                            expected_params[name] = param_type
                            if param.default != inspect.Parameter.empty:
                                default_values[name] = param.default
                        # Analyse arguments named
                        raw_params = self.parse_named_arguments(param_parts)
                        # Preparation of parameters fusioned with default values
                        merged_params = {}
                        for key in expected_params:
                            if key in raw_params:
                                merged_params[key] = raw_params[key]
                            elif key in default_values:
                                merged_params[key] = default_values[key]
                            else:
                                raise ValueError(f"Missing parameter: {key}")

                        # Type conversion 
                        typed_params = {
                            key: utils.convert_param_type(merged_params[key], expected_params[key])
                            for key in expected_params
                        }
                        for key in typed_params:
                            print(f"key: {key}, value: {typed_params[key]}, type: {type(typed_params[key])}")                  
                        # Play the command
                        if not playbook_mode:
                            print("handle_soar_command self id:", id(self))
                            print("Play the command not in playbook mode")
                            # result = func(**typed_params)
                            # self.commands["soar_play_context"]["function"](history_name, instance, index, tenant, command_id, display)
                            self.commands["soar_set_context"]["function"](history_name, index, tenant, command_name, typed_params, author, instance, command_id, False, display, session_token)
                            print("handle_soar_command self id:", id(self))
                        else:
                            print("Play the command in playbook mode")
                            self.commands["soar_set_context"]["function"](history_name, index, tenant, command_name, typed_params, author, instance, command_id, True, display, session_token)
                    except Exception as e:
                        self.logger.log("error", f"Error executing command '{cmd_str}': {traceback.format_exc()}")
                        param = cmd_str.split()[1:] if len(cmd_str.split()) > 0 else "",
                        res = utindex.create_soar_history_entry(command_id, author, command_name, param, f"Command failed: {str(e)}", "failed", self.context["history"])
                        if display:
                            self.context["history"][command_id].append(res)
                print("handle_soar_command self id:", id(self))
                print("results:", str(results))
                # print("history:", str(self.context["history"]))   
                print("queue: ", str(self.queue.get_size()))
                return copy.deepcopy(self.context)
            # If no command found, just play the id
            # TODO this function will not work
            return self.commands["soar_play_context"]["function"](history_name, instance, index, tenant, command_id, display, session_token)
        except Exception:
            self.logger.log("error", f"Failed to handle SOAR command: {traceback.format_exc()}")
            # TODO add current id in case of error of playbook
            res = utindex.create_soar_history_entry(command_id, author, str(data), str(data), f"Command handling failed", "failed", self.context["history"])
            return res    
        