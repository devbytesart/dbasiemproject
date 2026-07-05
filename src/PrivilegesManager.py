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
document: privileges manager
"""

import sqlite3, bcrypt, os, json, traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
import Utils as utils
import uuid
import jwt

DEFAULT_TOKEN_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class PrivilegesManager:
    def __init__(self, auth_id, storage_path, logger):
        self.auth_id = auth_id
        self.storage_base = storage_path
        self.storage_folder = Path(self.storage_base) / "Authentication"
        self.storage_path = self.storage_folder / "global_privileges.json"
        self.storage_path_users = self.storage_folder / "users.db"
        self.logger = logger
        self.secret = "secret"
        self.jwt_encryption_algorithm = "HS256"
        # TODO test if there any side effect with True for initialized
        self.initialized = False
        # TODO get the expiration date from the configuration file
        self.token_expiration = 3600
        # self.initialize_database()

    def initialize_global_privileges(self, data):
        if not os.path.exists(self.storage_path):
            utils.create_folders(self.storage_path)
            if data is None:
                # TODO use a json file to load this part
                # TODO limit permissions of admin roles, must bot be superadmin
                data = {"version" : 1,
                        "last_modification": datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT),
                        "infrastructure":{
                            "authenticators": [{
                                "id" : "&authenticator1",   
                                "resources": [
                                    {
                                        "id": "all", 
                                        "name": "all", 
                                        "type": "all",
                                        "description": "all resources" 
                                    },{
                                        "id":"userinterface", 
                                        "name": "userinterface", 
                                        "type": "service",
                                        "description": "access to the user interface when logged in"
                                    },{
                                        "id":"global_configuration", 
                                        "name":"global_configuration", 
                                        "type": "file",
                                        "description": "the global configuration provided by the master coordinator"
                                    }, {
                                        "id":"global_privileges", 
                                        "name":"global_privileges", 
                                        "type": "file",
                                        "description": "the global privileges provided by the master coordinator"
                                    }, {
                                        "id": "soar_index",
                                        "name": "soar", 
                                        "type": "index", 
                                        "description": "the index to store data from the soar (scheduler and soar)"
                                    }, {
                                        "id": "soar_tasks",
                                        "name": "soar_tasks",
                                        "type": "tenant", 
                                        "description": "the tenant by default used by the scheduler to schedule tasks on the SOAR"
                                    }, {
                                        "id": "techno_scheduler", 
                                        "name": "scheduler", 
                                        "type": "technology", 
                                        "description": "the technology by default used by the scheduler to store scheduled tasks in the SOAR"
                                    }
                                ],
                                "roles": [{
                                                "id": "superadmin", 
                                                "name": "superadmin", 
                                                "permissions": [{"id": "all", "read": True, "write": True}], 
                                                "inherit": []
                                           }, 
                                           {
                                               "id": "analyst", 
                                               "name": "analyst",
                                               "permissions": [{"id": "userinterface", "read": True, "write": False}],
                                               "inherit": []
                                           }, 
                                           {
                                               "id": "admin",
                                               "name": "admin",
                                               "permissions": [],
                                               "inherit": ["superadmin"]
                                           }, 
                                           {
                                               "id": "scheduler_role", 
                                               "name": "scheduler", 
                                               "permissions": [
                                                   {"id": "userinterface", "read": True, "write": False},
                                                   {"id": "soar_index", "read": True, "write": True},
                                                   {"id": "soar_tasks", "read": True, "write": True}, 
                                                   {"id": "techno_scheduler", "read": True, "write": True}
                                                   ],
                                               "inherit": []
                                           }],
                                "users": [{
                                                "id":"siem_system", 
                                                "name": "siem_system", 
                                                "email": "siem_system@local.local", 
                                                "roles": ["superadmin"]
                                            }, {
                                                "id": "scheduler", 
                                                "name": "scheduler", 
                                                "email": "soar_system@local.local", 
                                                "roles": ["scheduler_role"]
                                            } 
                                           ]
                            }]
                        }
                    }
            with open(self.storage_path, "w") as file:
                json.dump(data, file, indent=4)
        # Intialize the database
        self.initialized = True



    def initialize_database(self):
        try:
            if not os.path.exists(self.storage_path_users):
                self.initialized = False
                utils.create_folders(self.storage_path_users)
                conn = sqlite3.connect(self.storage_path_users)
                cursor = conn.cursor()

                # Table creation
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    inherit_roles TEXT DEFAULT '[]' -- List roles inherited on json form
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id TEXT PRIMARY KEY,
                    role_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    can_read BOOLEAN NOT NULL,
                    can_write BOOLEAN NOT NULL,
                    FOREIGN KEY (role_id) REFERENCES roles (id),
                    FOREIGN KEY (resource_id) REFERENCES resources (id)
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    password_hash TEXT,
                    email TEXT,
                    disabled BOOLEAN NOT NULL,
                    authentication_type TEXT NOT NULL,
                    session_token TEXT,
                    session_creation_date TEXT NOT NULL,
                    session_token_expired BOOLEAN,
                    number_of_failed_attempted INTEGER DEFAULT 0,
                    last_failed_attempted TEXT
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (role_id) REFERENCES roles (id),
                    UNIQUE (user_id, role_id) -- Avoid duplicata 
                )
                """)

                conn.commit()
                conn.close()
        except:
            self.logger.log("error", f"Error initializing privileges database {traceback.format_exc()}")
            if conn:
                conn.close()

    def insert_data(self, data):
        try:
            conn = sqlite3.connect(self.storage_path_users)
            cursor = conn.cursor()

            # Insert resources
            if "resources" in data:
                print("SAVE RESOURCES IN DATABASE")
                for resource in data.get("resources", []):
                    cursor.execute("""
                    INSERT OR REPLACE INTO resources (id, name, type, description)
                    VALUES (?, ?, ?, ?)
                    """, (resource.get("id"), resource.get("name"), resource.get("type"), resource.get("description")))

            # Insert roles
            if "roles" in data:
                print("SAVE ROLES IN DATABASE")
                for role in data.get("roles", []):
                    # Convert roles inherited in JSON
                    inherit_roles_json = json.dumps(role.get("inherit", []))
                    cursor.execute("""
                    INSERT OR REPLACE INTO roles (id, name, inherit_roles)
                    VALUES (?, ?, ?)
                    """, (role["id"], role["name"], inherit_roles_json))

                    # Insert permissions for each role
                    for perm in role.get("permissions", []):
                        cursor.execute("""
                        INSERT OR REPLACE INTO permissions (role_id, resource_id, can_read, can_write)
                        VALUES (?, ?, ?, ?)
                        """, (role["id"], perm["id"], perm["read"], perm["write"]))

            # Insert users
            if "users" in data:
                print("SAVE USERS IN DATABASE")
                for user in data.get("users", []):
                    user_id = user.get("id")
                    user_name = user.get("name")
                    if not user_id or not user_name:
                        self.logger.log("error", f"User ignored: ID or name missing for {user}")
                        continue

                    password = user.get("password", None)
                    password_hash = self.hash_password(password) if password else None

                try:
                    # Verify if user already exists 
                    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                    existing_user = cursor.fetchone()

                    if existing_user:
                        print("User already exists, updating...")
                        # Update existing users
                        update_fields = [
                            "name = ?",
                            "email = ?",
                            "disabled = ?",
                            "authentication_type = ?",
                            "session_token = ?",
                            "session_creation_date = ?",
                            "session_token_expired = ?",
                            "number_of_failed_attempted = ?",
                            "last_failed_attempted = ?"
                        ]
                        update_values = [
                            user_name,
                            user.get("email"),
                            user.get("disabled", False),
                            user.get("authentication_type", "local"),
                            user.get("session_token", None),
                            user.get("session_creation_date", datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT)),
                            user.get("session_token_expired", False),
                            user.get("number_of_failed_attempted", 0),
                            user.get("last_failed_attempted", None),
                        ]

                        # Update password only if provided
                        if password_hash:
                            update_fields.append("password_hash = ?")
                            update_values.append(password_hash)

                        # Add clause WHERE
                        update_values.append(user_id)

                        # Execute request of update
                        cursor.execute(f"""
                        UPDATE users
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                        """, update_values)
                    else:
                        print("User does not exist, inserting...")
                        # Insert new user
                        cursor.execute("""
                        INSERT INTO users (
                            id, name, password_hash, email, disabled, authentication_type,
                            session_token, session_creation_date, session_token_expired,
                            number_of_failed_attempted, last_failed_attempted
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id,
                            user_name,
                            password_hash,
                            user.get("email"),
                            user.get("disabled", False),
                            user.get("authentication_type", "local"),
                            user.get("session_token", None),
                            user.get("session_creation_date", datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT)),
                            user.get("session_token_expired", False),
                            user.get("number_of_failed_attempted", 0),
                            user.get("last_failed_attempted", None)
                        ))
                except Exception as e:
                    self.logger.log("error", f"Error during user insertion or update {user_name}: {e}")

                # Drop all roles for this user
                cursor.execute("""
                    DELETE FROM user_roles
                    WHERE user_id = ?
                    """, (user_id,))

                # Attribution of new roles for this user
                for role_id in user.get("roles", []):
                    cursor.execute("""
                    REPLACE INTO user_roles (user_id, role_id)
                    VALUES (?, ?)
                    """, (user_id, role_id))

            conn.commit()
        except Exception as e:
            self.logger.log("error", f"Error inserting data into database: {traceback.format_exc()}")
        finally:
            if conn:
                conn.close()


    # Function to translate database in JSON
    def database_to_json(self):
        try:
            conn = sqlite3.connect(self.storage_path_users)
            cursor = conn.cursor()

            # Get resources
            cursor.execute("SELECT id, name, type, description FROM resources")
            resources = [{"id": row[0], "name": row[1], "type": row[2], "description": row[3]} for row in cursor.fetchall()]

            # Get roles and permissions
            roles = []
            cursor.execute("SELECT id, name FROM roles")
            for role_id, role_name in cursor.fetchall():
                cursor.execute("""
                SELECT resource_id, can_read, can_write
                FROM permissions WHERE role_id = ?
                """, (role_id,))
                permissions = [
                    {"resource_id": row[0], "read": bool(row[1]), "write": bool(row[2])}
                    for row in cursor.fetchall()
                ]
                roles.append({"id": role_id, "name": role_name, "permissions": permissions})

            # Get users and roles
            users = []
            cursor.execute("SELECT id, name, email, disabled, authentication_type FROM users")
            for user_id, name, email, disabled, auth_type in cursor.fetchall():
                cursor.execute("""
                SELECT role_id FROM user_roles WHERE user_id = ?
                """, (user_id,))
                roles_ids = [row[0] for row in cursor.fetchall()]
                users.append({
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "disabled": bool(disabled),
                    "authentication_type": auth_type,
                    "roles": roles_ids
                })

            conn.close()

            # Build object final JSON
            data = {
                "resources": resources,
                "roles": roles,
                "users": users
            }
            return data
        except:
            self.logger.log("error", f"Error converting database to JSON {traceback.format_exc()}")
            if conn:
                conn.close()
            return None
        

    def get_user_permissions(self, username):
        try:
            print(f"Getting user permissions for: {username}")
            conn = sqlite3.connect(self.storage_path_users)
            cursor = conn.cursor()

            # Recursive function to get all inherited roles
            def get_inherited_roles(role_id, visited=None):
                if visited is None:
                    visited = set()
                if role_id in visited:
                    return []  # Avoid loops
                visited.add(role_id)

                cursor.execute("""
                SELECT inherit_roles
                FROM roles
                WHERE id = ?
                """, (role_id,))
                result = cursor.fetchone()

                if not result:
                    return []

                # Load inherited from JSON
                inherited_roles = json.loads(result[0]) if result[0] else []
                all_roles = inherited_roles[:]

                # Recursivity to get inherited roles of inherited roles
                for inherited_role in inherited_roles:
                    all_roles.extend(get_inherited_roles(inherited_role, visited))

                return list(set(all_roles))  # Delete duplicata

            # Get role associated to the user
            cursor.execute("""
            SELECT DISTINCT ur.role_id
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            WHERE u.name = ?
            """, (username,))
            user_roles = [row[0] for row in cursor.fetchall()]
            if not user_roles:
                print(f"No roles found for user: {username}")
                return []  # None role found for the user

            # Get all roles inherited
            all_roles = set(user_roles)
            for role in user_roles:
                all_roles.update(get_inherited_roles(role))

            print(f"All roles for user {username}: {all_roles}")

            # Split direct role and inherited
            inherited_roles = all_roles - set(user_roles)

            # Get permissions and roles directly attributed
            cursor.execute(f"""
            SELECT DISTINCT res.name AS resource_name,
                res.type AS resource_type,
                p.can_read, p.can_write
            FROM roles r
            JOIN permissions p ON r.id = p.role_id
            JOIN resources res ON p.resource_id = res.id
            WHERE r.id IN ({','.join('?' for _ in user_roles)})
            """, tuple(user_roles))
            direct_permissions = cursor.fetchall()

            print(f"Direct permissions for user {username}: {direct_permissions}")

            # Get permission of inherited roles
            cursor.execute(f"""
            SELECT DISTINCT res.name AS resource_name,
                res.type AS resource_type,
                p.can_read, p.can_write
            FROM roles r
            JOIN permissions p ON r.id = p.role_id
            JOIN resources res ON p.resource_id = res.id
            WHERE r.id IN ({','.join('?' for _ in inherited_roles)})
            """, tuple(inherited_roles))
            inherited_permissions = cursor.fetchall()

            print(f"Inherited permissions for user {username}: {inherited_permissions}")

            conn.close()

            # Convert results in JSON with resources type
            direct_permissions_json = [
                {"resource": row[0], "type": row[1], "read": bool(row[2]), "write": bool(row[3])}
                for row in direct_permissions
            ]
            inherited_permissions_json = [
                {"resource": row[0], "type": row[1], "read": bool(row[2]), "write": bool(row[3])}
                for row in inherited_permissions
            ]

            print("Permissions directes :", str(direct_permissions_json))
            print("Permissions héritées :", str(inherited_permissions_json))

            return direct_permissions_json + inherited_permissions_json

        except Exception as e:
            self.logger.log("error", f"Error getting user permissions {traceback.format_exc()}")
            if conn:
                conn.close()
            return []

    def hash_password(self, password):
        if not password:  # Verify if password is None
            return None
        if isinstance(password, bytes):  # Check if already in bytes
            password_bytes = password
        else:
            password_bytes = password.encode()  # Encode in bytes if not already and return the hash
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    def verify_password(self, password, hashed_password):
        """
        Verify if the password provided correspond to the hash password

        :param password: Plain text password to check
        :param hashed_password: Hashed password for comparison
        :return: True if password corresponds else if not
        """
        if not password or not hashed_password:
            return False
        if isinstance(password, bytes):
            password_bytes = password
        else:
            password_bytes = password.encode()  # Encode in bytes if required
        # Verify password with the hash
        return bcrypt.checkpw(password_bytes, hashed_password)
    

    def handle_get_local_privileges(self, request):
        #TODO finish this function 
        try:
            if not self.initialized:
                return self.database_to_json()
            else:
                print(self.get_user_permissions_by_token(request.get("session_token")))
        except:
            self.logger.log("error", f"Error handling get local privileges {traceback.format_exc()}")
            return None

    def backup_global_privileges(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path) as file:
                    privileges = json.loads(file.read())
            if privileges:
                version = privileges.get("version")  
                copy_path = os.path.join(self.storage_base, "backup_privileges", f"privileges_backup_{version}.json")
                utils.create_folders(copy_path)
                with open(copy_path, "w") as file:
                    json.dump(privileges, file, indent=4)
            return True
        except:
            self.logger.log("error", f"Error handling backup global privileges {traceback.format_exc()}")
            return False

    def handle_set_local_privileges(self, request):
        try:
            print("PRIVILEGE MANAGER REQUEST: " + str(request))
            if not self.initialized:
                self.insert_data(request.get("privileges"))
                # self.initialized = True
            else:
                #TODO finish this function
                token = request.get("token")
                configuration = request.get("privileges")
                if self.initialized:
                    # TODO check token permissions (think about the first initialization that must not require token)
                    pass
                self.insert_data(configuration)
        except:
            self.logger.log("error", f"Error handling set local privileges {traceback.format_exc()}")
            return None
        
    def handle_set_global_privileges(self, request):
        #TODO validate the configuration 
        #TODO add encryption of the file
        #TODO check the token for the right to get the global privileges
        try:
            # TODO check the token for the right to get the global privileges
            # TODO add encryption of the file
            # Save backup of the current privileges
            self.backup_global_privileges()
            # Change version
            privileges = request.get("privileges")
            privileges["version"] = privileges.get("version", 1) + 1
            privileges["last_modification"] = datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT)
            with open(self.storage_path, "w") as file:
                json.dump(privileges, file, indent=4)
            return True
        except:
            self.logger.log("error", f"Error handling set global privileges {traceback.format_exc()}")
            return False

    def get_global_privileges(self, scope="all"):
        """ Get directly the global privileges from the file """
        with open(self.storage_path, "r") as file:
            data = json.loads(file.read())
            # If scope is all, return the whole file
            if scope == "all":
                return data
            # Search for a specific id for the authenticator
            for authenticator in data.get("infrastructure", {}).get("authenticators", []):
                if authenticator.get("id") == f"&{scope}":
                    return authenticator
            # If no authenticator is found, return None
            return None

    def handle_get_global_privileges(self, request):
        try:
            print("IN PRIVILEGE MANAGER REQUEST GET GLOBAL PRIVILEGES")
            # TODO check the token for the right to get the global privileges
            # TODO add encryption of the file
            return self.get_global_privileges()
        except:
            self.logger.log("error", f"Error handling set global privileges {traceback.format_exc()}")
            return None

    def handle_sign_out(self, request):
        try:
            # TODO implement this function
            pass
        except:
            self.logger.log("error", f"Error handling sign out {traceback.format_exc()}")
            return None

    def handle_sign_up(self, request):
        try:
            username = request.get("username")
            password = request.get("password")
            email = request.get("email")
            authentication = request.get("authentication", "local")
            if password is None or username is None:
                return False
            # 1. Connect to the database to check if the user already exists
            conn = sqlite3.connect(self.storage_path_users)
            cursor = conn.cursor()
            # Check if the username is ALREADY taken (regardless of the password)
            results = cursor.execute("SELECT * FROM users WHERE name = ?", (username,)).fetchall()
            conn.close() # Close the connection to prevent SQLite locks
            # 2. If the user already exists, stop the execution immediately
            if len(results) > 0:
                self.logger.log("info", f"Sign up attempted with existing username: {username}")
                return False
            # 3. If the user does not exist, proceed with registration
            if self.initialized:
                print("IN SELF INITIALIZED")
                # TODO: You should use self.hash_password(password) here for security!
                data = {"users": [{"id": username, "name": username, "password": password, "email": email, "authentication": authentication}]}
                self.insert_data(data)
                self.logger.log("info", f"Sign up performed with username {username}")
                return True
            else:
                print("IN SELF NOT INITIALIZED FIRST INITIALIZATION")
                # First user -> Becomes superadmin
                data = {"users": [{"id": username, "name": username, "password": password, "email": email, "authentication": authentication, "roles":["superadmin"]}]}  
                self.insert_data(data)
                self.logger.log("info", f"Sign up first user performed with username {username}")
                # Switch initialization state to True to prevent future first-time setups
                self.initialized = True
                self.logger.log("info", f"Users database initialized")
                return True
        except Exception as e:
            self.logger.log("error", f"Error handling sign up user: {traceback.format_exc()}")
            return False


    def handle_sign_in(self, request):
        try:
            # TODO check the duplicata of token creation with the function create_token
            # TODO erase the print password ...
            print("IN PRIVILEGE MANAGER REQUEST SIGN IN:", str(request))
            username = request.get("username")
            password = request.get("password")
            # password_hash = self.hash_password(password)
            # TODO erase session token from the database (useless)
            session_token = uuid.uuid4().hex
            # print("session_token: ", session_token)
            try:
                conn = sqlite3.connect(self.storage_path_users)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE name = ? AND disabled = 0", (username, ))
                results = cursor.fetchone()
                print("results: ", str(results))
                if results:
                    # if password hash or user disabled return None 
                    if results[2] is None or results[4]:
                        self.logger.log("error", f"Error sign_in user disabled or password empty : {traceback.format_exc()}")
                        return None
                    # Check if password matches
                    if not self.verify_password(password, results[2]):
                        self.logger.log("error", f"Error sign_in password does not match : {traceback.format_exc()}")
                        return None
                    # Insert the new token session in the database,
                    cursor.execute("""
                    UPDATE users
                    SET 
                        session_token = ?, 
                        session_creation_date = ?, 
                        session_token_expired = ?, 
                        number_of_failed_attempted = 0
                    WHERE name = ?;
                    """, (session_token, datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT), 0, username))
                    conn.commit()
                else:
                    self.logger.log("warning", f"Failed logon attempt for user {username} {traceback.format_exc()}")
                    # Insert the failed logon attempt in the database and block when the max is reached
                    conn.rollback()
                    cursor.execute("UPDATE users SET number_of_failed_attempted = number_of_failed_attempted + 1, last_failed_attempted = datetime('now') WHERE name = ?;", (username,))
                    # TODO finish the request to increase the logon attempts in the database
                    conn.commit()
                    return None
            except:
                self.logger.log("error", f"Error handling authenticate user {traceback.format_exc()}")
                return None
            return self.create_token(username)
        except:
            self.logger.log("error", f"Error handling authenticate user {traceback.format_exc()}")
            return None

    def handle_check_username(self, data): 
        """ Check that the username is the same as the token one"""
        try:
            token = data.get("session_token")
            # TODO identify why there is once the token complete and the other request only the token encrypted with only one call from the indexsearchmotor
            try: # does not work without this
                token = json.loads(token)
                token = token.get("token")
            except:
                pass
            username = data.get("username")
            print("TOKEN: ", str(token), ":", str(type(token)))
            token_data = self.decode_token(token)
            token_data_username = token_data.get("username")
            if token_data_username == username:
                self.logger.log("info", f"Check username: username {username} and token username {token_data_username} are the same")
                return True
            self.logger.log("warning", f"Check username: username {username} and token username {token_data_username} are not the same")
            return False
        except:
            self.logger.log("error", f"Error handling verify user {traceback.format_exc()}")
            return False

    def handle_change_password(self, request):
        """ Return True if the password was successfully updated, False otherwise """
        try:
            # Decode the request parameters
            try: # does not work without this
                token = json.loads(request.get("session_token"))
                token = token.get("token")
            except:
                return False
            username = request.get("username")
            new_password = request.get("new_password")
            if not username or not new_password:
                self.logger.log("warning", "Change password failed: Missing username or new_password")
                return False
            # Decode the provided session token
            token_data = self.decode_token(token)
            if token_data is None:
                self.logger.log("error", f"Error decoding token {traceback.format_exc()}")
                return False
            # Check if the token username matches the request username and if the token is not expired
            print("token_data: ", str(token_data))
            if (
                token_data.get("username") == username and
                datetime.strptime(token_data.get("expiration"), DEFAULT_TOKEN_DATE_FORMAT).replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
            ):
                # 1. Generate the password hash using your class method
                password_hash = self.hash_password(new_password)

                # 2. Connect and update only the password_hash field
                conn = sqlite3.connect(self.storage_path_users)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE users 
                    SET password_hash = ? 
                    WHERE id = ?
                """, (password_hash, username))

                conn.commit()
                conn.close()

                self.logger.log("info", f"User {username} successfully changed their password")
                return True
            else:
                self.logger.log("warning", f"User {token_data.get('username')} unauthorized or token expired to change password for {username}")
                return False
        except:
            self.logger.log("error", f"Error changing password {traceback.format_exc()}")
            return False

    def handle_check_permissions(self, request):
        """ Return True if the user has the required permissions, False otherwise """
        try:
            # Decode the request
            token = request.get("session_token")
            permissions_required = request.get("permissions_required")
            # read = request.get("read") # By default true in the request
            # write = request.get("write") # By default false in the request, true authorized read and write
            # Decode the token
            token_data = self.decode_token(token)
            if token_data is None:
                self.logger.log("error", f"Error decoding token {traceback.format_exc()}")
                return False
            # Check if the user has the required permissions
            print("token_data: ", str(token_data))
            print("permissions_required:", str(permissions_required))
            if (
                len(token_data.get("permissions", [])) > 0 and
                all(
                    any(
                        (perm["resource"] == req["resource"] or perm["resource"] == "all") and
                        (perm["type"] == req["type"] or perm["type"] == "all") and 
                        perm["read"] >= req.get("read", False) and
                        perm["write"] >= req.get("write", False)
                        for perm in token_data["permissions"]
                    )
                    for req in permissions_required
                ) and
                datetime.strptime(token_data.get("expiration"), DEFAULT_TOKEN_DATE_FORMAT).replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
            ):
                # TODO must check the read or write permissions
                self.logger.log("info", f"User {token_data.get('username')} has the required permissions {permissions_required}")
                return True
            else:
                self.logger.log("warning", f"User {token_data.get('username')} does not have the required permissions {permissions_required}")
                return False
        except:
            self.logger.log("error", f"Error checking permissions {traceback.format_exc()}")
            return False
        
    def create_token(self, username):
        """ Create a token with the username of the user """
        try:
            # Create a token with the username of the user
            permissions = self.get_user_permissions(username)
            # Get information from the token for the expiration date
            conn = sqlite3.connect(self.storage_path_users)
            cursor = conn.cursor()
            cursor.execute("SELECT session_creation_date FROM users WHERE name = ?", (username, ))
            results = cursor.fetchone()
            # if results:
            #     token_expiration_date = (datetime(results[0]).strptime(DEFAULT_TOKEN_DATE_FORMAT) + timedelta(seconds=self.token_expiration)).strftime(DEFAULT_TOKEN_DATE_FORMAT)
            # else:
            #     token_expiration_date = datetime.now().strftime(DEFAULT_TOKEN_DATE_FORMAT)
            if results:
                print("results[0]: ", results[0])
                # Parse date from results[0]
                token_expiration_date = (
                    datetime.strptime(results[0], DEFAULT_TOKEN_DATE_FORMAT) +
                    timedelta(seconds=self.token_expiration)
                ).strftime(DEFAULT_TOKEN_DATE_FORMAT)
            else:
                print("results[0] is None")
                token_expiration_date = datetime.now(timezone.utc).strftime(DEFAULT_TOKEN_DATE_FORMAT)
            # Update the database with the new token information
            jwt_token = jwt.encode({"username": username, "id":username, "expiration": token_expiration_date, "permissions": permissions}, self.secret, algorithm=self.jwt_encryption_algorithm)
            # TODO change the id by an unique id
            token = {"authenticator": self.auth_id, "token": jwt_token, "username": username, "id": username}
            return token
        except:
            self.logger.log("error", f"Error creating token {traceback.format_exc()}")
            return None
        
    def decode_token(self, token):
        """ Decode a token in clear json data """
        try:
            if token is not None:
                # Decode the token
                token_data = jwt.decode(token, self.secret, algorithms=[self.jwt_encryption_algorithm])
                return token_data
        except:
            self.logger.log("error", f"Error decoding token {traceback.format_exc()}")
            return None
    