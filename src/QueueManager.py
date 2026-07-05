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
document: queue manager
"""

import queue
import threading
import os
import time
from glob import glob
from collections import defaultdict
import traceback

class QueueManager:
    def __init__(self, max_queue_size, backup_file, backup_max_file=50, backup_max_size=8096, delimiter=b"\n"):
        self.max_queue_size = max_queue_size
        # TODO split the folder from the file, error during creation of the file when /data/<subfolder>/file
        self.backup_file = backup_file
        self.backup_max_file = backup_max_file
        self.backup_file_max_size = backup_max_size
        self.data_queue = queue.Queue(maxsize=max_queue_size)
        self.queue_lock = threading.Lock()
        self.file_locks = defaultdict(threading.Lock)
        self.stop_thread = threading.Event()
        self.delimiter = delimiter
        # Statistics
        self.avg_enqueue = 0
        self.avg_dequeue = 0
        self.avg_time_enqueue = 0
        self.avg_time_dequeue = 0
        self.avg_nb_save = 0
        self.avg_nb_restore = 0
        self.avg_time_save_file = 0
        self.avg_time_restore_file = 0

        # Start the thread to restore data from file to queue
        self.restore_thread = threading.Thread(target=self._restore_from_file_thread)
        self.restore_thread.daemon = True
        self.restore_thread.start()

    def get_stats(self):
        stats_log = {
            "current_queue_size": self.data_queue.qsize(),
            "avg_enqueue": self.avg_enqueue,
            "avg_dequeue": self.avg_dequeue,
            "avg_time_enqueue": self.avg_time_enqueue,
            "avg_time_dequeue": self.avg_time_dequeue,
            "avg_nb_saved": self.avg_nb_save,
            "avg_nb_restore": self.avg_nb_restore,
            "avg_time_save_time": self.avg_time_save_file,
            "avg_time_restore_time": self.avg_time_restore_file
        }
        return stats_log

    def _get_current_backup_file(self):
        backup_files = sorted(glob(f"{self.backup_file}.*"), key=os.path.getmtime)
        if not backup_files:
            return f"{self.backup_file}.{int(time.time())}"
        latest_file = backup_files[-1]
        if os.path.getsize(latest_file) >= self.backup_file_max_size:
            if len(backup_files) >= self.backup_max_file:
                # TODO genere error messages to log for the queue manager too
                print("Maximum number of backup files reached, data is ignored.")
                return None
            return f"{self.backup_file}.{int(time.time())}"
        return latest_file

    def save_to_file(self, data):
        current_file = self._get_current_backup_file()
        if current_file is None:
            print("Maximum number of backup files reached, data is ignored.")
            return
        with self.file_locks[current_file]:
            with open(current_file, 'ab') as f:
                self.avg_nb_save += len(data) / 2
                f.write(data + self.delimiter)


    def _restore_from_file_thread(self):
        while not self.stop_thread.is_set():
            start_time = time.time()
            self.restore_from_file()
            self.avg_time_restore_file += (time.time() - start_time) / 2
            # Measure wait time
            wait_start = time.time()
            self.stop_thread.wait(1)
            wait_time = time.time() - wait_start
            # print(f"self.stop_thread.wait took {wait_time:.2f} seconds")

    def restore_from_file(self):
        try:
            if not self.data_queue.full():
                backup_files = sorted(glob(f"{self.backup_file}.*"), key=os.path.getmtime)
                for file_name in backup_files:
                    with self.file_locks[file_name]:
                        with open(file_name, 'rb') as f:
                            # lines = f.readlines()
                            lines = f.read()
                            lines = lines.split(self.delimiter)
                        remaining_lines = []
                        for line in lines:
                            # TODO check if line.strip() is required
                            if not self.enqueue(line, False):
                                remaining_lines.append(line + b'')
                            else:
                                self.avg_nb_restore += len(line) / 2
                        if remaining_lines:
                            with open(file_name, 'wb') as f:
                                for l in remaining_lines:
                                    if l != self.delimiter:
                                        # f.write(l + b'')
                                        # TODO change this in case of problem
                                        f.write(l + self.delimiter)
                            return
                        else:
                            os.remove(file_name)
                            print(f"{file_name} has been removed.")
        except:
            print("Error in restore_from_file")
            print(traceback.format_exc())

    def enqueue(self, data, force=True):
        try:
            start_time = time.time()
            # TODO change this in case of problem
            self.data_queue.put_nowait(data + self.delimiter)
            self.avg_time_enqueue += (time.time() - start_time) / 2
            self.avg_enqueue += len(data) / 2
            return True
        except queue.Full:
            if force:
                start_time = time.time()
                self.save_to_file(data)
                self.avg_time_save_file += (time.time() - start_time) / 2
                self.avg_nb_save += len(data) / 2
            return False

    def dequeue(self, count):
        try:
            start_time = time.time()
            elements = bytearray()
            for _ in range(count):
                try:
                    elements.extend(self.data_queue.get_nowait())
                except queue.Empty:
                    break
            self.avg_time_dequeue += (time.time() - start_time) / 2
            # TODO check if this is correct -> len(elements) ??
            self.avg_dequeue += len(elements) / 2
            return bytes(elements)
        except queue.Empty:
            return {}
        except:
            print("Error in dequeue")
            print(traceback.format_exc())
    
    def isFull(self):
        return self.data_queue.full() and (len(self.backup_file) >= self.backup_max_file)

    def isEmpty(self):
        return self.data_queue.empty() and (len(self.backup_file)) == 0

    def wait_for_empty_queue(self):
        while not self.isEmpty():
            time.sleep(0.5)

    def get_size(self):
        return self.data_queue.qsize()

    def stop(self):
        self.stop_thread.set()
        self.restore_thread.join()

    def set_config(self, max_queue_size, backup_file, backup_max_file, backup_max_size):
        self.max_queue_size = max_queue_size
        self.backup_file = backup_file
        self.backup_max_file = backup_max_file
        self.backup_file_max_size = backup_max_size
