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
document: webhook
"""

import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import ssl
import json
import socket
import traceback
import time
import Utils as utils

class Webhook:
    def __init__(self, ip, port, callback, auth_token, certfile, keyfile):
        self.ip = ip
        self.port = port
        self.callback = callback
        self.auth_token = auth_token
        self.certfile = certfile
        self.keyfile = keyfile
        self.KEEP_RUNNING = True
        self.server = None
        self.thread = None
        try:
            self.start()
        except Exception as e:
            print("Failed to start the server:", e)
            print(traceback.format_exc())

    def start(self):
        try:
            # self.run = True
            # self.thread = threading.Thread(target=self.run_server, daemon=True)
            self.KEEP_RUNNING = True
            self.thread = threading.Thread(target=self.run_server)
            self.thread.start()
        except Exception as e:
            print("Error in starting the server thread:", e)
            print(traceback.format_exc())

    def stop(self):
        print("RECEIVED STOP WEBHOOK")
        self.KEEP_RUNNING = False  # Stop loop run_server()

        if self.server:
            try:
                print("before shutdown")
                
                print("✅ server shutdown")
                self.server.server_close()
                time.sleep(2)
                print("✅ server closed")
                
                # Close the sicket to force free of port 
                if hasattr(self.server, 'socket'):
                    self.server.socket.close()

                print("✅ server shut down")
            except Exception as e:
                print("Error while shutting down the server:", e)

        if self.thread:
            try:
                self.thread.join(timeout=3)  # Wait max 3s to avoid blocking
                if self.thread.is_alive():
                    print("❌ Thread is still alive!")
            except Exception as e:
                print("Error while joining the server thread:", e)
        
        print("✅ STOP FUNCTION ENDED")




    def run_server(self):
        if utils.check_port_in_use(self.port):
            print(f"Port {self.port} is already in use.")

        class RequestHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    if self.path == '/webhook':
                        self.handle_webhook()
                    elif self.path == '/compressed':
                        self.handle_compressed()
                    elif self.path == '/binary':
                        self.handle_binary()
                    elif self.path == '/shutdown':
                        self.handle_shutdown()
                    else:
                        self.send_error(404, "Path not found")
                except Exception as e:
                    self.send_error(500, str(e))
                    print("Error in POST request:", e)
                    print(traceback.format_exc())


            def handle_webhook(self):
                auth_header = self.headers.get('Authorization')
                if not auth_header or auth_header != f"Bearer {self.server.auth_token}":
                    self.send_error(401, f"Unauthorized: webhook request.")
                    return
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    response = json.dumps(self.server.callback(post_data)).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(response)
                except Exception as e:
                    self.send_error(500, "Error processing webhook")
                    print("Error in handle_webhook:", e)
                    print(traceback.format_exc())

            def handle_compressed(self):
                auth_header = self.headers.get('Authorization')
                if not auth_header or auth_header != f"Bearer {self.server.auth_token}":
                    self.send_error(401, f"Unauthorized: compressed request.")
                    return
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    if self.headers.get('Content-Encoding') == utils.COMPRESSION_EXTENSION:
                        # print("Received compressed data..." + str(post_data))
                        post_data = utils.decompress_data(post_data)
                        # print("Received decompressed data after decompress..." + str(post_data))
                        if self.headers.get('Content-Type') == 'application/json':
                            post_data = post_data.decode("utf-8")
                            # print("Received compressed JSON data:", str(post_data))
                    callback_response = self.server.callback(post_data)
                    # print("Calllback response:", str(callback_response))
                    if not isinstance(callback_response, bytes):
                        response_data = json.dumps(callback_response).encode('utf-8')
                    else:
                        response_data = callback_response
                    # print("Response data:", str(response_data))
                    compressed_response = utils.compress_data(response_data)
                    # print("Compressed response:", str(compressed_response))
                    if not compressed_response:
                        raise ValueError("Failed to compress data.")
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Encoding', utils.COMPRESSION_EXTENSION)
                    self.send_header('Content-Length', str(len(compressed_response)))
                    self.end_headers()
                    self.wfile.write(compressed_response)
                except Exception as e:
                    self.send_error(500, "Error processing compressed request")
                    print("Error in handle_compressed:", e)
                    print(traceback.format_exc())

            def handle_binary(self):
                auth_header = self.headers.get('Authorization')
                if not auth_header or auth_header != f"Bearer {self.server.auth_token}":
                    self.send_error(401, f"Unauthorized binary.")
                    return
                try:
                    content_length = int(self.headers['Content-Length'])
                    get_data = self.rfile.read(content_length)
                    response_data = self.server.callback(get_data)
                    if not response_data:
                        self.send_error(404, "No more value in the queue!")
                        return
                    self.send_response(200)
                    self.send_header('Content-Type', "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(response_data)
                except Exception as e:
                    self.send_error(500, "Error processing binary data")
                    print("Error in handle_binary:", e)
                    print(traceback.format_exc())

            def handle_shutdown(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Server shutting down...')
                # threading.Thread(target=self.server.shutdown).start()
                self.server.server_close()

            def log_message(self, format, *args):
                return  # Override to disable logging

        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), RequestHandler)
            self.server.auth_token = self.auth_token
            self.server.callback = self.callback
            self.server.timeout = 1  # Add timeout to avoid blocking 

            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

            while self.KEEP_RUNNING:
                try:
                    self.server.handle_request()
                except Exception as e:
                    print(f"Error in handle_request: {e}")

        except FileNotFoundError as e:
            print("SSL certificate or key file not found:", e)
        except ssl.SSLError as e:
            print("SSL error:", e)
        except Exception as e:
            print("Unexpected error in server:", e)
            print(traceback.format_exc())
        finally:
            if self.server:
                self.server.server_close()
                print("Server closed successfully.")
