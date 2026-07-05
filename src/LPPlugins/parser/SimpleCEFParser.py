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
DOCUMENT: simple cef parser

"""

from LPParserInterface import LPParserInterface
import re, traceback

class SimpleParser(LPParserInterface):

    """ Parser for CEF format
    # CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|[Extension]"""

    def verify(self, data, logger):
        if data.startswith("CEF:"):
            return True
        return False

    def parse(self, data, logger):
        # Escape problematic characters
        # Clean the data by removing tabs, newlines, and carriage returns
        data = data.replace("\t", "").replace("\n","").replace("\r","")
        s = data.split("|")
        parsed_data = {"log_type": "cef"}
        try:
            # Check the size of CEF log
            if len(s) >= 7:
                parsed_data.update({
                    "log_version": s[0][4] if len(s[0]) > 4 else "unknown",
                    "deviceVendor": s[1],
                    "deviceProduct": s[2],
                    "deviceVersion": s[3],
                    "deviceEventClassId": s[4],
                    "name": s[5],
                    "severity": s[6]
                })
            else:
                # If the CEF log is not in the correct format, return unparsed log
                parsed_data["unparsed"] = str(s)
        except Exception as e:
            parsed_data["unparsed"] = str(s)
            logger.log("error", "Erreur de parsing initial:", traceback.format_exc())
            return parsed_data
        # Treatment of extension after the 7th element
        if len(s) > 7:
            try:
                # Analysis of key value pattern
                pattern = r'(\w+)=((?:(?! \w+=).)*)'
                matches = re.findall(pattern, s[7])

                for key, value in matches:
                    # Avoid empty keys values
                    if key:
                        parsed_data[key] = value.replace("\\", "")  # Remove backslashes
            except Exception as e:
                parsed_data["unparsed_extension"] = str(s[7])
                logger.log("Erreur de parsing de l'extension:", traceback.format_exc())
        return parsed_data
    
    def createMap(self):
        return {
                "default_timestamp" : "rt",
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
                    "deviceVendor" : {
                        "type" : ["keyword"]
                    },
                    "deviceProduct" : {
                        "type" : ["keyword"]
                    },
                    "deviceVersion" : {
                        "type" : ["keyword"]
                    },
                    "name": {
                        "type" : ["keyword"]
                    },
                    "severity": {
                        "type" : ["keyword"]
                    },
                    "rt": {
                        "type" : ["timestamp"],
                        "timezone": "Europe/Paris",
                        "format": "%Y-%m-%d %H:%M:%S.%f"
                    },
                    "externalId" : {
                        "type": ["keyword"]
                    },
                    "msg": {
                        "type": ["keyword"]
                    },
                    "categoryDeviceGroup":{
                        "type": ["keyword"]
                    },
                    "categoryBehavior": {
                        "type": ["keyword"]
                    },
                    "categoryOutcome": {
                        "type": ["keyword"]
                    },
                    "dvc": {
                        "type": ["IPv4","IPv6"]
                    },
                    "dhost": {
                        "type": ["keyword"]
                    },
                    "dvhost": {
                        "type": ["keyword"]
                    },
                    "dst": {
                        "type": ["IPv4","IPv6"]
                    },
                    "destinationZoneURI": {
                        "type": ["keyword"]
                    },
                    "src": {
                        "type": ["IPv4","IPv6"]
                    },
                    "shost": {
                        "type": ["keyword"]
                    },
                    "sourceZoneURI": {
                        "type": ["keyword"]
                    },
                    "suser" : {
                        "type" : ["keyword"]
                    },
                    "duser" : {
                        "type" : ["keyword"]
                    },
                    "cs1": {
                        "type": ["keyword"]
                    },
                    "cs2": {
                        "type": ["keyword"]
                    },
                    "cs3": {
                        "type": ["keyword"]
                    },
                    "cs4": {
                        "type": ["keyword"]
                    },
                    "cs5": {
                        "type": ["keyword"]
                    },
                    "cs6": {
                        "type": ["keyword"]
                    },
                    "cs1Label": {
                        "type": ["keyword"]
                    },
                    "cs2Label": {
                        "type": ["keyword"]
                    },
                    "cs3Label": {
                        "type": ["keyword"]
                    },
                        "cs4Label": {
                        "type": ["keyword"]
                    },
                    "cs5Label": {
                        "type": ["keyword"]
                    },
                    "cs6Label": {
                        "type": ["keyword"]
                    },
                    "amac": {
                        "type": ["MAC"]
                    },
                    "dtz": {
                        "type": ["keyword"]
                    },
                    "deviceFacility": {
                        "type": ["keyword"]
                    },
                    "deviceProcessName": {
                        "type": ["keyword"]
                    }
                }
            }
