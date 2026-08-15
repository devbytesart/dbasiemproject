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
document: docker manager
"""

import docker
from docker.types import LogConfig
import os
from Configurator import *
# from Logger import *
import socket
from docker.errors import NotFound, APIError

class DockerManager:
    def __init__(self, bridge=True):
        self.client = docker.from_env()
        self.bridge = bridge
        self.memory_limit = "512m" # TODO add this in config
        self.memswap_limit = "1gb" # TODO add this in config
        # Create a network for the internal communication
        try:
            if bridge:
                self.internal_network = self.client.networks.list(names=["internal_network"])[0]
        except NotFound:
            if bridge:
                self.internal_network = self.client.networks.create(
                    "internal_network",
                    driver="bridge",
                    ipam=docker.types.IPAMConfig(
                        pool_configs=[docker.types.IPAMPool(subnet='192.168.100.0/24', gateway='192.168.100.1')]
                    )
                )

    def remove_container(self, container_tag, only_if_stopped=True):
        """Remove a container with retries."""
        # TODO add this value (3) in configuration file
        for attempt in range(3):
            try:
                existing_container = self.client.containers.get(container_tag)
                # Check if the container should only be removed if stopped
                if only_if_stopped:
                    container_state = existing_container.attrs["State"]
                    if container_state["Status"] != "running":
                        print(f"Attempt {attempt + 1}: Container '{container_tag}' found and stopped. Removing it...")
                        existing_container.remove(force=True)
                        return True
                    else:
                        print(f"Attempt {attempt + 1}: Container '{container_tag}' is still running.")
                else:
                    print(f"Attempt {attempt + 1}: Removing container '{container_tag}' regardless of its state...")
                    existing_container.remove(force=True)
                    return True
            except NotFound:
                print(f"Attempt {attempt + 1}: No existing container named '{container_tag}' found.")
                return True  # Container is effectively removed if not found
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error while removing container '{container_tag}': {e}")
        print(f"Failed to remove container '{container_tag}' after 3 attempts.")
        return False


    def create_container(self, image_name, container_tag, ports, volumes, command):
        """Create a new container, avoiding name conflicts."""
        # Remove container if it exists
        self.remove_container(container_tag)
        print("Creating container...")
        # Config network 
        networking_config = self.client.api.create_networking_config({
            "internal_network": self.client.api.create_endpoint_config(
                aliases=["logcollector1"]  # Alias DNS for logcollector1
            )
        })
        # Create the container
        print(image_name, container_tag, ports, volumes, command) 
        if self.bridge:
            container = self.client.containers.run(
                image_name,
                name=container_tag,
                stdin_open=True,
                hostname=container_tag,
                tty=True,
                detach=True,
                volumes=volumes,
                ports=ports,
                command=command,
                network="internal_network",
                networking_config=networking_config,
                # TODO find a way to add it in config file if driver or not
                # log_config=LogConfig(type="none"),
                # mem_limit=self.memory_limit,
                # memswap_limit=self.memswap_limit,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                # network_mode="host",
                privileged=True # TODO must be changed if another solution possible
            )
        else:
            # Network host
            container = self.client.containers.run(
                image_name,
                name=container_tag,
                stdin_open=True,
                hostname=container_tag,
                tty=True,
                detach=True,
                volumes=volumes,
                command=command,
                network="host",
                # TODO find a way to add it in config file if driver or not
                # log_config=LogConfig(type="none"),
                # mem_limit=self.memory_limit,
                # memswap_limit=self.memswap_limit,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                privileged=True # TODO must be changed if another solution possible
            )

        # Try to connect the container on network
        try:
            # TODO invert this lines if any problem
            print("Reload container")
            container.reload()
            time.sleep(1)
            # print("Connect container")
            # self.internal_network.connect(container)
            print(f"Container '{container_tag}' connected to network 'internal_network'. {traceback.format_exc()}")
        except APIError as e:
            print(f"Failed to connect container '{container_tag}' to network: {e}")
        return container


    def container_exists(self, container_id):
        """Check if a Docker container with the given ID exists."""
        try:
            container = self.client.containers.get(container_id)
            return container is not None
        except docker.errors.NotFound:
            return False
        except Exception as e:
            print(f"Error checking if container exists: {e}")
            return False

    def get_container_status(self, container_id):
        """ 
        Return dictionary of detailed status of the container
        ex:
            dict: Status, Health (if configured), ExitCode, Error, StartedAt...
        """
        try:
            container = self.client.containers.get(container_id)
            # Force refresh data container 
            container.reload()
            
            state = container.attrs.get("State", {})
            
            status_info = {
                "exists": True,
                "status": state.get("Status", "unknown"),  # 'running', 'exited', 'paused', 'restarting'...
                "running": state.get("Running", False),
                "paused": state.get("Paused", False),
                "restarting": state.get("Restarting", False),
                "dead": state.get("Dead", False),
                "exit_code": state.get("ExitCode", 0),
                "error": state.get("Error", ""),
                "started_at": state.get("StartedAt", ""),
                "finished_at": state.get("FinishedAt", ""),
                "health": state.get("Health", {}).get("Status", "none")  # 'healthy', 'unhealthy', 'starting'
            }
            
            return status_info

        except NotFound:
            return {"exists": False, "status": "not_found", "running": False}
        except Exception as e:
            print(f"Error getting status for container {container_id}: {e}")
            return {"exists": False, "status": "error", "error": str(e), "running": False}

# Example usage
# if __name__ == "__main__":
#     manager = DockerManager()

## Python code to use
# import docker
# client = docker.from_env()
# container = client.containers.run("ubuntu:latest",
# name="test",
# stdin_open=True,
# tty=True,
# detach=True,
# ports={'2222/tcp': 3333}, 
# volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, 
# command="python Main.py")

#container.logs()