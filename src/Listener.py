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
document: listener
"""

import socket
import ssl
import threading

class Listener:
    def __init__(self, ip, port, callback, protocol='TCP', certfile=None, keyfile=None):
        self.ip = ip
        self.port = port
        self.callback = callback
        self.protocol = protocol
        self.certfile = certfile
        self.keyfile = keyfile
        self.run = False
        self.t = None
        self.buffer_size = 8160

    def start(self):
        self.run = True
        if self.protocol.upper() == 'TCP':
            self.t = threading.Thread(target=self.listen_tcp, daemon=True)
        elif self.protocol.upper() == 'UDP':
            self.t = threading.Thread(target=self.listen_udp, daemon=True)
        else:
            raise ValueError("Unsupported protocol. Use 'TCP' or 'UDP'.")
        self.t.start()

    def stop(self):
        self.run = False
        if self.protocol.upper() == 'TCP':
            # Create a dummy connection to unblock the accept call for TCP
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dummy_socket:
                try:
                    # dummy_socket.connect((self.ip, self.port))
                    dummy_socket.connect(("0.0.0.0", self.port))
                    dummy_socket.close()
                except socket.error as e:
                    print(f"Error stopping TCP listener: {e}")
        elif self.protocol.upper() == 'UDP':
            # Send a dummy packet to unblock the recvfrom call for UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dummy_socket:
                try:
                    dummy_socket.sendto(b'', (self.ip, self.port))
                except socket.error as e:
                    print(f"Error stopping UDP listener: {e}")
        self.t.join()

    def listen_tcp(self):
        context = None
        if self.certfile and self.keyfile:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # server_socket.bind((self.ip, self.port))
            server_socket.bind(("0.0.0.0", self.port))
            server_socket.listen()
            print(f"Listening on port {self.port} (TCP)")

            while self.run:
                try:
                    conn, addr = server_socket.accept()
                    if context:
                        conn = context.wrap_socket(conn, server_side=True)
                    print(f"Connected by {addr}")
                    threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
                except socket.error as e:
                    print(f"Socket error: {e}")
                    continue

        print("End of TCP socket")

    def handle_client(self, conn, addr):
        with conn:
            data = b""
            try:
                while self.run:
                    packet = conn.recv(self.buffer_size)
                    if not packet:
                        break
                    data += packet
                    self.callback(conn, data)
                    # print("after  callback")
                    data = b""
            except socket.error as e:
                print(f"Connection error with {addr}: {e}")
            finally:
                print(f"Connection with {addr} closed")

    def listen_udp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.ip, self.port))
            print(f"Listening on port {self.port} (UDP)")

            while self.run:
                try:
                    data, addr = server_socket.recvfrom(self.buffer_size)
                    print(f"Received from {addr}")
                    self.callback(None, data)
                except socket.error as e:
                    print(f"Socket error: {e}")
                    continue

        print("End of UDP socket")
