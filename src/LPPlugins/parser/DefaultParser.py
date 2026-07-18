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
project: siem project
DOCUMENT: default parser

"""

from LPParserInterface import LPParserInterface
import re, traceback, json

class DefaultParser(LPParserInterface):
    """ Put the value in unparsed without any treatment """
    
    def verify(self, data, logger):
        return True

    def parse(self, data, logger):
        # Escape problematic characters
        # Clean the data by removing tabs, newlines, and carriage returns
        data = data.replace("\t", "").replace("\n","").replace("\r","").replace("\\", "").replace("\"", "").replace("\'", "").strip()
        logger.log("debug", "Data to parse: " + str(data))
        parsed_data = {"log_type": "default"}
        try:
            parsed_data["unparsed"] = str(data)
            return parsed_data
        except Exception as e:
            parsed_data["unparsed"] = "No information available"
            logger.log("error", "Error during initial parsing:", traceback.format_exc())
            return parsed_data
        
    def createMap(self):
        return {
            "default_timestamp" : "timestamp",
            "fields": {
                "id": {
                    "type" : ["keyword"]
                },
                "technology": {
                    "type" : ["keyword"]
                }, 
                "tenant": {
                    "type" : ["keyword"]
                },
                "index": {
                    "type" : ["keyword"]
                },
                "log_type": {
                    "type" : ["keyword"]
                }
            }
        }
