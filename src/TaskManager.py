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
document: task manager
"""

import schedule
import threading
from datetime import datetime, timedelta
import time
import json
import re
import atexit
import signal
import traceback
import UtilsIndexing as utindex
from functools import partial

class TaskManager:
    def __init__(self, commands, logger, queue, instance, index="soar", tenant="soar_tasks", technology="scheduler"):
        self.logger = logger
        self.commands = commands
        self.queue = queue
        self._shutdown = False
        self.instance = instance
        self.index = index
        self.tenant = tenant
        self.technology = technology
        self._lock = threading.Lock()
        self.named_jobs = {}  # key: task_name, value: dict with job info

        # Thread for scheduled loop
        self._scheduler_thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        self._scheduler_thread.start()

        atexit.register(self.shutdown)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.log("info", f"Received signal {signum}, shutting down scheduler.")
        self.shutdown()

    def shutdown(self):
        with self._lock:
            if not self._shutdown:
                self._shutdown = True
                self.logger.log("info", "Shutting down task manager...")

    def _run_scheduler_loop(self):
        while not self._shutdown:
            schedule.run_pending()
            time.sleep(1)

    def _run_task(self, func_name, params):
        try:
            if func_name not in self.commands:
                raise ValueError(f"Command '{func_name}' not found")
            self.logger.log("info", f"Running task: {func_name} with params {params}")
            func = self.commands[func_name]["function"]
            func(**params)
        except Exception as e:
            self.logger.log("error", f"Error running task {func_name}: {e}")

    def _parse_interval_string(self, interval_str):
        units = {
            's': 'seconds', 'sec': 'seconds',
            'm': 'minutes', 'min': 'minutes',
            'h': 'hours',
            'd': 'days',
        }
        match = re.fullmatch(r'(\d+)\s*(s|sec|m|min|h|d)', interval_str.strip(), re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid interval format: '{interval_str}'")
        value, unit = match.groups()
        unit = units[unit.lower()]
        return int(value), unit
    
    def init_scheduled_task(self):
        """ Search in the index to find data and restart the schedule task """
        try:
            self.logger.log("info", "Task Manager, init scheduled tasks")
            query = "!search type:scheduled_task"
            print("self.instance", self.instance)
            print("self.index", self.index)
            print("self.tenant", self.tenant)
            print("self.techno", self.technology)
            res = self.commands["siem_search"]["function"](self.instance, query, [self.index], [self.tenant], [self.technology])
            print("res:", str(res), str(type(res)))
            if res != "[]":
                print("taskmgm init scheduled res:", str(res))
                res = json.loads(res)
                data = res.get("data")
                if len(res) > 0:
                    for task in data:
                        if task.get("status") == "active":
                            id = task.get("id")
                            name = task.get("name")
                            self.logger.log("info", f"Restart Scheduled task: {name}")
                            params = task.get("params",{})
                            subparams = params.get("params",{})
                            sched_params = task.get("sched_params",{})
                            context_name = sched_params.get("context_name")
                            task_name = sched_params.get("task_name")
                            new_context_name = sched_params.get("var_name") if "var_name" in sched_params else sched_params.get("new_context_name")
                            index = subparams.get("index")
                            tenant = subparams.get("tenant")
                            instance = subparams.get("instance", self.instance)
                            is_playbook = subparams.get("playbook",True)
                            display = True
                            cron_str = run_date = interval_str = None
                            trigger = task.get("trigger")
                            if trigger == "cron":
                                cron_str = task.get("frequency")
                            elif trigger == "interval":
                                interval_str = task.get("frequency_str")
                            elif trigger == "run_date":
                                run_date = task.get("frequency")
                            print("data: ", task_name, context_name, new_context_name, index, tenant, instance, str(is_playbook))
                            self.schedule_task(task_name, context_name, instance, index, tenant, is_playbook, display, new_context_name, run_date, interval_str, cron_str, id)
                return True
            return False  
        except:
            self.logger.log("error", f"Failed to init scheduled task {traceback.format_exc()}")
            return False


    def schedule_task(self, task_name, context_name, instance, index, tenant,
                      is_playbook=True, display=True, new_context_name=None,
                      run_date=None, interval_str=None, cron_str=None, siem_id=None):
        # Create siem_id if siem_id is None
        print("schedule_task siem_id:", str(siem_id), str(type(siem_id)))
        if not siem_id:
            siem_id = utindex.create_random_id()
        with self._lock:
            if self._shutdown:
                self.logger.log("warning", f"Skipping scheduling of '{task_name}': TaskManager is shutting down.")
                return

            func = "soar_set_context"
            subparams = {
                "name": context_name,
                "instance": instance,
                "index": index,
                "tenant": tenant,
            }

            if is_playbook:
                subfunc = "soar_play_playbook"
                subparams.update({
                    #"task_name": task_name,
                    #"context_name": context_name,
                    "var_name" : new_context_name,
                    #"is_playbook" : True 
                })
            else:
                subfunc = "soar_play_context"
                subparams.update({
                    "playbook": False,
                    "add_context": display,
                    "context_name": new_context_name
                })

            params = {
                "name": "scheduled_" + new_context_name,
                "instance": instance,
                "index": index,
                "tenant": "tasks_context",
                "command": subfunc,
                "params": subparams,
                "author": "scheduler",
                "command_id": -1,
                "playbook": False,
                "display": display,

            }
            sched_params = {
                "context_name": context_name,
                "new_context_name": new_context_name,
                "task_name": task_name
            }

            job_func = partial(self._run_task, func, params)
            job_data = {
                "id": siem_id,
                "name": task_name,
                "function": func,
                "params": params,
                "status": "active"
            }

            try:
                if run_date and run_date != "None":
                    if isinstance(run_date, str):
                        run_date = datetime.fromisoformat(run_date)
                    if run_date < datetime.now():
                        raise ValueError("run_date is in the past")

                    delay = (run_date - datetime.now()).total_seconds()
                    timer = threading.Timer(delay, job_func)
                    timer.start()

                    job_data.update({
                        "trigger": "date",
                        "frequency_str": run_date,
                        "frequency": run_date.isoformat(),
                        "job": timer
                    })
                    self.logger.log("info", f"Scheduled one-time task '{task_name}' at {run_date}")

                elif interval_str and interval_str != "None":
                    value, unit = self._parse_interval_string(interval_str)
                    sched = getattr(schedule.every(value), unit).do(job_func)

                    job_data.update({
                        "trigger": "interval",
                        "frequency_str": interval_str,
                        "frequency": f"{value} {unit}",
                        "job": sched
                    })
                    self.logger.log("info", f"Scheduled repeating task '{task_name}' every {value} {unit}")

                else:
                    raise ValueError("Must provide one of: run_date or interval_str")

                self.named_jobs[task_name] = job_data

                copy_job_data = {
                    "id": siem_id,
                    "type": "scheduled_task",
                    "name": task_name,
                    "instance": instance,
                    "function": func,
                    "params": params,
                    "sched_params": sched_params,
                    "status": "active",
                    "trigger": job_data["trigger"],
                    "frequency": job_data["frequency"],
                    "frequency_str" : job_data["frequency_str"]
                }
                print("copy_job_data", str(copy_job_data))
                task_to_index = utindex.create_simple_log(self.index, self.tenant, self.technology, task_name, copy_job_data, siem_id)
                print("task_to_index:", str(task_to_index))
                self.queue.enqueue(json.dumps(task_to_index).encode("utf-8"))
                print("after_enqueue")

            except Exception as e:
                self.logger.log("error", f"Error scheduling task '{task_name}': {e}")

    def remove_task(self, task_name):
        with self._lock:
            job_data = self.named_jobs.pop(task_name, None)
            if not job_data:
                self.logger.log("warning", f"Task '{task_name}' not found")
                return

            job = job_data.get("job")
            job["status"] = "deleted"

            # Save the new log
            print("remove task copy_job_data", str(job_data))
            task_to_index = utindex.create_simple_log(self.index, self.tenant, self.technology, task_name, job_data, job_data["id"])
            print("remove task task_to_index:", str(task_to_index))
            self.queue.enqueue(json.dumps(task_to_index).encode("utf-8"))
            print("remove task after_enqueue")
            # self.queue.enqueue(json.dumps(job).encode("utf-8"))

            if isinstance(job, schedule.Job):
                schedule.cancel_job(job)
            elif isinstance(job, threading.Timer):
                job.cancel()

            self.logger.log("info", f"Removed task '{task_name}'")

    def list_tasks(self):
        with self._lock:
            return [
                {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "function": data.get("function"),
                    "params": data.get("params"),
                    "trigger": data.get("trigger"),
                    "frequency": data.get("frequency"),
                    "status": data.get("status")
                }
                for data in self.named_jobs.values()
            ]

    def stop_task(self, task_name):
        with self._lock:
            job_data = self.named_jobs.get(task_name)
            if not job_data:
                raise ValueError(f"Task '{task_name}' not found")

            job = job_data.get("job")
            if isinstance(job, schedule.Job):
                schedule.cancel_job(job)
                self.logger.log("info", f"Stopped scheduled job for task '{task_name}'")
            elif isinstance(job, threading.Timer):
                job.cancel()
                self.logger.log("info", f"Cancelled one-time timer for task '{task_name}'")

            # Delete the reference to the object job, but keep the other info
            job_data["job"] = None
            job_data["status"] = "paused"

            # Create the new log
            print("stop task copy_job_data", str(job_data))
            task_to_index = utindex.create_simple_log(self.index, self.tenant, self.technology, task_name, job_data, job_data["id"])
            print("stop task task_to_index:", str(task_to_index))
            self.queue.enqueue(json.dumps(task_to_index).encode("utf-8"))
            print("stop task after_enqueue")
            # self.queue.enqueue(json.dumps(job_data).encode("utf-8"))


    def restart_task(self, task_name):
        with self._lock:
            job_data = self.named_jobs.get(task_name)
            if not job_data:
                raise ValueError(f"Task '{task_name}' not found")

            if job_data.get("status") != "paused":
                raise ValueError(f"Task '{task_name}' is not paused")

            # Relaunch new tasks with old parameters
            func_name = job_data["function"]
            params = job_data["params"]
            trigger = job_data["trigger"]
            frequency = job_data["frequency"]
            job_func = partial(self._run_task, func_name, params)

            if trigger == "date":
                self.logger.log("warning", f"Cannot restart one-time task '{task_name}' — reschedule it explicitly")
                return

            elif trigger == "interval":
                value, unit = self._parse_interval_string(frequency)
                sched = getattr(schedule.every(value), unit).do(job_func)
                job_data["job"] = sched

            else:
                raise ValueError(f"Unsupported trigger type '{trigger}' for task '{task_name}'")

            job_data["status"] = "active"
            self.logger.log("info", f"Restarted task '{task_name}' with trigger '{trigger}' and frequency '{frequency}'")

            # Save the new log
            print("restart task copy_job_data", str(job_data))
            task_to_index = utindex.create_simple_log(self.index, self.tenant, self.technology, task_name, job_data, job_data["id"])
            print("restart task task_to_index:", str(task_to_index))
            self.queue.enqueue(json.dumps(task_to_index).encode("utf-8"))
            print("restart task after_enqueue")
            # self.queue.enqueue(json.dumps(job_data).encode("utf-8"))
