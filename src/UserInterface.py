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
document: user interface
"""

import json
import random
from ServiceBase import *
from Logger import *
from flask import Flask, Response, render_template, render_template_string, request, jsonify, send_from_directory, make_response, abort, redirect, url_for, session, send_file
from flasgger import Swagger
from pathlib import Path
import markdown
from functools import wraps
from WebRequester import *
from Configurator import *
from ParameterLoader import *
from CMDHandler import *
from QueueManager import *
from Webhook import *
# from ReportManager import *
import UtilsEnum as uenum
import uuid
import tempfile
import io

#app = Flask(__name__)
#app.secret_key = str(random.randint(1, 1000000000))
# TODO add secure headers for the web requests

#####################
# UI CLASS PART
#####################

class UserInterface(ServiceBase):
    def __init__(self, config_file, config):
        # self.file_path = file_path
        print("USERINTERFACE INIT")
        self.configurator = Configurator(config_file, config)
        self.load_configuration()
        self.logger = Logger(self.id, self.monitoring_log_level, self.monitoring_log_path, self.monitoring_max_queue_size, self.monitoring_max_file, self.monitoring_max_file_size, self.monitoring_enable_print, self.monitoring_enable_queue, self.monitoring_enable_file)
        self.cmdhandler = CMDHandler({
            "configure":self.handle_set_config, 
            "configuration":self.configurator.handle_get_configuration,
            "shutdown":self.handle_shutdown, 
            "retrieve_logs":self.handle_retrieve_logs, 
            "retrieve_monitoring": self.handle_retrieve_monitoring,
            "retrieve_mapping": self.handle_retrieve_mapping})
        # self.dashboard_list = {}
        self._start_microservices()
#        self.app = Flask(__name__)
        # TODO change for a better secret 
#        self.app.secret_key = str(random.randint(1, 1000000000))
#        self.setup_routes()

    def load_configuration(self):
        try:
            print("LOAD NEW CONFIG")
            self.config = self.configurator.get_config()
            # ID
            self.id = self.config["id"]
            # REQUIRED PERMISSIONS
            self.required_permissions = [{"resource":"userinterface", "type": "service", "read": True, "write": False}]
            # WEB REQUESTER
            self.proxies = self.config["webrequester"]["proxy"]
            self.timeout = self.config["webrequester"]["timeout"]
            self.slave_reverse = self.config["webrequester"].get("slave_reverse")
            # WEB SERVICE
            self.webserver_host = self.config["webserver"]["host"]
            self.webserver_port = self.config["webserver"]["port"]
            self.webserver_auth_token = self.config["webserver"]["auth_token"]
            self.webserver_certfile = self.config["webserver"]["certs"]["certfile"]
            self.webserver_keyfile = self.config["webserver"]["certs"]["keyfile"]
            # WEBHOOK
            self.webhook_host = self.config["webhook"]["host"]
            self.webhook_port = self.config["webhook"]["port"]
            self.webhook_token = self.config["webhook"]["auth_token"]
            self.webhook_certfile = self.config["webhook"]["certs"]["certfile"]
            self.webhook_keyfile = self.config["webhook"]["certs"]["keyfile"]
            # QUEUE
            self.max_queue_size = self.config["queue"]["max_queue_size"]
            self.backup_file = self.config["queue"]["backup_file"]
            self.backup_max_file = self.config["queue"]["backup_max_file"]
            self.max_backup_file_size = self.config["queue"]["max_backup_file_size"]
            # LOGGER
            self.monitoring_log_level = self.config["logger"]["log_level"]
            self.monitoring_log_path = self.config["logger"]["log_path"]
            self.monitoring_max_queue_size = self.config["logger"]["max_queue_size"]
            self.monitoring_max_file = self.config["logger"]["max_file"]
            self.monitoring_max_file_size = self.config["logger"]["max_file_size"]
            self.monitoring_enable_print = utils.convert_param_type(self.config["logger"]["enable_print"], bool)
            self.monitoring_enable_queue = utils.convert_param_type(self.config["logger"]["enable_queue"], bool)
            self.monitoring_enable_file = utils.convert_param_type(self.config["logger"]["enable_file"], bool)
            # SLAVE COORD
            if "slavecoordinator" in self.config and "id" in self.config["slavecoordinator"]:
                self.slavecoords_id = self.config["slavecoordinator"]["id"]
                self.slavecoords_host = self.config["slavecoordinator"]["host"]
                self.slavecoords_port = self.config["slavecoordinator"]["port"]
                self.slavecoords_auth_token = self.config["slavecoordinator"]["auth_token"]
                self.slavecoordsReq = WebRequester(self.slavecoords_host, self.slavecoords_port, self.slavecoords_auth_token)
            else:
                self.slavecoordsReq = None
            # INDEX SEARCH MOTOR
            print("CONFIG INDEXSEARCHMOTOR")
            if "indexsearchmotor" in self.config and "id" in self.config["indexsearchmotor"]:
                print(" in CONFIG INDEXSEARCHMOTOR")
                self.indexsearchmotors_id = self.config["indexsearchmotor"]["id"]
                self.indexsearchmotors_host = self.config["indexsearchmotor"]["host"]
                self.indexsearchmotors_port = self.config["indexsearchmotor"]["port"]
                self.indexsearchmotors_auth_token = self.config["indexsearchmotor"]["auth_token"]
                self.indexsearchmotorsReq = WebRequester(self.indexsearchmotors_host, self.indexsearchmotors_port, self.indexsearchmotors_auth_token)
            else:
                self.indexsearchmotorsReq = None
            # REPORT INDEX
            # if "reporting" in self.config and "index" in self.config["reporting"]:
            #     self.reporting_index = self.config["reporting"]["index"]
            # else:
            #     self.reporting_index = "soar"
            self.reporting_index = []
            # AUTHENTICATOR
            self.authenticatorsReq = None
            if "authenticator" in self.config and "id" in self.config["authenticator"]:
                self.authenticators_id = self.config["authenticator"]["id"]
                self.authenticators_host = self.config["authenticator"]["host"]
                self.authenticators_port = self.config["authenticator"]["port"]
                self.authenticators_auth_token = self.config["authenticator"]["auth_token"]
                self.authenticatorsReq = WebRequester(self.authenticators_host, self.authenticators_port, self.authenticators_auth_token)
            # SOAR
            if "soar" in self.config and "id" in self.config["soar"]:
                self.soars_id = self.config["soar"]["id"]
                self.soars_host = self.config["soar"]["host"]
                self.soars_port = self.config["soar"]["port"]
                self.soars_auth_token = self.config["soar"]["auth_token"]
                self.soarsReq = WebRequester(self.soars_host, self.soars_port, self.soars_auth_token)
            else:
                self.soarsReq = None
            print("END OF CONFIGURATION")
        except:
            self.logger.log("error", f"Error during configuration loading: {traceback.format_exc()}")

    def _load_stats(self):
        # TODO
        pass

    def _stop_microservices(self):
        try:
            print("STOP MICRO SERVICES")
            self.webhook.stop()
            print("AFTER STOP WEBHOOK")
            self.app = None
            self.logger.log("info",f"Stop microservices {self.id}")
            return True
        except:
            self.logger.log("error", f"Error during microservices stopping: {traceback.format_exc()}")
            return False
        # TODO stop the webhook

    def _start_microservices(self):
        print("START MICRO SERVICES")
        self.logger.log("info",f"Start microservices {self.id}")
        self.webhook = Webhook(self.webhook_host, self.webhook_port, self.cmdhandler.handle_json, self.webhook_token, self.webhook_certfile, self.webhook_keyfile)
        self.queue_manager = QueueManager(self.max_queue_size, self.backup_file, self.backup_max_file, self.max_backup_file_size)
        # self.report_manager = ReportManager(self.logger, self.indexsearchmotorsReq)
        self.app = Flask(__name__)
        # Start swagger
        self.app.config['SWAGGER'] = {
            'title': 'Documentation API du SIEM',
            'uiversion': 3
        }
        self.swagger = Swagger(self.app, template={
            "swagger": "2.0", 
            "info": {
                "title": "SIEM API",
                "description": "SIEM API protected by authentication",
                "version": "1.0"
            },
            "securityDefinitions": {
                "SessionAuth": {
                    "type": "apiKey",
                    "name": "Cookie",
                    "in": "header",
                    "description": "Authentication via session Flask (cookie)"
                }
            }
        })
        # TODO change for a better secret 
        self.app.secret_key = str(random.randint(1, 1000000000))
        print("SETUP ROUTES")
        self.setup_routes()

    def _restart_microservices(self):
        try:
            stopped = self._stop_microservices()
            if stopped:
                return self._start_microservices()
            else:
                return False
        except:
            self.logger.log("error", f"Failed to restart microservices: {traceback.format_exc()}")
            return False

    def handle_retrieve_monitoring(self, data):
        try:
            print("Userinterface handle_retrieve_monitoring called: " + str(data))
            results = self.logger.retrieve_monitoring(data)
            if results:
                return results
            # return {"status": "error", "message": "Failed to retrieve monitoring data"}
            return None
        except:
            self.logger.log("error", f"Failed to retrieve monitoring data: {traceback.format_exc()}")
            # return {"status": "error", "message": "Failed to retrieve monitoring data"}
            return None
        
    def handle_retrieve_logs(self, size):
        try:
            index = size.get("index",None)
            if index and index not in self.reporting_index:
                self.reporting_index.append(index)
            # Using bytearray to improve performance
            elements = bytearray(b"[") 
            size = int(size["size"])
            elements_count = 0
            for _ in range(size):
                dequeued_element = self.queue_manager.dequeue(1)
                if not dequeued_element:
                    break
                # Add , if not first element
                if elements_count > 0:
                    elements.extend(b",") 
                # Add current element
                elements.extend(dequeued_element)
                elements_count += 1
            if elements_count > 0:
                elements.extend(b"]")  # Close the array
                print("Result: " + str(elements))
                return bytes(elements)  # Return as bytes
            else:
                return None
        except Exception as e:
            self.logger.log("error",f"Error while retrieving logs: {traceback.format_exc()}")
            # TODO: Reinsert data in queue in case of error
            return None

    def handle_retrieve_mapping(self, data):
        # TODO implement a better mapping...
        return {
            "fields": {
                "id": {
                    "type": "string",
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
                "name": {
                    "type" : ["keyword"]
                },
                "type": {
                    "type" : ["keyword"]
                }, 
                "dashboard_id": {
                    "type" : ["keyword"]
                },
                "report_id": {
                    "type" : ["keyword"]
                },
                "siem_timestamp": {
                    "type" : "timestamp",
                    "timezone": "Europe/Paris",
                    "format": "%Y-%m-%d %H:%M:%S.%f"
                }, 
                "parserReceivedTime": {
                    "type" : "timestamp",
                    "timezone": "Europe/Paris",
                    "format": "%Y-%m-%d %H:%M:%S.%f"
                }
            }
        }

    def handle_set_config(self, data):
        try:
            print("New configuration received: " + str(data))
            self.configurator.set_config(data)
            print("Userinterface handle_set_config called")
            self.load_configuration()
            return self._restart_microservices()
            # TODO change this to return json object
            # if self._restart_microservices():
                #return {"status": "success", "message": "Configuration loaded successfully."}
        except:
            self.logger.log("error", f"Failed to set configuration: {traceback.format_exc()}")
            # return {"status": "error", "message": "Failed to set configuration."}
            return False
    
    def handle_shutdown(self):
        return self._stop_microservices()

    def read_json(self, file):
        try:
            # TODO ask to mastercoordinator to send the configuration file
            # wr = WebRequester("webhook", self.mastercoords[0]["auth_token"], self.mastercoords[0]["host"], self.mastercoords[0]["port"])
            # return json.loads(wr.configuration())
            # TODO change the session token
            token = json.loads(session.get("user_id"))
            if file == "globalconfiguration":
                if not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":"global_configuration", "type": "global_configuration", "read": True, "write": False}])):
                    return {"message": "Failed to load global configuration - Not enough permissions to read global_configuration"}
                return json.loads(self.slavecoordsReq.get_global_configuration(session.get("user_id")))
            elif file == "globalauthorisation":
                if not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":"global_privileges", "type": "global_configuration", "read": True, "write": False}])):
                    return {"message": "Failed to load global configuration - Not enough permissions to read global_privileges"}
                return json.loads(self.slavecoordsReq.get_privileges(session.get("user_id")))
            else:
                return {"configuration": "not found"}
        except:
            self.logger.log("error", f"Failed to retrieve configuration: {traceback.format_exc()}")
            return None

    def write_json(self, file, data):
        try:
            token = json.loads(session.get("user_id"))
            if file == "globalconfiguration":
                if not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":"global_configuration", "type": "global_configuration", "read": True, "write": True}])):
                    return {"message": "Failed to load global configuration - Not enough permissions to read global_configuration"}
                return self.slavecoordsReq.set_global_configuration(session.get("user_id"), data)
            elif file == "globalauthorisation":
                if not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":"global_privileges", "type": "global_configuration", "read": True, "write": True}])):
                    return {f"message": "Failed to load global configuration - Not enough permissions to read global_privileges"}
                return self.slavecoordsReq.set_privileges(session.get("user_id"), data)
            else:
                return {"configuration": "not found"}
            # TODO ask to mastercoordinator to update the configuration file
            # TODO change this with the configuration file
            # wr = WebRequester("webhook", self.mastercoords[0]["auth_token"], self.mastercoords[0]["host"], self.mastercoords[0]["port"])
        except:
            self.logger.log("error", f"Failed to update configuration: {traceback.format_exc()}")
            return None

    def query(self, data):
        try:
            print("In query",str(data))
            data["session_token"] = session.get("user_id")
            # current_id = json.loads(session.get("user_id")).get("username") + "_" + str(data["page_id"])
            current_id = utils.create_current_id(json.loads(session.get("user_id")).get("username"), str(data["page_id"]))
            data["current_id"] = current_id
            # ims = self.get_indexsearchmotors()
            # wr = WebRequester("webhook", ["auth_token"], ims[0]["host"], ims[0]["port"])
            start_time_query = time.time()
            results = self.indexsearchmotorsReq.query_data(data)
            print("Time taken to query: ", time.time() - start_time_query)
            if results:
                return results
            else:
                return []
        except:
            self.logger.log("error", f"Failed to query data: {traceback.format_exc()}")
            return None
    
#####################
# DECORATOR PART
#####################

    def setup_routes(self):
        """
        Define all routes for Flask."""

        @self.app.context_processor
        def inject_page_title():
            # Get the endpoint of the current route
            endpoint = request.endpoint or ""
            
            # if endpoint is empty or index, use a default title
            if not endpoint or endpoint == "index":
                title = "Home"
            else:
                # Convert endpoint in readable title
                title = endpoint.replace("_", " ").title()

            # Inject "page title" in all templates 
            return dict(page_title=title)

        #####################
        # ROUTE PART
        #####################

        # Basic home route redirecting to login
        @self.app.route('/')
        def home():
            return redirect(url_for('login'))

        # Login page route
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """
            Login function to authenticate to the web interface of the Application.
            ---
            tags:
              - name: Authentication
            summary: Login Page to authenticate to the web page.
            description: > 
              Displays the login form (GET).  
              Processes the login (POST).  
              If credentials are valid, the user is redirected to the Search page.  
              If authentication fails, the login page is redisplayed with an error message.
            produces:
              - text/html
            parameters:
              - name: username
                in: formData
                type: string
                required: true
                description: Username of the user.
              - name: password
                in: formData
                type: string
                required: true
                description: Password of the user.
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Login page displayed (GET) or redisplayed on authentication failure (POST).
                schema:
                  type: string
                  description: HTML Login Page
              302:
                description: Redirect to the Search page on successful authentication.
                headers:
                  Location:
                    description: URL of the search page
                    schema:
                      type: string
                      example: /search
              401:
                description: Invalid Credentials - login page displayed with error message.
            """
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')

                #TODO modify this part with the real authentication
                # if username == "dante" and password == "dante":
                #     session['user_logged_in'] = True
                #     session['user_id'] = 'dante_id'
                #     return redirect(url_for('Search'))
                jwt_token = self.authenticatorsReq.sign_in(username, password)
                print("JWT_TOKEN:", jwt_token)
                if jwt_token != "null" and jwt_token != "" and jwt_token is not None:
                    session['user_logged_in'] = True
                    session['user_id'] = jwt_token
                    self.logger.log("info",f"Successful login {username} on {self.id}")
                    return redirect(url_for('Search'))
                else:
                    self.logger.log("warning",f"Failed login {username} on {self.id}")
                    return render_template('login.html', error="Invalid username or password")

            return render_template('login.html')

        # Change password route
        @self.app.route('/changepassword', methods=['GET', 'POST'])
        @login_required
        def changepassword():
            """
            Change password function when the user is connected
            ---
            tags:
              - name: Authentication
            summary: Change password formular page
            description: > 
              Displays the signup form (GET). 
              Processes the changepassword request (POST).  
              Users must be connectoed to change his password
            produces:
              - text/html
            parameters:
              - name: username
                in: formData
                type: string
                required: true
                description: Username of the user.
              - name: password
                in: formData
                type: string
                required: true
                description: Password of the user.
              - name: confirm_password
                in: formData
                type: string
                required: true
                description: Confirm the password
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success page displayed (GET) or redisplayed on user creation failure (POST).
                schema:
                  type: string
                  description: HTML Sign up Page
              302:
                description: Redirect to the Login page on successful user creation.
                headers:
                  Location:
                    description: URL of the Login page
                    schema:
                      type: string
                      example: /login
              401:
                description: Error during user creation - Page displayed with error message.
            """
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                # Validate form data
                if password != confirm_password:
                    self.logger.log("warning",f"Failed password changed {username} on {self.id}")
                    return render_template('changepassword.html', error="Passwords do not match.")
                success = self.authenticatorsReq.change_password(session.get("user_id"), username, password)
                if success:
                    self.logger.log("info",f"Successful password changed {username} on {self.id}")
                    return redirect(url_for('login'))  # Redirect to login page
                else:
                    self.logger.log("warning",f"Failed password changed {username} on {self.id}")
                    return render_template('changepassword.html', error="Error changing password. Please try again.")
            return render_template('changepassword.html')



        # Signup page route
        @self.app.route('/signup', methods=['GET', 'POST'])
        def signup():
            """
            Sign up function to create a user in the application.
            ---
            tags:
              - name: Authentication
            summary: Sign up Page to create a user
            description: > 
              Displays the signup form (GET). 
              Processes the signup request (POST).  
              If signup is created, the user is added to the database without any permissions.
              Permissions must be managed by an administrator.
            produces:
              - text/html
            parameters:
              - name: username
                in: formData
                type: string
                required: true
                description: Username of the user.
              - name: password
                in: formData
                type: string
                required: true
                description: Password of the user.
              - name: confirm_password
                in: formData
                type: string
                required: true
                description: Confirm the password
              - name: email
                in: formData
                type: string
                required: true
                description: email of the user
              - name: auth_type
                in: formData
                type: string
                required: true
                description: Describe the type of authentication (local, ldap...)
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Signup page displayed (GET) or redisplayed on user creation failure (POST).
                schema:
                  type: string
                  description: HTML Sign up Page
              302:
                description: Redirect to the Login page on successful user creation.
                headers:
                  Location:
                    description: URL of the Login page
                    schema:
                      type: string
                      example: /login
              401:
                description: Error during user creation - Signup page displayed with error message.
            """
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                email = request.form.get('email')
                auth_type = request.form.get('auth_type', "local")    
                # Validate form data
                if not username or not password or not confirm_password or not email or not auth_type:
                    return render_template('signup.html', error="All fields are required.")
                if password != confirm_password:
                    return render_template('signup.html', error="Passwords do not match.")
                # Simulate user creation logic (replace with actual logic)
                success = self.authenticatorsReq.sign_up(username, password, email, auth_type)
                if success:
                    self.logger.log("info",f"Success password changed {username} on {self.id}")
                    return redirect(url_for('login'))  # Redirect to login page
                else:
                    self.logger.log("warning",f"Failed user signup {username} on {self.id}")
                    return render_template('signup.html', error="Error creating account. Please try again.")
            return render_template('signup.html')

        # Logout route
        @self.app.route('/logout')
        @login_required
        def logout():
            """
            Logout function to logout from the Application.
            ---
            tags:
              - name: Authentication
            summary: Logout Page for the application.
            description: > 
              Displays the login form (GET).  
              Logout the user from the application.
            produces:
              - text/html
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Login page displayed (GET).
                schema:
                  type: string
                  description: HTML Login Page
              401:
                description: Invalid session - Logout undefined error.
            """
            try:
                self.authenticatorsReq.sign_out(session.get("user_id"))
            except:
                self.logger.log("error", f"Failed to sign out: {traceback.format_exc()}")
            session.pop('user_logged_in', None)
            return redirect(url_for('login'))

        @self.app.route('/edition')
        @login_required
        def Edition():
            """
            Redirection to Edition page to create Reports and Dashboards.
            ---
            tags:
              - name: Redirection
            summary: Redirection to application page.
            description: > 
              Displays the Edition page (GET).  
              If credentials are valid, the user is redirected to the Edition page.  
              If authentication fails, the login page is displayed.
            produces:
              - text/html
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Edition page displayed.
                schema:
                  type: string
                  description: HTML Edition Page
              302:
                description: Redirect to the edition page on successful authentication.
                headers:
                  Location:
                    description: URL of the edition page
                    schema:
                      type: string
                      example: /edition
              401:
                description: Invalid Credentials - login page displayed.
            """
            return render_template('edition.html')
        

        @self.app.route('/reset_research_timeout')
        @login_required
        def reset_research_timeout():
            """
            Reset the timeout to keep the session awake
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Monitoring
            description: > 
              Reset the user page timeout session
              GET: Get the page to reset the session timeout
            security:
              - SessionAuth: []
            responses:
              200:
                description: Research timeout reset successfully
              400:
                description: Failed to reset research timeout
            """
            try:
                if self.indexsearchmotorsReq.reset_research_timeout(session.get("user_id")):
                    return {"status": "success", "message": "Research timeout reset successfully"}, 200
                raise Exception("Failed to reset research timeout")
            except:
                self.logger.log("error", f"Failed to reset research timeout: {traceback.format_exc()}")
                return {"status": "error", "message": "Failed to reset research timeout"}, 400

        @self.app.route('/save_dashboard', methods=['POST'])
        @login_required
        def save_dashboard(dtype="dashboard"):
            """
            Save the dashboard from the Edition page
            ---
            tags:
              - name: Dashboard
            summary: Save the dashboard
            description: > 
              Save the dashboard on the SIEM. Add the dashboard in the queue and wait the logindexer to get the dashboard.
              POST: Save the dashboard on the queue of the user interface
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                description: > 
                  Information to add in the query to be indexed
                    id -> str : Unique id of the log
                    name -> str : Name of the dashboard
                    type -> str: Type of widgets (report or dashboard)
                    index -> str: Index of the report (must correspond to the logindexer that get the report)
                    tenant -> str: Tenant of the report to store the report
                    technology -> str: Technology where to store the report
                    widgets -> dict: json data of all widgets that compose the report
                    siem_timestamp -> date of the siem
                    parserReceivedTime -> same as siem_timestamp
            responses:
              200:
                description:
                  Return json message : saved successful
                schema:
                  type: object
              500:
                description: Error message - Failed to save dashboard
            """
            try:
                data = request.json
                token = json.loads(session.get("user_id"))
                user_id = token.get("id")
                dt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
                # Protect data entries from malicious inputs
                data = utils.sanitize_json(data)
                # Name
                name = data.get("name", "Unnamed")
                # Verify permissions
                # Check index permissions write
                if not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":"userinterface", "type": "service", "read": True, "write": True}])):
                    return jsonify({"message": "Failed to save dashboard/report - Not enough permissions on userinterface"}), 401
                elif not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":data.get("index"), "type": "index", "read": True, "write": True}])):
                    return jsonify({"message": "Failed to save dashboard/report - Not enough permissions on index"}), 401
                elif not json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), [{"resource":data.get("tenant"), "type": "tenant", "read": True, "write": True}])):
                    return jsonify({"message": "Failed to save dashboard/report - Not enough permissions on tenant"}), 401
                # json dumps widgets
                log = {"data": {"parsed": {
                    "id": utils.create_unique_id(), 
                    "name": name,
                    "type": dtype,
                    dtype + "_id": data.get("name") + "_" + user_id, 
                    # "index": self.reporting_index,
                    "index": data.get("index"),
                    "tenant": data.get("tenant"),
                    "technology": data.get("technology"),
                    "widgets": json.dumps(data["widgets"]) if "widgets" in data else {},
                    "siem_timestamp": dt, 
                    "parserReceivedTime": dt
                }}}
                log["data"]["raw"] = base64.b64encode(json.dumps(log["data"]["parsed"]).encode('utf-8')).decode('utf-8')
                self.queue_manager.enqueue(json.dumps(log).encode('utf-8'))
                self.logger.log("info", f"Saving dashboard/report by user: {user_id}")
                # with open('dashboard.json', 'w') as f:
                    # json.dump(data, f)
                return jsonify({"message": "Dashboard/Report saved successfully"})
            except Exception as e:
                self.logger.log("error", f"Failed to save dashboard/report: {traceback.format_exc()}")
                return jsonify({"message": "Failed to save dashboard/report"}), 500

        @self.app.route('/save_report', methods=['POST'])
        @login_required
        def save_report(dtype="report"):
            """
            Save the reports from the Edition page
            ---
            tags:
              - name: Reports
            summary: Save the reports
            description: > 
              Save the report on the SIEM. Add the report in the queue and wait the logindexer to get the report.
              POST: Save the report on the queue of the user interface
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                description: > 
                  Information to add in the query to be indexed
                    id -> str : Unique id of the log
                    name -> str : Name of the report
                    type -> str: Type of widgets (report or dashboard)
                    index -> str: Index of the report (must correspond to the logindexer that get the report)
                    tenant -> str: Tenant of the report to store the report
                    technology -> str: Technology where to store the report
                    widgets -> dict: json data of all widgets that compose the report
                    siem_timestamp -> date of the siem
                    parserReceivedTime -> same as siem_timestamp
            responses:
              200:
                description:
                  Return json message : saved successful
                schema:
                  type: object
              500:
                description: Error message - Failed to save report
            """
            return save_dashboard(dtype)


        @self.app.route("/downloads", methods=['GET'])
        @login_required
        def download_document():
            """
            Download reports 
            ---
            tags:
              - name: Reports
            summary: Display reports
            description: > 
              Download the report
              GET: Download the report
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                description: > 
                  Get to the temporary page to download the report
                  document_id -> str : temporary id of the item to download
                  token -> str: Token to check permissions
            responses:
              200:
                description:
                  Return the json data of type table
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
              404:
                description: No document found
            """
            try:
                document_id = request.args.get("id", None)
                token = session.get("user_id")

                if document_id is None:
                    raise Exception("Missing document id.")

                # Get content (base64 with prefix file/pdf:... or file/csv:...)
                report_b64 = self.indexsearchmotorsReq.download_document(token, document_id).decode("utf-8").strip('"')
                print("report_b64:", str(report_b64), str(type(report_b64)))
                if not report_b64:
                    raise Exception("No document found!")

                # Detection of format with prefix
                prefix_pdf = f"{uenum.SIEM_Field_Format.file.value}/{uenum.SIEM_File_Type.pdf.value}:"
                prefix_csv = f"{uenum.SIEM_Field_Format.file.value}/{uenum.SIEM_File_Type.csv.value}:"

                if report_b64.startswith(prefix_pdf):
                    file_format = "pdf"
                    mimetype = "application/pdf"
                    file_data = base64.b64decode(report_b64[len(prefix_pdf):])
                elif report_b64.startswith(prefix_csv):
                    file_format = "csv"
                    mimetype = "text/csv; charset=utf-8"
                    file_data = base64.b64decode(report_b64[len(prefix_csv):])
                else:
                    raise Exception("Unknown file format!")

                # Conver the file in memory
                file_obj = io.BytesIO(file_data)
                self.logger.log("info", f"File {document_id}.{file_format} downloaded.")
                # Download the file
                return send_file(
                    file_obj,
                    as_attachment=True,
                    download_name=f"{document_id}.{file_format}",
                    mimetype=mimetype
                )

            except Exception:
                self.logger.log("error", f"Error in download document {traceback.format_exc()}")
                return jsonify({"message": "No document found!"}), 404



        @self.app.route('/get_dashboard_list', methods=['POST'])
        @login_required
        def get_dashboard_list():
            """
            List all dashboards available for users
            ---
            tags:
              - name: Dashboard
            summary: Dashboard display page
            description: List all dashboards available for users
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                description: > 
                  Query the SIEM to retrieve available dashboard for the user
                  startTime (default time : 01-01-1970 00:00:00) -> str : Datetime of query start
                  endTime (default time: 01-01-2500 00:00:00) -> str : Datetime of query end
                  index -> array : list of indices to search data
                  page_id -> str : unique id of the page request to retrieve data later
                  query -> str : request command for the search
                  technology (default []) -> array : list of technologies to limit the scope
                  tenant -> str : list of tenants where to perform the request
            responses:
              200:
                description: Success - list of dashboards available for the user
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                      example: OK
                    reports:
                      type: array
                      items:
                        type: string
                        example: Monthly dashboard
              400:
                description: >
                  Invalid request format
                  or 
                  Missing page_id
                  or 
                  Invalid user data
              401:
                description: Not authorized - User not authenticated
              404:
                description: No dashboards found
              500:
                description: >
                  No data received
                  or 
                  Invalid data format
            """
            try:
                print("Getting dashboard list")
                # Verify JSON requests
                r = request.get_json()
                r= r.get("params",{})
                if not r:
                    return jsonify({"message": "Invalid request format"}), 400
                print("Request: ", r)
                page_id = r.get("page_id")
                if not page_id:
                    return jsonify({"message": "Missing page_id"}), 400
                print("Page id: ", page_id)
                index = [r.get("index", "")]
                tenant = [r.get("tenant", "")]
                technology = [r.get("technology", "")]
                query = "!search type:dashboard"
                # Verify users 
                user_data = session.get("user_id")
                if not user_data:
                    return jsonify({"message": "User not authenticated"}), 401
                user_id = json.loads(user_data).get("id")
                if not user_id:
                    return jsonify({"message": "Invalid user data"}), 400
                query_payload = {
                    "query": query,
                    "startTime": None,
                    "endTime": None,
                    "index": index,
                    "tenant": tenant,
                    "technology": technology,
                    "page_id": page_id
                }
                print("Request: ", str(query_payload))
                # Execute requests
                data = self.query(query_payload)
                if not data:
                    return jsonify({"message": "No data received"}), 500
                # Parsing secured JSON
                try:
                    data_json = json.loads(data)
                    print("Data: ", str(data_json))
                    dashboard_items = data_json.get("data", [])
                except json.JSONDecodeError as e:
                    print(f"Error in JSON parsing: {e}")
                    return jsonify({"message": "Invalid data format"}), 500
                # Treatment dashboards
                dashboard_list = ["None"]
                for i in dashboard_items:
                    if "name" in i:
                        dashboard_list.append(i["name"])
                return jsonify(dashboard_list), 200
            except Exception as e:
                print(f"Error in get_dashboard_list: {e}")
                return jsonify({"message": "No dashboards found"}), 404


        @self.app.route('/get_history_list', methods=['GET'])
        @login_required
        def get_history_list():
            """
            Get the history list for the SOAR
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Get the list of history associated with the index, tenant and vault
            produces:
              - text/html
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                description: > 
                  Query the SIEM to retrieve available dashboard for the user
                  startTime (default time : 01-01-1970 00:00:00) -> str : Datetime of query start
                  endTime (default time: 01-01-2500 00:00:00) -> str : Datetime of query end
                  index -> array : list of indices to search data
                  page_id -> str : unique id of the page request to retrieve data later
                  query -> str : request command for the search
                  technology (default []) -> array : list of technologies to limit the scope
                  tenant -> str : list of tenants where to perform the request
            responses:
              200:
                description: Success - Display the list of history in SOAR
                schema:
                  type: string
                  description: List of context, playbook
              400:
                description: Invalid user data
              401:
                description: Invalid Credentials - login page displayed.
              404:
                description: No history found
              500:
                description: No data received or invalid data format
            """
            try:
                # TODO get the history list from the SOAR and not the indexsearchmotor
                print("Getting history list")

                # Read parameter in the URL (GET method )
                index = request.args.get("index", "soar")
                tenant = request.args.get("tenant", "soar")
                page_id = request.args.get("page_id", random.randint(1, 1000000000))

                print(f"Params - index: {index}, tenant: {tenant}, page_id: {page_id}")

                query = "!search type:context or type:playbook"

                # Get verification of user 
                user_data = session.get("user_id")
                if not user_data:
                    return jsonify({"message": "User not authenticated"}), 401

                user_id = json.loads(user_data).get("id")
                if not user_id:
                    return jsonify({"message": "Invalid user data"}), 400

                query_payload = {
                    "query": query,
                    "startTime": None,
                    "endTime": None,
                    "index": [index],
                    "tenant": [tenant],
                    "technology": ["soar"],
                    "page_id": page_id
                }

                print("Query payload:", query_payload)

                data = self.query(query_payload)
                if not data:
                    return jsonify({"message": "No data received"}), 500

                try:
                    data_json = json.loads(data)
                    print("Data received:", data_json)
                    history_items = data_json.get("data", [])
                except json.JSONDecodeError as e:
                    print(f"Error in JSON parsing: {e}")
                    return jsonify({"message": "Invalid data format"}), 500

                # Treatment of historic
                history_list = ["None"]
                for i in history_items:
                    if "name" in i:
                        history_list.append(i["name"])

                return jsonify(history_list), 200

            except Exception as e:
                print(f"Error in get_history_list: {e}")
                return jsonify({"message": "No history found"}), 404



        @self.app.route('/dashboard', methods=['GET'])
        @login_required
        def Dashboard():
            """
            Redirection to Dashboard page to create Reports and Dashboards.
            ---
            tags:
              - name: Dashboard
            summary: Dashboard display page
            description: > 
              Displays the dashboard page (GET).  
              If credentials are valid, the user is redirected to the dashboard page.  
              If authentication fails, the login page is displayed.
            produces:
              - text/html
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Dashboard page displayed.
                schema:
                  type: string
                  description: HTML Dashboard Page
              302:
                description: Redirect to the Dashboard page on successful authentication.
                headers:
                  Location:
                    description: URL of the Dashboard page
                    schema:
                      type: string
                      example: /dashboard
              401:
                description: Invalid Credentials - login page displayed.
            """
            return render_template('dashboard.html')
            


        @self.app.route('/refresh_dashboard', methods=['POST'])
        @login_required
        def refresh_dashboard():
            """
            Refresh the dashboard displayed
            ---
            tags:
              - name: Dashboard
            summary: Display Dashboard
            description: > 
              Refresh the dashboard
              POST: Refresh the dashboard by sending the query to get the report
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                required: true
                description: >
                  Format of json entry:
                  startTime (default time : 01-01-1970 00:00:00) -> str : Datetime of query start
                  endTime (default time: 01-01-2500 00:00:00) -> str : Datetime of query end
                  index -> array : list of indices to search data
                  page_id -> str : unique id of the page request to retrieve data later
                  query -> str : request command for the search
                  technology (default []) -> array : list of technologies to limit the scope
                  tenant -> str : list of tenants where to perform the request
            responses:
              200:
                description:
                  Return the json dashboard result to display it in the screen
                schema:
                  type: object
            """
            try:
                #TODO add other error message 401 unauthorised and page not found,... 
                data = request.json
                print(f"Received refresh data: {data}")  # For debugging
                # dashboard_name = request.json["dashboard"]
                #TODO change the system dashboard list is not adapted (problem permissions for several user)
                # if dashboard_name in self.dashboard_list:
                dashboard = data.get("dashboard")
                if dashboard:
                    query_payload = {
                        "query": f"!search type:dashboard and name:{dashboard}",
                        "startTime": data.get("startDate",None),
                        "endTime": data.get("endDate", None),
                        "index": [data.get("indices")],
                        "tenant": [data.get("tenants")],
                        "technology": [data.get("technologies")],
                        "page_id": data.get("page_id")
                    }
                    answer = json.loads(self.query(query_payload))
                    print("Received : " + str(answer) + " " + str(type(answer)))
                    return jsonify(answer.get("data",[""])[0]), 200
                # return render_template('dashboard.html', data=None)
                return "{}"
            except:
                # return render_template('dashboard.html', data=None)
                return "{}"

        @self.app.route('/query', methods=['POST'])
        @login_required
        def query():   
            """
            Query the SIEM to retrieve table, graphs, ...
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Management
            description: > 
              Query the SIEM to retrieve table, graphs, ...
              GET: Return the data in json format
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                required: true
                description: >
                  Format of json entry:
                  startTime (default time : 01-01-1970 00:00:00) -> str : Datetime of query start
                  endTime (default time: 01-01-2500 00:00:00) -> str : Datetime of query end
                  index -> array : list of indices to search data
                  page_id -> str : unique id of the page request to retrieve data later
                  query -> str : request command for the search
                  technology (default []) -> array : list of technologies to limit the scope
                  tenant -> str : list of tenants where to perform the request
            responses:
              200:
                description:
                  Return the json data of type table
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            # TODO change this part to dispatch the queries, parallelism
            # wr = WebRequester("webhook", "my_secure_token", "192.168.178.38", "5400")
            # ims = self.get_indexsearchmotors()
            # TODO change this part with configuration file valreques

            # wr = WebRequester("webhook", ims[0]["auth_token"], ims[0]["host"], ims[0]["port"])
            try:
                data = request.get_json()
                # data["session_token"] = session.get("user_id")
                # current_id = json.loads(session.get("user_id")).get("username") + "_" + str(data["page_id"])
                # data["current_id"] = current_id
                start_time_query = time.time()
                # results = self.indexsearchmotorsReq.query_data(data)
                results = self.query(data)
                print("Time taken to query: ", time.time() - start_time_query)
                if results:
                    return results
                else:
                    return []
            except:
                print(f"Error in query:{traceback.format_exc()}")
                return []
            
            
        @self.app.route('/get_page', methods=['POST'])
        @login_required
        def get_page():
            """
            In case of result of type table, get the page of x pages, and which page
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Management
            description: > 
              In case of result of type table, get the page of x pages, and which page
              GET: Return the page required of the table data
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                required: true
                description: >
                  Format of json entry:
                    session_token -> str : authentication token,
                    action -> str : first, last, previous, next, ... , 
                    current_page -> integer : number of current page
                    items_per_page -> integer : number of page per page
                    current_id (default : main) -> str : unique id of the web page associated to the user and page
                    retry (default: 5) -> integer : retry amount for the request
            responses:
              200:
                description:
                  Return the json data of type table
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            # TODO change this part to dispatch the queries, parallelism
            # ims = self.get_indexsearchmotors()
            # wr = WebRequester("webhook", ims[0]["auth_token"], ims[0]["host"], ims[0]["port"])
            try:
                print("Get page:" + str(request.get_json()))
                data = request.get_json()
                if "current_id" not in data:
                    # data["current_id"] = json.loads(session.get("user_id")).get("username") + "_" + str(data["page_id"])
                    data["current_id"] = utils.create_current_id(json.loads(session.get("user_id")).get("username"), str(data["page_id"]))
                results = self.indexsearchmotorsReq.get_page(session.get("user_id"), data["action"],data["currentPage"], data["itemsPerPage"], data["current_id"])
                if results:
                    print("RESULTS", str(results))
                    return results
                else:
                    return {"type": "table", "data": [], "fields": []}
            except:
                print(f"Error in get_page:{traceback.format_exc()}")
                return {"type": "table", "data": [], "fields": []}
            

        @self.app.route('/query_help')
        @login_required
        def query_help():
            """
            Request the SIEM to get the help on the query commands
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Management
            description: > 
              Request to the SIEM to get help page about the siem commands
              GET: Get with referer url the available search help page
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the json with details of the commands availables
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            # Detect the page with the header HTTP "Referer"
            referer_url = request.referrer
            # Determine the context based on the referer URL
            if referer_url is None:
                context = "general"
            elif "/edition" in referer_url:
                context = "edition_help"
            elif "/search" in referer_url:
                try:
                    # Clean the break lines
                    context = self.indexsearchmotorsReq.get_help()
                    context = context.replace("\\n", "").replace("\\\"", '"')
                    print(context)
                except:
                    self.logger.log("error", f"Error in get_help:{traceback.format_exc()}")
                    context = "<p>No help available for this page.</p>"
            elif "/dashboard" in referer_url:
                context = "dashboard_help"
            elif "/configuration" in referer_url:
                return render_template('help_configuration.html')
            elif "/soar" in referer_url:
                context = self.soarsReq.get_help()
                context = context.replace("\\n", "").replace("\\\"", '"')
            else:
                context = "general_help"
            # Display the template related to the right context
            return render_template('query_help.html', context=context)



        @self.app.route('/get_suggestions')
        # TODO no need to check permissions for this page
        @login_required
        def get_suggestions():
            """
            Launch a command on the SOAR to get the suggestions based on the beginning of the query
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Management
            description: > 
              Request to the SIEM to get the suggestions based on the beginning of the query
              GET: Get the available search with parameters and details based on the beginning of the query
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: q
                in: query
                type: string
                required: true
                description: >
                  q for query, this is the start of the query to complete with suggestions
            responses:
              200:
                description:
                  Return the json with details of the commands availables
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            try:
                query = request.args.get('q', '').lower()
                if query:
                    # TODO change this part
                    # ims = self.get_indexsearchmotors()
                    # wr = WebRequester("webhook", ims[0]["auth_token"], ims[0]["host"], ims[0]["port"])
                    # wr = WebRequester("webhook", "my_secure_token", "192.168.178.38", "5400")
                    suggestions_db = json.loads(self.indexsearchmotorsReq.get_suggestions())
                    # TODO propose suggestions even in the middle of the request. Here only the start proposes something
                    matched_suggestions = [s for s in suggestions_db if query in s.lower()]
                    return jsonify({'suggestions': matched_suggestions})
            except:
                return jsonify({'suggestions': []})
            

        # TODO factorise this function with get_suggestions    
        @self.app.route('/command_suggestions')
        @login_required
        def command_suggestions():
            """
            Launch a command on the SOAR to get the suggestions based on the beginning of the query
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Launch a command on the SOAR to get the suggestions based on the beginning of the query
              GET: Get the available soar command with parameters and details based on the beginning of the query
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: q
                in: query
                type: string
                required: true
                description: >
                  q for query, this is the start of the query to complete with suggestions
            responses:
              200:
                description:
                  Return the json with details of the commands availables
                schema:
                  type: object
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            print("in command suggestions")
            try:
                # print("Suggestions query", str(query))
                query = request.args.get('q', '')
                print("Suggestions:", str(query), str("."))
                suggestions_db = json.loads(self.soarsReq.get_commands_suggestions(query))
                print("Suggestions:", str(suggestions_db))
                return jsonify({'suggestions': suggestions_db})
            except:
                print(f"Error in command_suggestions:{traceback.format_exc()}")
                return jsonify({'suggestions': []})


        @self.app.route('/search_available_index', methods=["GET"])
        @login_required
        def search_available_index():
            """
            Launch a command on the SOAR to get the instances of indices available for the user
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Launch a command to search all available indices for the user
              GET: Get the available indices for the user
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the list of available indices
                schema:
                  type: array
                  items:
                    type: string
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            referer_url = request.referrer
            print("referrer_url:",referer_url)
            # In case of dashboard and edition (use only dedicated index)
            if "/dashboard" in referer_url or "/edition" in referer_url or "/soar" in referer_url:
                print("index :", str(self.reporting_index))
                return self.reporting_index
            # Others requirements (search)
            res = self.indexsearchmotorsReq.get_available_indices(session.get("user_id"))
            if res:
                return json.loads(res)
            return None


        @self.app.route('/search_available_tenant', methods=["GET"])
        @login_required
        def search_available_tenant():
            """
            Launch a command on the SOAR to get the instances of tenants available for the user
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Launch a command to search all available tenants for the user
              GET: Get the available tenants for the user
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the list of available tenants
                schema:
                  type: array
                  items:
                    type: string
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            res = self.indexsearchmotorsReq.get_available_tenants(session.get("user_id"))
            if res:
                return json.loads(res)
            return None


        @self.app.route('/search_available_technologies', methods=["GET"])
        @login_required
        def search_available_technologies():
            """
            Launch a command on the SOAR to get the instances of technologies available for the user
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Launch a command to search all available technologies for the user
              GET: Get the available technologies for the user
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the list of available technologies
                schema:
                  type: array
                  items:
                    type: string
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            res = self.indexsearchmotorsReq.get_available_technologies(session.get("user_id"))
            if res:
                return json.loads(res)
            return None
        
        
        @self.app.route('/search_available_vault_instances', methods=["GET"])
        @login_required
        def search_available_vault():
            """
            Launch a command on the SOAR to get the instances of vault available for the user
            ---
            tags:
              - name: SOAR
            summary: Security Orchestration and Automation Response
            description: > 
              Launch a command to search all available vault instance for the user
              GET: Get the available vault for the user
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the list of available vault
                schema:
                  type: array
                  items:
                    type: string
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            res = self.soarsReq.get_available_vault_instances(session.get("user_id"))
            if res:
                return json.loads(res)
            return None


        @self.app.route('/configuration', methods=['GET', 'POST'])
        @login_required
        def Configuration():
            """
            Redirection to configuration page to configure permissions, user preferences and global configuration.
            ---
            tags:
              - name: Configuration
            summary: Configuration to the application page.
            description: > 
              Displays the Edition page (GET).  
              GET : Displays the configuration (Edition) page, loading data depending on the "option" query parameter.  
              POST : Saves configuration data based on the "option" query parameter and returns a JSON result.
            produces:
              - text/html
              - application/json
            consumes:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: option
                in: query
                type: string
                required: false
                description: >
                  Configuration category to read or modify.
                  Possible values: uiconfiguration, globalconfiguration, globalauthorisation.
                  Default: uiconfiguration.
              - name: body
                in: query
                required: false
                description: JSON configuration data sent during POST operations.
                schema:
                  type: object
            responses:
              200:
                description: >
                  GET → HTML configuration page returned.  
                  POST → JSON success response.
                schema:
                  type: string
              302:
                description: Redirect to configuration page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /configuration
              400:
                description: Invalid request or processing error (POST or GET).
              401:
                description: Unauthorized access — user not authenticated.
            """
            # TODO separe the POST and GET in two functions to have tags redirection and configuration splitted
            # POST request
            if request.method == 'POST':
                try:
                    selected_option = request.args.get('option', 'uiconfiguration')
                    data = request.json
                    print("OPTION:", str(selected_option))
                    # TODO test this part
                    self.write_json(selected_option, data)  # Ensure this function manage correctly the file depending on option
                    return jsonify({"status": "success"})
                except Exception as e:
                    return jsonify({"status": "error", "message": str(e)}), 400
            # GET request
            try:
                # Get option of url (bydefault : "uiconfiguration")
                selected_option = request.args.get('option', 'uiconfiguration')
                # Read the data depending on selected option
                if selected_option == 'globalconfiguration':
                    data = self.read_json("globalconfiguration")
                elif selected_option == 'globalauthorisation':
                    data = self.read_json("globalauthorisation")
                else:  # by default : 'uiconfiguration'
                    data = self.read_json('')
                return render_template('configuration.html', json_data=json.dumps(data), selected_option=selected_option)
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400


        @self.app.route('/static/<path:path>')
        @login_required
        def send_static(path):
            return send_from_directory('static', path)



        @self.app.route('/search', methods=['OPTIONS', 'GET', 'POST'])
        @login_required
        def Search():
            """
            Launch a command on the SIEM to get the results of your search in specified format.
            ---
            tags:
              - name: SIEM
            summary: Security Information and Event Management.
            description: > 
              Launch a command to search in the data of the SIEM.
              GET: Get the page to launch a research.
              POST : Post the search request and return the results in json format that will be interpreted and display on the web page. 
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: data
                in: query
                type: object
                required: true
                description: >
                  Data is a json that contains several keys
            responses:
              200:
                description:
                  Return the context in json.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            # TODO check if the POST /search is used
            try:
                if request.method == 'OPTIONS':
                    response = make_response()
                    response.headers["Access-Control-Allow-Origin"] = "*"
                    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
                    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
                    return response, 204  # No Content response to OPTIONS request

                if request.method == 'GET':
                    # TODO change this part to get the master primary or secondary
                    # mc = self.get_mastercoordinators()
                    return render_template('search_view.html', self.indexsearchmotorsReq["host"], self.indexsearchmotorsReq["port"], self.indexsearchmotors["auth_token"])

                if request.method == 'POST':
                    # Example to treat the researches
                    data = request.get_json()
                    return jsonify({"result": f"You searched for : {data['handle_search_data']}"})
            except:
                return render_template('search_view.html')


        @self.app.route("/menu")
        @login_required
        def Menu():
            """
            Load the menu page on the sidebar.
            ---
            tags:
              - name: Redirection
            summary: Redirection to menu page.
            description: > 
              Displays the menu page (GET).  
              If credentials are valid, the user is redirected to the menu page.  
              If authentication fails, the login page is displayed.
            produces:
              - text/html
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - Menu page displayed.
                schema:
                  type: string
                  description: HTML Menu Page
              302:
                description: Redirect to the Menu page on successful authentication.
                headers:
                  Location:
                    description: URL of the Menu page
                    schema:
                      type: string
                      example: /menu
              401:
                description: Invalid Credentials - login page displayed.
            """
            return render_template("menu.html", show_soar=True if self.soars_id else False)
        

        @self.app.route("/soar")
        @login_required
        def Soar():
            """
            Load the SOAR page
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Displays the soar page (GET).  
              If credentials are valid, the user is redirected to the soar page.  
              If authentication fails, the login page is displayed.
            produces:
              - text/html
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - SOAR page displayed.
                schema:
                  type: string
                  description: HTML SOAR Page
              302:
                description: Redirect to the SOAR page on successful authentication.
                headers:
                  Location:
                    description: URL of the SOAR page
                    schema:
                      type: string
                      example: /soar
              401:
                description: Invalid Credentials - login page displayed.
            """
            return render_template("soar.html")
    
        
        @self.app.route("/soar_load_history", methods=["POST"])
        @login_required
        def SoarLoadHistory():
            """
            Launch a command in the soar to load the history of commands related to the name given in parameters
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Launch a command in the soar to load the history of commands related to the name given in parameters.
              POST : Post the command in the SOAR to load the historic of commands and results based on parameters in entry.
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: filter
                in: query
                type: object
                required: false
                description: >
                  Filter of the history
            responses:
              200:
                description:
                  Return the context in json.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            # TODO verify if this function is still used somewhere
            try:
                data = request.get_json()
                res = self.soarsReq.soar_load_history(session.get("user_id"), data.get("filter", {}))
                if res:
                    return json.loads(res)
                return []
            except:
                return []
            

        @self.app.route("/soar_load_variables", methods=["POST"])
        @login_required
        def SoarLoadVariables():
            """
            Launch a command in the soar to load the variables in the context
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Launch a command in the soar to load the variables in the context.
              POST : Post the command in the SOAR to load the variables of the context.
            produces:
              - application/json
            security:
              - SessionAuth: []
            responses:
              200:
                description:
                  Return the context in json.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            try:
                # TODO verify if this function is still used somewhere
                # TODO if not parameters why POST, should be GET
                data = request.get_json()
                res = self.soarsReq.soar_load_variables(session.get("user_id"))
                if res:
                    return json.loads(res)
                return {}
            except:
                return {}

        @self.app.route("/soar_erase_history", methods=["POST"])
        @login_required
        def SoarEraseHistory():
            """
            Launch a command in the soar to erase the history of commands and results.
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Launch a command in the SOAR to erase all or a part of the history of commands.
              POST : Post the command in the SOAR to erase all or a part of the history of commands and results.
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: filter
                in: query
                type: object
                required: false
                description: >
                  filter (specific id for example) to erase. Erase all or only the filter.
            responses:
              200:
                description:
                  Return the context updated in json.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            try:
                data = request.get_json()
                res = self.soarsReq.soar_erase_history(session.get("user_id"), filter=data.get("filter", {}))
                if res:
                    return json.loads(res)
                return []
            except:
                return []


        @self.app.route("/soar_replace_id", methods=["POST"])
        @login_required
        def SoarReplaceId():
            """
            Launch a command in the soar to replace the id
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Launch a command in the SOAR to swap an id with another one.
              POST : Post the command in the SOAR to swap the ids (origin to final).
            produces:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: origin
                in: query
                type: string
                required: true
                description: >
                  Original id to replace by the final. 
              - name: final
                in: query
                type: string
                required: true
                description: >
                  new id for the original.
            responses:
              200:
                description:
                  Return the context in json.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            try:
                data = request.get_json()
                res = self.soarsReq.soar_replace_id(session.get("user_id"), data.get("origin"), data.get("final"))
                if res:
                    return json.loads(res)
                return []
            except:
                return []

        @self.app.route("/soar_command", methods=["POST"])
        @login_required
        def SoarCommand():
            """
            Launch a command in the soar for the context in parameters.
            ---
            tags:
              - name: SOAR
            summary: security orchestration and automation response
            description: > 
              Launch a command in the SOAR.  
              POST : Post the command in the SOAR.
            produces:
              - text/html
              - application/json
            consumes:
              - application/json
            security:
              - SessionAuth: []
            parameters:
              - name: command
                in: query
                type: string
                required: true
                description: >
                  Command to launch in the SOAR. The command must exists in the SOAR and respect parameters.
              - name: id
                in: query
                type: string
                required: true
                description: >
                  Id of the command, if the command exists the result will be modified else, a new command will be created. -1 by default.
              - name: playbook_mode
                in: query
                type: boolean
                required: true
                description: >
                  If the command is added in the context or the playbook. If playbook, the command is not executed but added in the historic of commands.
              - name: index
                in: query
                type: string
                required: true
                description: >
                  Index where to find the context or the playbook.
              - name: tenant
                in: query
                type: string
                required: true
                description: >
                  Tenant where to find the context or the playbook.
              - name: vault
                in: query
                type: string
                required: true
                description: >
                  The instance name of the vault to get credentials to run the command with rights permissions.
              - name: history
                in: query
                type: string
                required: true
                description: >
                  Name of the context or the playbook in the index, tenant where to add the command.
              - name: display
                in: query
                type: boolean
                required: true
                description: >
                  If the command should be added in the history or only executed.
            responses:
              200:
                description:
                  POST → JSON success response.
                schema:
                  type: object
              302:
                description: If user not connected, redirect to the authentication page.
                headers:
                  Location:
                    description: URL of the configuration page
                    schema:
                      type: string
                      example: /soar
              400:
                description: Invalid request or processing error POST.
              401:
                description: Unauthorized access — user not authenticated.
            """
            try:
                #TODO must check the user session and the permission
                data = request.get_json()
                print("SUBMIT SOAR COMMAND:", str(data))
                res = self.soarsReq.soar_command(session.get("user_id"), 
                                                data.get("command"), 
                                                data.get("id", None), 
                                                data.get("playbook_mode", False), 
                                                data.get("index", None), 
                                                data.get("tenant", None),
                                                data.get("vault", None),
                                                data.get("history", None),
                                                data.get("display", True)
                )
                if res:
                    return json.loads(res)
                return None
            except:
                return None

        @self.app.route("/report_list", methods=["GET"])
        @login_required
        def report_list():
            """
            List all reports for users
            ---
            tags:
              - Reports
            summary: Return list of reports
            description: Require the authentication of the user
            security:
              - SessionAuth: []
            responses:
              200:
                description: Success - list of reports
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                      example: OK
                    reports:
                      type: array
                      items:
                        type: string
                        example: Monthly report
              401:
                description: Not authorized - user not connected
            """
            # TODO: Complete this function
            user_id = json.loads(session.get("user_id")).get("id")
            data = {
                'query': {
                    'query': '!search type:report',
                    'startTime': None,
                    'endTime': None,
                    'index': [self.reporting_index],
                    'tenant': [user_id]
                },
                'format': 'pdf'
            }
            return self.query(data)



        @self.app.route("/docs/media/<path:filename>")
        def doc_media(filename):
            media_dir = Path(__file__).resolve().parent.parent / "docs" / "media"
            return send_from_directory(media_dir, filename)

        # === Documentation Markdown dynamic ===
        @self.app.route("/docs/")
        @self.app.route("/docs/<page>")
        def render_doc(page="index"):
            """
            Provide a page markdown from the folder /docs
            """
            print("render docs")
            md_path = Path(__file__).resolve().parent.parent / "docs" / f"{page}.md"
            print(md_path)
            if not md_path.exists():
                abort(404)

            print("after abort")
            # Read markdown content
            content = markdown.markdown(
                md_path.read_text(encoding="utf-8"),
                extensions=["fenced_code", "tables", "toc"]
            )

            # Template HTML simple and modern
            html_template = """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Documentation SIEM</title>
                <style>
                    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
                    pre { background: #f4f4f4; padding: 10px; border-radius: 6px; overflow-x: auto; }
                    code { background: #eee; padding: 2px 4px; border-radius: 4px; }
                    h1, h2, h3 { color: #333; }
                    a { color: #007bff; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    nav { background: #f8f9fa; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <nav>
                    <img src="/static/media/dbart.png" style="width:32px;" alt="DevBytesArt®"/>
                    <a href="/docs/index">Welcome</a> |
                    <a href="/docs/installation">Installation</a> |
                    <a href="/docs/tutorial">Tutorial</a> |
                    <a href="/apidocs/">API</a>
                </nav>
                {{ content|safe }}
            </body>
            </html>
            """
            return render_template_string(html_template, content=content)

# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session or ui.authenticatorsReq is None:
            return redirect(url_for('login'))
        else:
            token = json.loads(session.get("user_id"))
            print("TO  KEN: " + str(token) + str(type(token)))
            if json.loads(ui.authenticatorsReq.check_permissions(token.get("token"), ui.required_permissions)):
                return f(*args, **kwargs)
            else:
                return redirect(url_for('login'))
    return decorated_function


# TODO find a way to restart the service when the ui is changed
if __name__ == '__main__':
    # Initialize the UserInterface with the path to your JSON file
    config_loader = ConfigLoader()
    config_loader.parse_arguments()
    if config_loader.get_config():  
        print("CONFIG LOADER START OF THE SERVER")  
        ui = UserInterface("userinterfaceconfig.json", config_loader.get_config())
        ui.app.run(host="0.0.0.0", port=443, debug=False, use_reloader=False, ssl_context=('certs/server.crt', 'certs/server.key'))