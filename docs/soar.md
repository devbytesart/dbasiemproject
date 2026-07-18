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
DOCUMENT: soar doc
-->

# SOAR

The SOAR (Security Orchestration and Authomation Response) is used to launched set of commands and automate some actions at the application level or connected to others applications. The SOAR is used to generate and download reports, schedule tasks, launched conditional, looped and/or dynamic set of commands. 

## Playbook / Context

The difference between playbook and context is important to understand. You can see playbook as template and context as the results of the execution of the playbook. When a command is added to a playbook, only the commands and parameters are added and result is set to None. 
When a command is added to a context, the commands, parameters and results are stored in the card. 
When a playbook is launched, a context is created to get results and the playbook remains unchanged.

## History of Commands

The context/playbook is a list of commands (with or without results) that follow the order of the id. However, some commands let the user create conditions, loop or jump in order to change the flow and the order of commands. 

In order to keep old values, results are stored in a list with the last results as the last value of the list. It is possible to call any results in loop for example. 

It is possible to change with commands the results, commands or parameters of an id or a results in the list. 

The history of commands stored also the variables list in order to keep the current id of the playbook (when stopped), and others variables.

Every historic is saved in the SIEM and can be loaded from the SIEM. The user has to select the index, tenant and vault and configure the application accordingly.

## SOAR Cards

Each commands send is displayed on SOAR Results Card, able to display the id, author, date, commands, parameters, some buttons for actions on the id commands and results displayed with a specific format.

The commands and the parameters can be changed at any moment. The commands can change place and ids will be swapped (**careful with conditions and loop**). In order to save the new commands or parameters, it is required to change the command and play the command. 

The buttons can play, replay (reset the list of results and replay the command), copy the command or the result or delete the card. 

The results displayed in the SOAR Result Card depends on the result format of the SOAR, it can be table, raw data, json or graph or even dashboard... 

## Reload Commands

In order to be able to launch commands from the SOAR, the commands must exists in custom folders (specified in the configuration file) and the SOAR folder. It is python function defined in the file, that can be modified at any time, but required to launch the commands "soar_reload_functions" that will reset and reload the list of commands with new one. **Careful that the commands does not crash as the SOAR cannot be able to find any commands**. For test purpose and before passing in production, use another instance of the SOAR to test your new functions. 

## Save and load contexts

The SOAR system must be saved in the SIEM in order to work. When a command is launched, the SOAR will perform a request to the SIEM to load the context/playbook, add or modify the command and result and save it in the logs of the SOAR waiting for the Log Indexer to save it in the SIEM. That is why, the configuration of the Log Indexer frequency, the waiting time between commands launched in the web interface and the SOAR saving must be configured accordingly. **If Log Indexer does not get logs quickly enough or the saving time in the log too long or the next command is launched from the User Interface too quickly, the context can be not up to date and lead to error**.

Thus, it is required for each SOAR to configure the Index Search Motor components and the Log Indexer to have a SOAR working.

## Vault system

The vault is used as a keystore to store credentialy based on a unique id. The user that has the permission to use the vault id is able to launch the commends with the permissions of the user stored in credentials.

The vault is a file encrypted with SHA256 algoirhtm that files path are defined in the configuration of the application. 

## Scheduled tasks

Scheduled tasks in the SOAR needs the user scheduler present in the vault (**it is not present in the first launched**). The scheduler is used when the SOAR is starting, to request the SIEM and retrieve the saved scheduled tasks to relaunch it. That is why the user scheduler is required and mandatory. 

Schedule tasks can be start, stopped, erase, replay, and display tasks list.

The scheduler can launch only playbook (schedule_playbook) or context (schedule_task command).

Scheduler is able to run:
- at a specific date
- at a fixed interval
- with a cron command (**not implemented yet**)

## Reporting and dashboards

From the SOAR, it is possible to schedule dashboards and download it from the playbook or download it from the search request when created. 

Dashboard can be displayed in the SOAR Cards of the SOAR. Indeed, SOAR can display graph, table from a research and dashboards in the same page. 

## SOAR possibility

SOAR can launch commands, change the order of the next task launched, apply conditions to change to one id or another. 
However, the SOAR Cards are listed and the flow is not visible yet. A project of the next versions will be to displayed the workflow graphically in order to see the conditional branches and loop inside the playbook/context. 

