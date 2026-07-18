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
page: unittest
"""

import socket, os, sys, json, threading, time
from tqdm import tqdm

# Add path from parent folder to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from WebRequester import *

class UnitTest:
    def testMasterCoordinator(self):
        self.path = ["127.0.0.1", 0, "webhook", "port"]
        self.data = 4443
        try:
            w = WebRequester("webhook", "my_secure_token", "127.0.0.1", 443)
            w.configure(self.path, self.data)
        except Exception as e:
            print("Error : " + str(e))

    def testSlaveCoordinator(self):
        self.path = ["127.0.0.1", 1, "webhook", "port"]
        self.data = 4446
        try:
            w = WebRequester("webhook", "my_secure_token", "127.0.0.1", )
            w.configure(self.path, self.data)
        except Exception as e:
            print("Error : " + str(e))

    def testLogCollector(self):
        try:
            ip = "localhost"
            port = 5500
            data_size = 0
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                print(f"Connected to {ip} on port {port}")
                with open("sample.log") as f:
                    lines = f.readlines()
                    data_size = len(lines)
                    for line in tqdm(lines):
                        client_socket.sendall(line.encode())
                        time.sleep(0.002) 
            print("Total lines sent:", data_size)
        except ConnectionRefusedError:
            print(f"Failed to connect to {ip}:{port}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def testLogCollectorRetrieveLogs(self):
        try:
            print("UNIT TEST RETRIEVE LOGS")
            ip = "desktop-onfm2fj"
            port = 5000
            export = ""
            wr = WebRequester("binary", "my_secure_token", ip, port)
            retrieved_count = 0  # Add for logs
            for _ in range(120):
                print(".")
                val = wr.retrieve_logs(70)
                if val is not None:
                    export += val + "\n"
                    retrieved_count += 1  # Increments counter
                time.sleep(0.8)
            with open("logs.txt","w") as f:
                f.write(export)
            print("Total lines retrieved:", retrieved_count)
        except Exception as e:
            print("Error : " + str(e))
        


if __name__ == '__main__':
    ut = UnitTest()

    # TEST MASTER AND SLAVE COORDINATOR
    #ut.testMasterCoordinator()
    #ut.testSlaveCoordinator()

    # TEST LOG COLLECTOR
    thread_sending = threading.Thread(target=ut.testLogCollector)
    # thread_retrieving = threading.Thread(target=ut.testLogCollectorRetrieveLogs)

    s = time.time()
    thread_sending.start()
    # thread_retrieving.start()

    thread_sending.join()
    # thread_retrieving.join()
    e = time.time()
    print("time: " + str(e - s))