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
document: logger
"""

import json, traceback, time, random, base64
from datetime import datetime, timedelta, timezone
from QueueManager import QueueManager
import logging
from logging import Handler
from datetime import datetime
from shutil import move
import os


class Logger:
    def __init__(self, id_technology, log_level, log_path, max_queue_size=8192, max_file=50, max_file_size=1073741824, print_enabled=True, queue_enabled=True, file_enabled=True):
        """
        Initialise the logger
        """
        self.technology = id_technology
        self.log_level = log_level
        self.log_path = log_path
        self.max_queue_size = max_queue_size
        self.max_file = max_file
        self.max_file_size = max_file_size
        # Print
        self.print_enabled = print_enabled
        # Init queue
        self.queue_monitoring_enabled = queue_enabled
        self.queue_monitoring = QueueManager(self.max_queue_size, self.log_path, self.max_file, self.max_file_size)
        # Init the file logger
        self.logger_file_enabled = file_enabled
        self.logger_file = self.setup_file_json_logger("logger_" + str(self.technology), self.log_path, max_file_size, max_file)
        # Print log enabled
        print("print:", str(self.print_enabled))
        print("queue:", str(self.queue_monitoring_enabled))
        print("file:", str(self.logger_file_enabled))

    def _log_level_priority(self, log_level):
        if log_level == "debug":
            return 0
        elif log_level == "info":
            return 1
        elif log_level == "warning":
            return 2
        elif log_level == "error":
            return 3
        elif log_level == "critical":
            return 4
        else:
            return 5
        
    def _log_level_priority_file(self, log_level):
        if log_level == "debug":
            return logging.DEBUG
        elif log_level == "info":
            return logging.INFO
        elif log_level == "warning":
            return logging.WARNING
        elif log_level == "error":
            return logging.ERROR
        elif log_level == "critical":
            return logging.CRITICAL
        else:
            return logging.DEBUG

    # --- Setup logger ---
    def setup_file_json_logger(self, name, log_file, max_bytes, max_files):
        logger_file = logging.getLogger(name)
        logger_file.setLevel(self._log_level_priority_file(self.log_level))
        logger_file.propagate = False
        if not any(isinstance(h, SizeRotatingJsonFileHandler) for h in logger_file.handlers):
            handler = SizeRotatingJsonFileHandler(log_file, max_bytes=max_bytes, max_files=max_files)
            logger_file.addHandler(handler)
        return logger_file

    def log_write(self, logger, level: str, message: str):
        level = level.lower()
        if hasattr(logger, level):
            log_func = getattr(logger, level)
            log_func(message)
        else:
            logger.error(f"Invalid level of log: {level} | Message: {message}")

    def log(self, log_level, message, tenant="siem_monitoring"):
        try:
            if self._log_level_priority(self.log_level) <= self._log_level_priority(log_level) and message is not None:
                if type(message) is not dict:
                    message = {"message": str(message)}
                # Create log
                # TODO add a parameter to enable or disable output on console
                # TODO duplicata of function for define the id
                log = {"data":{"parsed":{
                    "id": (str(time.time()) + str(random.random())).replace(".",""),
                    "tenant": tenant,
                    "technology": self.technology,
                    "siem_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "log_level": log_level
                },"raw": base64.b64encode(json.dumps(message).encode('utf-8')).decode('utf-8')}}
                log["data"]["parsed"].update(message)
                # Print log to console
                if self.print_enabled:
                    print(str(log["data"]["parsed"]))
                # Add values in files
                if self.logger_file_enabled:
                    # TODO check if better to use only message or the json parsed
                    self.log_write(self.logger_file, log_level, log["data"]["parsed"])
                # Add values in the queue
                if self.queue_monitoring_enabled:
                    self.queue_monitoring.enqueue(json.dumps(log).encode("utf-8"))
        except Exception:
            print("Error: " + traceback.format_exc())
            raise Exception("Error: " + traceback.format_exc())

    def retrieve_monitoring(self, data):
        try:
            # Use bytearray to improve performances during concatenation
            elements = bytearray(b"[")  # Init with bytearray containing "[" 
            size = int(data["size"])  # Convert to int
            elements_count = 0
            
            # Pop element from the queue
            for _ in range(size):
                dequeued_element = self.queue_monitoring.dequeue(1)
                if not dequeued_element:
                    break
                # Add comma if not first element
                if elements_count > 0:
                    elements.extend(b",")  # Use extend to avoid creation of new instances
                # Add current element extracted
                elements.extend(dequeued_element)
                elements_count += 1

            # Close array if elements were added             
            if elements_count > 0:
                elements.extend(b"]")  # Add array closure "]"
                return bytes(elements)  # Return in bytes
            else:
                return None
        except Exception as e:
            print("Error while retrieving monitoring logs: " + traceback.format_exc())
            # TODO: Enqueue data in queue in case of error (if required)
            return None


class SizeRotatingJsonFileHandler(Handler):
    def __init__(self, base_filename, max_bytes=1024 * 1024, max_files=5):
        super().__init__()
        self.base_filename = base_filename
        self.max_bytes = max_bytes
        self.max_files = max_files
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        log_dir = os.path.dirname(self.base_filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def emit(self, record):
        log_entry = self.format(record)
        log_entry_bytes = (log_entry + '\n').encode('utf-8')
        self.rotate_if_needed(len(log_entry_bytes))
        with open(self.base_filename, 'ab') as f:
            f.write(log_entry_bytes)

    def rotate_if_needed(self, incoming_size):
        if os.path.exists(self.base_filename):
            if os.path.getsize(self.base_filename) + incoming_size < self.max_bytes:
                return

        # Delete the oldest file if necessary
        oldest = f"{self.base_filename}.{self.max_files - 1}"
        if os.path.exists(oldest):
            os.remove(oldest)

        # Shift rotated files
        for i in range(self.max_files - 2, 0, -1):
            src = f"{self.base_filename}.{i}"
            dst = f"{self.base_filename}.{i + 1}"
            if os.path.exists(src):
                move(src, dst)

        # Move current log to .1
        if os.path.exists(self.base_filename):
            move(self.base_filename, f"{self.base_filename}.1")

