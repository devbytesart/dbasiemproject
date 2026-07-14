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
document: vault_commands
"""

import traceback
from typing import Any
from UtilsCrypto import *
import json

##############################################################
###     AUTHENTICATION VAULT PART
##############################################################

# TODO change this function to adapt dynamically
def vault_set_basic_credential(self: Any, id: str, username: str, password: str):
    """
    Add basic credential to authenticate in the vault
    params: 
    - id: str => id of the instance
    - username: str => username of the user
    - password: str => password of the user
    """
    try:
        self.vault.set(id, {"type": "basic", "id": id, "username": username, "password": password})
    except:
        raise Exception(f"Error while setting basic credential {traceback.format_exc()}")

def vault_set_ollama_credential(self:Any, id:str, url:str, apikey:str = ""):
    """
    Add credentials to authenticate to a Ollama LLM
    -id: str => id of the instance
    - url: str => url of the web services
    - apikey: str (None) => apikey to connect to the webservices
    """
    try:
        self.vault.set(id, {"type": "apikey", "id": id, "url": url, "apikey": apikey})
    except:
        raise Exception(f"Error while setting Ollama credential {traceback.format_exc()}")

def vault_list_credentials(self: Any):
    """
    List the id, type and username in the vault
    params: None
    """
    try:
        return self.vault.list_keys()
    except:
        raise Exception(f"Error while listing credentials {traceback.format_exc()}")

#TODO Test permissions to delete the key before
def vault_delete_credentials(self: Any, id:str):
    """
    Delete the id of the list 
    id: str => Id of the vault to delete
    """
    try:
        self.vault.delete_key(id)
        return f"Key {id} deleted"
    except:
        raise Exception(f"Error while deleting id {traceback.format_exc()}")