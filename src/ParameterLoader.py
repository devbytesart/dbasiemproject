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
title: siem project
document: operation parameter loader
"""

import argparse
import json
import os

class ConfigLoader:
    def __init__(self):
        self.config = None
        self.primary = False
        self.secret = None

    def parse_arguments(self):
        """Method to parse command line and load file or dictionary as config"""
        parser = argparse.ArgumentParser(description="Load configuration from file or dictionary")
        
        # Add arguments for the file and the dictionary
        parser.add_argument('-f', '--file', type=str, help='JSON configuration file to read')
        parser.add_argument('-i', '--input', type=str, help='JSON dictionary to read')
        parser.add_argument('-p', '--primary', type=bool, help='Primary coordinator')
        parser.add_argument('-s', '--secret', type=str, help='Authentication password')

        # Parsing des arguments
        args = parser.parse_args()
        
        # Load configuration from a file or a dictionary
        if args.primary:
            self.primary = True
        if args.secret:
            self.secret = args.secret
        if args.file:
            self.load_from_file(args.file)
        elif args.input:
            self.load_from_dict(args.input)
        else:
            print('Usage: -f to load a configuration file or -i to load a configuration dictionary in JSON format. -p for mastercoordinator if primary. -s for the secret password only for master coordinator.')

    def load_from_file(self, file_path):
        """Method to load configuration from file"""
        if os.path.exists(file_path) and file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                self.config = json.load(f)
            print(f'Configuration file loaded: {self.config}')
        else:
            print(f"Error: File '{file_path}' not found or not a JSON file.")

    def load_from_dict(self, json_string):
        """Method to load configuration from dictionary"""
        try:
            print("type:" + str(type(json_string)))
            self.config = json.loads(json_string)
            print(f'Dictionary of configuration: {self.config}')
        except json.JSONDecodeError as e:
            print(f"Error: The provided dictionary is not valid {e}")

    def is_primary(self):
        """Method to get the primary status"""
        return self.primary

    def get_config(self):
        """Method to get the loaded configuration"""
        return self.config
    
    def get_secret(self):
        """Method to get the secret password"""
        return self.secret