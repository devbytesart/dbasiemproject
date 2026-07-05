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
document: operation base
"""

import re
import UtilsEnum as ue
from abc import ABC, abstractmethod

# Class abstract base for operation
class OperationBase(ABC):
    def identify_operation(self, operation: str) -> bool:
        """Verify if operation is correspond to this class"""
        pass

    @abstractmethod
    def parse_operation(self, operation: str):
        """Analyse and find parameters for the function evaluate operation"""
        pass

    @abstractmethod
    def evaluate_operation(self, *args):
        """Evaluate with the parameters the results of the operation and return it"""
        pass

    @abstractmethod
    def execute_operation(self, operation: str, data: list, index: list, tenant: list, start_time: str, end_time: str, technology: list, token : str):
        """Execute the operation and return the result"""
        pass

    @abstractmethod
    def all_pages(self):
        """Return True if all data are required, False otherwise"""
        pass

    @abstractmethod
    def get_suggestions(self):
        """Return the suggestions for the operation ["suggestion1", "suggestion2", ...]"""
        pass

    @abstractmethod
    def get_required_permissions(self):
        """Return the required permissions for the operation"""
        pass

    @abstractmethod
    def get_help(self):
        """Return the help for the operation"""
        pass