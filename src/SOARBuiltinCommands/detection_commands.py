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
document: alert_commands
"""

import traceback
from typing import Any
import json
from datetime import datetime, timezone
import dateparser
import UtilsIndexing as utindex


def detection_create_alert(self: Any, name: str, type: str, severity: str, status: str, triggered: str, index:str, tenant:str, technology: str, group: bool = True, date: str=None):
    """ 
    With results of a query create an alert on the siem
    params:
    - name: str => name of the alert
    - type: str => custom type of alert such as soar_alert, siem_alert, real_time_alert ...
    - severity: str => custom severity of the alert such as Low, Medium, High, Critical ...
    - status: str => custom status of the alert such as active, closed, pending ...
    - triggered: list => data to store in the alert in format of siem result (list of json ...)
    - index: str => index where to store the alert
    - tenant: str => tenant where to store the alert in the index
    - technology: str => technology where to store the alert in the index
    - group: bool => group logs in the same alert or create one for one log
    - date: str => datetime of the alert format %Y-%m-%d %H:%M:%S.%f
    """
    try:
        print("results: " + str(triggered))
        triggered_data = json.loads(triggered).get("data", [])
        reference_id = []
        reference = []
        def create_and_enqueue_log():
            params = {
                "type": type,
                "severity": severity,
                "status": status,
                "reference": reference,
                "reference_id": reference_id,
                "date": date if date != "None" else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "grouped": group
            }
            log = utindex.create_simple_log(index, tenant, technology, name, params)
            log_str = str(log)
            log.update(params)
            self.logger.log("debug", f"Create alert named: {name} -> {log_str}")
            self.queue.enqueue(json.dumps(log).encode("utf-8"))
            return log.get("data", {}).get("parsed")
        if group:
            for res in triggered_data:
                reference_id.append(res.get("id"))
                reference.append(res)
            return create_and_enqueue_log()
        else:
            grouped_log = []
            for res in triggered_data:
                reference.clear()
                reference_id.clear()
                reference_id.append(res.get("id"))
                reference.append(res)
                grouped_log.append(create_and_enqueue_log())
            return grouped_log
    except Exception:
        self.logger.log("error", f"Failed to create the alert {traceback.format_exc()}")
        raise Exception("Failed to create alert")


def detection_create_rule(self:Any, name: str, type: str, severity: str, version: int, status: str, description: str, info:dict, query:str, index:list, index_alert:str, tenant:list, tenant_alert:str, technology: list, technology_alert:str, instance:str, loopback:str, group:bool=True, id:str=None):
    """
    Create a detection rule in a playbook or a context that it is possible to launch with a schedule task
    params:
    - name: str => Name of the detection rule
    - type: str => Type of detection rule 
    - version: int => Version of the rule
    - status: str => Status of the rule (creation, testing, production, disabled, deleted)
    - description: str => Description of the rule
    - info: dict => json of others information added by the user
    - query: str => Query of the research
    - index: list => Index list for the query
    - index_alet: str => Index where to store the alert
    - tenant: list => Tenant list for the query
    - tenant_alert: str => Tenant list to store the alert
    - technology: list => Technology list for the query
    - technology_alert: str => Technology to store the alert
    - instance: str => Name of the instance in the vault to query the siem
    - loopback: str => Time period (plan a buffer if scheduled task) for the query of the siem
    - id: str => id of the siem if rewrite in the siem
    """
    try:
        # What to do with others information
        # Interpret loopback
        _start = dateparser.parse(loopback)
        _start = _start.strftime("%Y-%m-%d %H:%M:%S.%f")
        # SIEM Search
        results = self.commands["siem_search"]["function"](instance, query, index, tenant, technology, start_time=_start)
        # Create detection alert
        return self.commands["detection_create_alert"]["function"](name, type, severity, status, results, index_alert, tenant_alert, technology_alert, group)
    except:
        self.logger.log("error",f"Failed to create the detection rule {traceback.format_exc()}")
        raise Exception("Failed to create rule")
    

