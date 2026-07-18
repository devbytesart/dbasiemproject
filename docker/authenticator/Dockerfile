###
# Copyright 2026 ttdantett DevBytesArt®

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# author: ttdantett
# title: siem project
# document: dockerfile authenticator
###

FROM python:3.10-slim
# For 32bits or low storage advice
# ENV PIP_NO_CACHE_DIR=1 \
#    PYTHONUNBUFFERED=1
WORKDIR /app
COPY docker/authenticator/requirements.txt /tmp/
# In case of error during the building of docker
# RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#    python3-dev
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Decomment if the RUN apt-get update is available
#RUN apt-get purge -y --auto-remove build-essential python3-dev
#RUN rm -rf /var/lib/apt/lists/*
COPY ../src/ServiceBase.py /app/
COPY ../src/Webhook.py /app/
COPY ../src/CMDHandler.py /app/
COPY ../src/Logger.py /app/
COPY ../src/WebRequester.py /app/
COPY ../src/Configurator.py /app/
COPY ../src/Authenticator.py /app/
COPY ../src/ParameterLoader.py /app/
COPY ../src/DockerManager.py /app/
COPY ../src/certs/server.crt /app/certs/
COPY ../src/certs/server.key /app/certs/
COPY ../src/ResourcesMonitor.py /app/
COPY ../src/PrivilegesManager.py /app/
COPY ../src/QueueManager.py /app/
COPY ../src/Utils.py /app/
COPY ../src/UtilsEnum.py /app/
RUN chmod +x /app/Authenticator.py
EXPOSE 443 80 8080 4443 5000-6000
# cd SIEMProject
# docker build -t ttdantett/siem_authenticator -f docker/authenticator/Dockerfile .

# Require create network the first time
#  docker network create --driver bridge --subnet=192.168.100.0/24 internal_network

# Other possibility (change the ip of the gateway)
# docker run -v //var/run/docker.sock:/var/run/docker.sock -d --name authenticator1 --hostname authenticator1 -v dockervolume1:/data/:rw -p 8443:8443 --network internal_network --network host --add-host 192.168.178.1:host-gateway -it ttdantett/siem_authenticator python authenticator.py -i '{\"version\":1,\"last_modified\":\"2024-10-2215:14:09\",\"infrastructure\":{\"id\":\"authenticator1\",\"type\":\"authenticator\",\"image\":\"ttdantett/siem_authenticator\",\"queue\":{\"max_queue_size\":15,\"backup_file\":\"data_backup_2.txt\"},\"logger\":{\"stats_file\":\"stats_2.txt\"},\"monitoring\":{\"log_level\":\"debug\",\"log_path\":\"authenticator_mon.log\",\"max_queue_size\":4096,\"max_file\":50,\"max_file_size\":1048576},\"webhook\":{\"port\":8443,\"host\":\"authenticator1\",\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"volumes\": {\"dockervolume1\": {\"bind\": \"/data/\",\"mode\": \"rw\"}},\"storage\": {\"path\": \"/data/storage/authenticator1\"}, \"sub-infrastructure\":{\"logcollectors\":[],\"logparsers\":[],\"logindexers\":[],\"cachesystems\":[],\"dedicatedindexsearchmotors\":[],\"indexsearchmotors\":[],\"userinterfaces\":[]}}}'

# FROM python
# import docker
# client = docker.from_env()
# container = client.containers.run("ttdantett/siem_authenticator",name="authenticator_1", stdin_open=True, tty=True, detach=True, ports={'443/tcp': 443}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/authenticator.py")

# TO run docker inside docker 
# On  Windows -> Activate wsl (as admin)
# docker run -v //var/run/docker.sock:/var/run/docker.sock -it docker
# On Linux
# docker run -v /var/run/docker.sock:/var/run/docker.sock -it <image_name>