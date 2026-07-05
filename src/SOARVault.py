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
project: SIEM project
page: soar vault
"""

from UtilsCrypto import *
import Utils as utils
import json
import traceback
import os
import tempfile

class SOARVault:
    def __init__(self, path, logger, algorithm, key_path, iv_path):
        self.path = path
        self.algorithm = algorithm
        self.key_path = key_path
        self.iv_path = iv_path
        self.logger = logger
        self.encryptor = Encryption(self.algorithm, self.key_path, self.iv_path)
        self.vault = {}
        self.load_vault()

    def load_vault(self):
        if os.path.exists(self.path):
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name
                self.encryptor.decrypt_file(self.path, tmp_path)
                with open(tmp_path, "r", encoding="utf-8") as f:
                    self.vault = json.load(f)
                os.remove(tmp_path)
            except Exception:
                self.logger.log("error", f"Error while loading vault: {traceback.format_exc()}")
        else:
            try:
                self.vault = {}
                utils.create_folders(self.path)
                self.set("scheduler", {"type": "basic", "id": "scheduler", "username": "scheduler", "password": "scheduler"})
                self.save()
            except Exception:
                self.logger.log("error", f"Error while creating vault: {traceback.format_exc()}")

    def get(self, key):
        return self.vault.get(key)

    def list_keys(self):
        return [
            {k: v for k, v in self.vault[instance].items() if k != "password"}
            for instance in self.vault
        ]

    def set(self, key: str, value: dict):
        self.vault[key] = value
        self.save()

    def save(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp:
                json.dump(self.vault, tmp, indent=2)
                tmp_path = tmp.name
            self.encryptor.encrypt_file(tmp_path, self.path)
            os.remove(tmp_path)
        except Exception:
            self.logger.log("error", f"Error while saving vault: {traceback.format_exc()}")
