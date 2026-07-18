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
document: resources monitor
"""

import json
import psutil
import os
import docker
import time
import threading
import traceback

class ResourceMonitor:
    def __init__(self, id_container, logger):
        self.disk_usage = psutil.disk_usage('/')
        self.cpu_count = os.cpu_count()
        self.virtual_memory = psutil.virtual_memory()
        # Container information
        self.container = docker.from_env()
        self.id = id_container
        self.cpu_avg = 0.0
        self.mem_avg = 0.0
        self.disk_read_avg = 0.0
        self.disk_write_avg = 0.0
        self.network_rx_avg = 0.0
        self.network_tx_avg = 0.0
        self.sample_count = 0
        self.running = True
        # logger
        self.logger = logger
        # frequency
        self.frequency = 30
        # Thread for the monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_container)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()


    def get_total_disk(self):
        return self.disk_usage.total

    def get_free_disk(self):
        return self.disk_usage.free

    def get_cpu_count(self):
        return self.cpu_count

    def get_total_memory(self):
        return self.virtual_memory.total

    def get_available_memory(self):
        return self.virtual_memory.available

    def get_system_info(self):
        system_info = {
            "total_disk": self.get_total_disk(),
            "free_disk": self.get_free_disk(),
            "cpu_count": self.get_cpu_count(),
            "total_memory": self.get_total_memory(),
            "available_memory": self.get_available_memory()
        }
        return system_info
    
    def monitor_container(self):
        try:
            container = self.container.containers.get(self.id)
            while self.running:
                try:
                    stats = container.stats(stream=False)

                    # CPU Usage
                    cpu_stats = stats.get('cpu_stats', {})
                    cpu_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
                    cpu_system = cpu_stats.get('system_cpu_usage', 1)  # Avoid division by zero
                    cpu_percent = (cpu_usage / cpu_system) * 100 if cpu_system > 0 else 0

                    # Memory Usage
                    memory_stats = stats.get('memory_stats', {})
                    mem_usage = memory_stats.get('usage', 0)
                    mem_limit = memory_stats.get('limit', 1)  # Avoid division by zero
                    mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0

                    # Disk I/O
                    blkio_stats = stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [])
                    disk_read = sum(x.get('value', 0) for x in blkio_stats if x.get('op') == 'Read')
                    disk_write = sum(x.get('value', 0) for x in blkio_stats if x.get('op') == 'Write')

                    # Network
                    network_stats = stats.get('networks', {})
                    rx_bytes = sum(net.get('rx_bytes', 0) for net in network_stats.values())
                    tx_bytes = sum(net.get('tx_bytes', 0) for net in network_stats.values())

                    # Update averages
                    self.cpu_avg += cpu_percent
                    self.mem_avg += mem_percent
                    self.disk_read_avg += disk_read
                    self.disk_write_avg += disk_write
                    self.network_rx_avg += rx_bytes
                    self.network_tx_avg += tx_bytes
                    self.sample_count += 1

                    time.sleep(self.frequency)

                except Exception as inner_exception:
                    self.logger.log("error", f"Error while processing container stats: {traceback.format_exc()}")
                    time.sleep(self.frequency)

        except docker.errors.NotFound:
            self.logger.log("error", f"The container with ID '{self.id}' has not been found.")
        except Exception as e:
            self.logger.log("error", f"An unexpected error occurred: {str(e)}\n{traceback.format_exc()}")


    def get_container_info(self):
        if self.sample_count == 0:
            return {"log_level":"debug", "msg":"No data collected yet."}
        # Computes means
        cpu_avg = self.cpu_avg / self.sample_count
        mem_avg = self.mem_avg / self.sample_count
        disk_read_avg = self.disk_read_avg / self.sample_count
        disk_write_avg = self.disk_write_avg / self.sample_count
        network_rx_avg = self.network_rx_avg / self.sample_count
        network_tx_avg = self.network_tx_avg / self.sample_count
        # Prepare data in JSON
        metrics = {
            "name": "resources_monitoring",
            "resource": self.id,
            "cpu_percent_avg": cpu_avg,
            "memory_percent_avg": mem_avg,
            "disk_read_avg_MB": disk_read_avg / (1024 * 1024),
            "disk_write_avg_MB": disk_write_avg / (1024 * 1024),
            "network_rx_avg_MB": network_rx_avg / (1024 * 1024),
            "network_tx_avg_MB": network_tx_avg / (1024 * 1024)
        }
        # Reinit averages
        self.cpu_avg = 0.0
        self.mem_avg = 0.0
        self.disk_read_avg = 0.0
        self.disk_write_avg = 0.0
        self.network_rx_avg = 0.0
        self.network_tx_avg = 0.0
        self.sample_count = 0
        return metrics

    def stop(self):
        self.running = False
        self.monitor_thread.join()


    def print_system_info(self):
        info = self.get_system_info()
        print(json.dumps(info, indent=4))
