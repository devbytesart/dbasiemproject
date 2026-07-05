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
document: utils_indexing
"""

import traceback
import json
from datetime import datetime, timezone
import Utils as utils
import base64
import random
import time

##############################################################
###     SIEM LOG
##############################################################


def create_random_id():
    """ Create a random id for a log """
    try:
        return (str(time.time()) + str(random.random())).replace(".","")
    except:
        print(f"Failed to create random id {traceback.format_exc()}")
        return None

def create_simple_log(index: str, tenant: str, technology: str, name: str, params: dict, id: str=None):
    """ Create a simple log to index
    params:
    - index: str => index of the log
    - tenant: str => tenant of the log
    - technology: str => technology of the log
    - name: str => name of the log
    - type: str => type of the log
    - params: str => params of the log to add other content
    - id: str => id of the log
    """
    try:
        # Create id 
        if id is None or id == "" or id == "None":
            id = create_random_id()
            if id is None:
                raise Exception("Failed to create id")
        # Create the log
        content = {
            "index": index,
            "tenant": tenant,
            "technology": technology,
            "name": name,  
            "parserReceivedTime": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "siem_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "id": id}
        if params:
            params = utils.safe_parse_to_json(params)
            content.update(params)
        log = {"data":{"parsed":content,"raw": base64.b64encode(json.dumps(content).encode('utf-8')).decode('utf-8')}}
        return log
    except:
        print(f"Failed to create the log {traceback.format_exc()}")
        return None


##############################################################
###     SIEM MAPPING
##############################################################

# TODO

##############################################################
###     SOAR HISTORY 
##############################################################

def create_soar_history_entry(id, author, name, params, answer, status, history=[], date=None):
    """ Add an entry to the SOAR history
    params:
    - id: str => id of the log
    - author: str => author of the log
    - name: str => name of the log
    - params: dict => params of the log
    - answer: str => answer of the log
    - status: str => status of the log
    - date: str => date of the log
    """
    try:
        # print All values
        print("id:", str(id), "name:", str(name),  "answer:", str(answer), "history:", str(history))
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        # Create table of answer
        res = [answer]
        if id is not None and any(d["id"] == id for d in history):
            res = history[id].get("answer")
            if res is None:
                res = []
            res.append(answer)
        id = len(history) if id is None else id
        answer = {
            "id": id,
            "author": author,
            "name": name,
            "command": name + " " + ' '.join(f'{str(k)}="{str(v)}"' for k, v in params.items()),
            "params": params,
            "answer": res,
            "status": status,
            "date": date
        }
        # Add the entry to the history
        existing = next((c for c in history if c["id"] == id), None)
        if existing:
            existing.update(answer)
        else:
            history.append(answer)   
        return answer
    except:
        print(f"Failed to add entry to SOAR history {traceback.format_exc()}")
        return None