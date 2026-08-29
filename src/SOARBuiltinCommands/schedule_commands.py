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
document: schedule_commands
"""

import traceback
from typing import Any

##############################################################
###     Task Scheduler
##############################################################

def schedule_task(self: Any, task_name: str, context_name:str, index:str, tenant:str, instance:str, is_playbook:bool=True, display:bool=True, new_context_name: str=None, run_date: str=None, interval: str=None, cron: str=None):
    """ Schedule a task to run at a specific date, interval or cron
    params:
    - task_name: str => Name of the task to retrieve in the logs
    - context_name: str => Name of the context/Playbook where the function are found
    - index: str => index name required to find the context/playbook in the logs
    - tenant: str => tenant name required to find the context/playbook in the logs
    - instance: str => instance name required to find the context/playbook in the logs
    - is_playbook: bool => if the task is a playbook or a context to play
    - display: bool => if the task must be quiet or displayed in the history
    - cron: str => crontab function to schedule the task
    - interval: str => interval to schedule the task (30s, 30m, 1h, 5d...)
    - run_date: str => date to run the task (format: YYYY-MM-DD HH:MM:SS)
    - new_context_name: str => new context name to create if the task is a playbook
    """
    try:
        self.task_scheduler.schedule_task(task_name, context_name, index=index, tenant=tenant, instance=instance, is_playbook=is_playbook, display=display, new_context_name=new_context_name, run_date=run_date, interval_str=interval, cron_str=cron)
        return "Task scheduled"
    except:
        raise Exception(f"Error while scheduling task {traceback.format_exc()}")


# def schedule_playbook(self: Any, name: str, playbook:str, instance: str, index: str, tenant:str, run_date: str=None, interval: str=None, cron: str=None):
#     """ Schedule a playbook to run it at a specific date, interval or cron
#     params:
#     name: str => Task name
#     playbook: str => Playbook name
#     instance: str => vault instance credentials name
#     index: str => index name where to find the playbook
#     tenant: str => tenant name where to find the playbook
#     run_date: str => date to run the task (format: YYYY-MM-DD HH:MM:SS)
#     interval: dict => interval
#     cron: dict => cron
#     """
#     try:
#         self.task_scheduler.schedule_playbook(name, playbook, instance, index, tenant, run_date=run_date, interval_str=interval, cron_str=cron)
#         return "Playbook scheduled"
#     except:
#         raise Exception(f"Error while scheduling playbook {traceback.format_exc()}")


def schedule_task_list(self: Any):
    """ List the tasks that are registered
    params: None
    """
    try:
        return self.task_scheduler.list_tasks()
    except:
        raise Exception(f"Error while listing tasks {traceback.format_exc()}")
    

def schedule_task_stop(self: Any, name: str):
    """ Stop a task that is registered 
    params:
    - name: str => name of the task to stop
    """
    try:
        self.task_scheduler.stop_task(name)
        return "Task stopped"
    except:
        raise Exception(f"Error while stopping task {traceback.format_exc()}")


def schedule_task_restart(self: Any, name: str):
    """ Restart a task that is registered
    params:
    - name: str => name of the task to restart
    """
    try:
        self.task_scheduler.restart_task(name)
        return "Task restarted"
    except:
        raise Exception(f"Error while restarting task {traceback.format_exc()}")



def schedule_task_remove(self: Any, name: str):
    """ Remove a task that is registered
    params:
    - name: str => name of the task to remove
    """
    try:
        self.task_scheduler.remove_task(name)
        return "Task removed"
    except:
        raise Exception(f"Error while removing task {traceback.format_exc()}")
    