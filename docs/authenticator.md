<!-- 
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
project: siem project
DOCUMENT: authenticator doc
-->

# Authenticator

Authenticator will verify the permissions of the users and grant access to pages and features of the application.

Several authenticator can be used by the application, however, the userinterface, SOAR and SIEM must be connected to only one. 

If several authenticators are required for different locations in the infrastructure (for example, Active Directory instances for multiple customers), it is necessary to create the same number of SIEMs, User Interfaces, Authenticators, and SOARs as there are Active Directory instances.

## Permissions system

Permissions system is composed of :

- resources 
- users
- roles

Resources is used to identify the name, id of the resource where the permissions must be accorded. It contains the id, the name, the type of resources and a description.

Users is the list of users that can use a specific resources. It is associated to a role and contains the id, the name, the email and the role.

The role will associated a permissions (read and write) to a resources and can also associate or inherit roles. 

The id : "all" designates all resources or all roles and give all accesses. 

Roles can inherit from others roles, that avoid rewrite same permissions in others permissions.

## Local Authentication

The permissions of local authentication are done by the configuration file and are stored in the database by the local authentication. 

## LDAP Authentication (not implemented yet)

LDAP authentication is not implemented yet. Instead of local roles, the roles of the Active Directory will be used to map the roles of the AD and the local roles of the users.

## Encryption database (not implemented yet)

The database will be encrypted in order to protect illegal accesses to the database. However, only the authenticator that possess the key and the initilization vector will be able to decrypt the database before using it. 

## Check privileges

When the user is sign in or sign up, its credentials will be sent to the authenticator that generate a token encrypted by a password that only the authenticator knows. 

During requests from the user interface to access to some resources, the token will be sent to the authenticator that will check permissions. 

At the end of the session, the user send a sign out and the token become deprecated. A timeout of the session can also close the session and block actions from the user. 

## First init

If the database does not exists in the file configured, a new database is created to manage users and permissions.

During the first launch of the application, several roles and users are created.

- resources: 
    - all (resource of type all that designate all resources)
    - user interface (for access to the userinterface, minimum requirement for all users)
    - global configuration (access to the global configuration of the infrastructure)
   - global privileges (access to the configuration of resources, roles and users)
    - soar index (index name for the soar default index to store playbook and context)
    - soar tasks (tenant for the scheduler to schedule takss)
    - techno scheduler (technology used by default for scheduler tasks)
- roles :
    - superadmin (all privileges and grant all privileges too)
    - analyst (access read only on user interface)
    - admin (inherite from superadmin but can be restricted) (**must be changed to restricted accesses**)
    - scheduler_role (user for the scheduler to perform researches on existing tasks in order to relaunch them at the boot of the application)
- users :
    - siem_system (inherite from superadmin roles and is the user by default)
    - scheduler (user with scheduler_role access to be able to retrieve tasks and launch it again)


## Global privileges backup 

A backup of the jsons for global privileges that is translated in the database is kept in the folder to keep a trace of all versions modifications of the file.

