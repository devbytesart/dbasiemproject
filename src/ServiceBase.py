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
document: service base
"""

from abc import ABC, abstractmethod

class ServiceBase(ABC):
    @abstractmethod
    def load_configuration(self):
        """Load the configuration of the service"""
        pass

    @abstractmethod
    def _load_stats(self):
        """Load the statistics of the service"""
        pass

    @abstractmethod
    def handle_set_config(self, data):
        """Handle the set configuration request"""
        pass

    @abstractmethod
    def handle_shutdown(self, data):
        """Handle the shutdown request"""
        pass

    @abstractmethod
    def handle_retrieve_monitoring(self, data):
        """Handle the retrieve monitoring request"""
        pass

    @abstractmethod
    def _stop_microservices(self):
        """Stop the microservices"""
        pass

    @abstractmethod
    def _start_microservices(self):
        """Start the microservices"""
        pass

    @abstractmethod
    def _restart_microservices(self):
        """Restart the microservices"""
        pass