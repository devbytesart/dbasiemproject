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
project: siem project
DOCUMENT: simple syslog parser

"""

from LPParserInterface import LPParserInterface
import re, traceback, json

class SimpleParser(LPParserInterface):

    """ Parser for Generic Syslog format
    # <timestamp> <dvchost> <appname>: <message>"""

    def verify(self, data, logger):
        yslog_regex = r'.*(?P<timestamp>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s(?P<dvchost>\S+)\s(?P<appname>\S+):\s(?P<message>.*)$'
        if re.match(yslog_regex, data) is not None:
            return True
        return False

    def parse(self, data, logger):
        # Escape problematic characters
        # Clean the data by removing tabs, newlines, and carriage returns
        data = data.replace("\t", "").replace("\n","").replace("\r","").replace("\\", "").replace("\"", "").replace("\'", "").strip()
        logger.log("debug", "Data to parse: " + str(data))
        parsed_data = {"log_type": "syslog"}
        try:
            # TODO test the regex
            # Regex
            # syslog_regex = r'^\<[\d]+\>(?P<timestamp>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s(?P<hostname>\S+)\s(?P<appname>\S+):\s(?P<message>.*)$'
            syslog_regex = r'.*(?P<timestamp>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s(?P<dvchost>\S+)\s(?P<appname>\S+):\s(?P<message>.*)$'
            match = re.match(syslog_regex, data)
            if match:
                parsed_data.update(match.groupdict())
            else:
                # If the CEF log is not in the correct format, return unparsed log
                parsed_data["unparsed"] = str(data)
        except Exception as e:
            parsed_data["unparsed"] = str(data)
            logger.log("error", "Error during initial parsing:", traceback.format_exc())
            return parsed_data
        # Treatment of extension after the 7th element
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
                    },
                    "log_version": {
                        "type" : ["keyword"]
                    },
                    "timestamp": {
                        "type" : ["timestamp"],
                        "timezone": "Europe/Paris",
                        "format": "%Y-%m-%d %H:%M:%S.%f"
                    },
                    "message": {
                        "type": ["keyword"]
                    },
                    "dvchost": {
                        "type": ["keyword"]
                    },
                    "appname": {
                        "type": ["keyword"]
                    }
                }
            }
