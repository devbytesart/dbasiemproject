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
# document: dockerfile master coordinator
###

FROM python:3.10-slim
# For 32bits or low storage advice
# ENV PIP_NO_CACHE_DIR=1 \
#    PYTHONUNBUFFERED=1
WORKDIR /app
COPY docker/mastercoordinator/requirements.txt /tmp/
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
COPY ../src/WebRequester.py /app/
COPY ../src/Configurator.py /app/
# COPY ../src/globalConfig.json /app
COPY ../src/MasterCoordinator.py /app/
COPY ../src/ParameterLoader.py /app/
COPY ../src/PrivilegesManager.py /app/
COPY ../src/certs/server.crt /app/certs/
COPY ../src/certs/server.key /app/certs/
COPY ../src/Logger.py /app/
COPY ../src/QueueManager.py /app/
COPY ../src/UtilsEnum.py /app/
COPY ../src/Utils.py /app/
RUN chmod +x /app/MasterCoordinator.py
EXPOSE 443 80 8080 4443 5000-6000
# cd SIEMProject
# docker build -t ttdantett/ttdantett/siem_mastercoordinator -f docker/mastercoordinator/Dockerfile .


# Other possibility (change the ip of the gateway)
#  docker run -d --name mastercoordinator1 --hostname mastercoordinator1 -v dockervolume1:/data/:rw -p 6000:6000 --network internal_network --network host --add-host 192.168.178.1:host-gateway -it ttdantett/siem_mastercoordinator python MasterCoordinator.py -i '{\"version\":1,\"last_modified\":\"2024-10-22T17:45:52\",\"infrastructure\":{\"mastercoordinators\":[{\"id\":\"mastercoordinator1\",\"type\":\"mastercoordinator\",\"primary\":true,\"image\":\"ttdantett/siem_mastercoordinator\",\"logger\":{\"log_level\":\"debug\",\"log_path\":\"mastercoordinator_mon.log\",\"max_queue_size\":4096,\"max_file\":50,\"max_file_size\":1048576,\"enable_print\":true,\"enable_queue\":true,\"enable_file\":true},\"volumes\":{\"dockervolume1\":{\"bind\":\"/data/\",\"mode\":\"rw\"}},\"storage\":{\"path\":\"/data/storage/mastercoordinator1\"},\"webhook\":{\"host\":\"mastercoordinator1\",\"port\":6000,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}}}],\"slavecoordinators\":[{\"id\":\"slavecoordinator1\",\"type\":\"slavecoordinator\",\"image\":\"ttdantett/siem_slavecoordinator\",\"queue\":{\"max_queue_size\":15,\"backup_file\":\"data_backup_slv_coord_1.txt\"},\"logger\":{\"stats_file\":\"stats_2.txt\",\"log_level\":\"debug\",\"log_path\":\"mastercoordinator.log\",\"max_queue_size\":8192,\"max_file\":50,\"max_file_size\":1048576,\"enable_print\":true,\"enable_queue\":true,\"enable_file\":true},\"bridge\":{\"enabled\":true},\"webhook\":{\"host\":\"slavecoordinator1\",\"port\":8443,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"storage\":{\"path\":\"/data/storage/slavecoordinator1\"},\"masters\":[{\"id\":\"&mastercoordinator1\"}],\"sub-infrastructure\":{\"logcollectors\":[],\"logparsers\":[],\"logindexers\":[],\"cachesystems\":[],\"dedicatedindexsearchmotors\":[],\"indexsearchmotors\":[],\"userinterfaces\":[{\"id\":\"userinterface1\",\"type\":\"userinterface\",\"image\":\"ttdantett/siem_userinterface\",\"volumes\":{\"dockervolume1\":{\"bind\":\"/data/\",\"mode\":\"rw\"}},\"slavecoordinator\":{\"id\":\"&slavecoordinator1\"},\"queue\":{\"max_queue_size\":8192,\"backup_file\":\"/data/data_backup_userinterface_1.txt\",\"backup_max_file\":50,\"max_backup_file_size\":1073741824},\"logger\":{\"stats_file\":\"stats_2.txt\",\"log_level\":\"debug\",\"log_path\":\"userinterface.log\",\"max_queue_size\":8192,\"max_file\":50,\"max_file_size\":1048576,\"enable_print\":true,\"enable_queue\":true,\"enable_file\":true},\"webrequester\":{\"timeout\":120,\"proxy\":\"None\",\"slave_reverse\":{\"id\":\"None\"}},\"webserver\":{\"host\":\"userinterface1\",\"port\":443,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"webhook\":{\"host\":\"userinterface1\",\"port\":444,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"indexsearchmotor\":{},\"soar\":{},\"authenticator\":{\"id\":\"&authenticator1\"}}],\"authenticators\":[{\"id\":\"authenticator1\",\"type\":\"authenticator\",\"image\":\"ttdantett/siem_authenticator\",\"webrequester\":{\"timeout\":120,\"proxy\":\"None\",\"slave_reverse\":{\"id\":\"None\"}},\"volumes\":{\"dockervolume1\":{\"bind\":\"/data/\",\"mode\":\"rw\"}},\"storage\":{\"path\":\"/data/storage/authenticator1\"},\"logger\":{\"log_level\":\"debug\",\"log_path\":\"mastercoordinator_mon.log\",\"max_queue_size\":4096,\"max_file\":50,\"max_file_size\":1048576,\"enable_print\":true,\"enable_queue\":true,\"enable_file\":true},\"webhook\":{\"host\":\"authenticator1\",\"port\":7000,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"slavecoordinator\":{\"id\":\"&slavecoordinator1\"}}]}}]}}' -p True -s "changeit"

# FROM python
# import docker
# client = docker.from_env()
# container = client.containers.run("ttdantett/siem_mastercoordinator",name="mastercoordinator_1", stdin_open=True, tty=True, detach=True, ports={'443/tcp': 443}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/MasterCoordinator.py")

# TO run docker inside docker 
# On  Windows -> Activate wsl (as admin)
# docker run -v //var/run/docker.sock:/var/run/docker.sock -it docker
# On Linux
# docker run -v /var/run/docker.sock:/var/run/docker.sock -it <image_name>