<!-- 
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
DOCUMENT: user interface doc
-->

# User Interface

The User Interface is responsible to send the html page to the user.
Several page are available through the User Interface component and each page is able to requests, according to the documentation, to another component to have response (Index Search Motor, SOAR, ...).

The User Interface allows a user to request with API requests and/or API requests. The User Interface is a kind of proxy.

## Configuration interface

The configuration main page is used to :

- configure the user preferences (**not implemented yet**)
- configure the users permissions, roles and resources. (**only if user has permissions to do it**)
- configure the global configurations of the applications (components and infrastructure of SIEM and SOAR) (**only if user has permissions to do it**)

According to the configuration page displayed (global configuration or permissions, or preferences), a formular is available to help the user to create new elements. However, modification or deletion must be done directly from the JSON configuration. An element from the JSON configuration can be copied and modified. 

## Search interface

The search page is used to launch requests in the index and displayed any kind of results : table or graphics. 

This page is composed of a search bar with suggestions proposed based on the text entered in the search bar. Indeed, several kind of commands for search can be used and suggestions provide details about the structure.

The help page displayed the details of commands with explanation, structures and examples. 

With the command ***Ctrl + Enter***, the requests is sent to the server. 

The User Interface will get the request from the user and send it to the Index Search Motor configured to get results in JSON format. The JSON result will be interpreted to display the right type on the webpage. 

The web page is also sending request timeout reset to keep the user connected until the token is expired. Data are saved in the Index Search Motor.

In case of table, only the x (10 by default) first results are displayed, but the user can change the number of values in pages, load others pages. To summarize, in general, only a part of data in table are displayed in the User Interface but all data are stored in the Index Search Motor component. 

## Documentation interface
### Main documentation

The main documentation is organised with a global presentation, a tutorial to install the application, and a tutorial more precised to use it (**not implemented yet**).

The main documentation introduces all components of the application in order to understand how the infrastructure and all components works.

(**not implemented yet**)
The tutorial to install the application is used to explain the user how to install and configure the application. Only simple installation are explained and is explained in this part in order to have a functional first application or launch.

(**not implemented yet**)
The tutorial, is more precised and used to explain details about configuration, proposed some infrastructures to segregate data, to have redundancy and so on.

### API documentation

The API documentation proposes a swagger that explain details about requests to send to the User Interface in order to have results directly from the command. However, obsviouly, results of search will be displayed in JSON format.

The swagger lets the user tests some commands directly from this page with the token of your session.

## Dashboard interface

The dashboard interface enables the user to display dashboard existing in the SIEM. Indeed, the application is designed to saved all customs elements on the SIEM index and be requested as others data.

Dashboards is using tags to select index, tenant and technologies.
After selecting these tags, available dashboards name are selectables.

Refresh interval and limits are parameters to reload and display the dashboards.

## Edition interface

The Edition interface is used to create dashboard and report and save it in the SIEM in order to find with an usual search query. 

Ediiton has two tabs to create a dashboard and create the report.

In order to place widget, select, drag and drop in the drop zone at the center of the screen and resize it. The dashboard is limited to surface displayed in order to be able to display all the dashboard in the same page. The size proportion will be saved in the SIEM in order to keep the same proportion independantly of the size of the screen.

The same principle is applied to the report reation but the widget will be displayed one below the others in order to display a printable document and not be limited to number of widget or size of table and graph displayed. Only the width of the page is a limitation. 

In order to save the dashboard, show the panel at the top, select the index, the tenant, the technology and put the name of the dashboard.

The dashboard tag at the right is used to load an existing dashboard or report and be able to modify it.

## SOAR interface

### Context ? Playbook ? 

SOAR is working with contexts and playbooks. Playbook will not launch commands but save it. Context will launch the command and display the results in the SOAR Card. When a playbook is launched, it create a context with the same name with dates or another custom name to display results, but playbook will only save commands and not launch it really.

### Interface 

The SOAR interface is used to display playbook and contexts and launch others commands that will be added in the playbook of the context.

In order to launch commands, it is required to load or create a new context/playbook by selecting the tenant, index and vault instance and set the name of the playbook/dashboard. 

The vault instance is used to store the credentials to connect to another application or save the credentials of the SIEM and let other users to have access if the owner grant right to launch this playbook/context and use the credential vault. Credential are never displayed, but can be displayed by creating a specific command. So, it is mandatory to be careful and know what commands are available to avoid data leaks.

The slide "playbook mode" is used to select if it is a context or a playbook.

On the top right, a JSON is visible to see the history of commands, parameters and results.

Suggestions of commands are provided in the command bar with details of the commands and parameters displayed in order to help the user to set the correct parameters.

### Act on all the playbook

With these buttons, acts on all the commands of the playbook.

- Play All : The play all function  will play all the commands one after the others and display result (or create the context). The playbook will start at the current task.
- Replay All: Replay all will reset the results of the context (jere only the context) and relaunch the playbook or the context.
- Stop: Stop will send the command to stop the playbook as soon as possible. Be careful as it is asynchonous.
- Import: Let the user import context or playbook depending on the slide "playbook mode".
- Export: Export will export in json format the playbook or the context.
- Delete: Delete will reset all the context/playbook.
- Launch: Launch will take the command entered in the bar and add it in the context. If in context, it will play the command and add the result in the context, else only the command will be added.

### SOAR Card Results

Each result from the SOAR is displayed in a SOAR Card, that let the user:
- the id of the context
- the command launched
- author of the command (**only soar for now**)
- date of the command launched
- button to copy the command
- button to edit the original command and modify the playbook/context
- play the command only (add a new result in the list of results)
- replay the command only (reset the results and add a new one)
- delete the command of the list
- parameters of the command
- results (display as a table, raw or graph)

The SOAR Cards can be swapped by drag and drop the cards to another place.

### How is it saved and launched ? 

In order to keep the context/playbook is up to date, each commands results or new commands added must be saved in the SIEM. 

To do this, the SOAR must log the context up to date in the log and a log indexer must save the context in the SIEM. Then in order to get the new version, a SIEM search is done. 
**Important:** Because of this system, a delay must be configured in the SOAR to save and get the last version between each commands launched. With a quick system and quick commands launched, 3 seconds is enough for the command delay, 1 second must be configured in the logindexer to get the logs from the SOAR. But value, must be adapted. *This system must be changed as it could lead to error*

## API requests

User Interface provide API requests in order to be able to request (send search, get page, send soar commands) via the User Interface to get results.

A swagger is implemented to let the user perform tests directly from the web page.

A dedicated API request is available in this documentation to find more details.