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
document: lp categorzer interface
"""

from abc import ABC, abstractmethod
import traceback

class LPCategorizerInterface(ABC):

    @abstractmethod
    def categorize(self, data, logger):
        # Take in parameter a json of key value to add the categorisation in the logs
        pass

    def add_category(self, data, field_name, field_value, category_name, category_value, logger):
        """Take the field name and replace by value """
        try:
            if field_name in data["data"]["parsed"]:
                if field_value == data["data"]["parsed"].get(field_name):
                    data["data"]["parsed"][category_name] = category_value
        except:
            logger.log("error", f"Error in categorisation {traceback.format_exc()}")