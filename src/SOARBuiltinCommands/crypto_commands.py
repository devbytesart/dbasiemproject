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
document: crypto_commands
"""

import traceback
from typing import Any
from UtilsCrypto import *
import json


##############################################################
###     ENCRYPTION PART
##############################################################

def crypto_generate_aes256_key(file_path: str):
    """
    Generate a key for the encryption
    params:
    - file_path: str => path to the file
    """
    try:
        Encryption.generate_key(file_path)
        return "Key generated"
    except:
        return f"Error during generation: {traceback.format_exc()}"


def crypto_generate_aes_256_iv(file_path: str):
    """
    Generate a iv for the encryption
    params:
    - file_path: str => path to the file
    """
    try:
        Encryption.generate_iv(file_path)
        return "IV generated"
    except:
        return f"Error during generation: {traceback.format_exc()}"


