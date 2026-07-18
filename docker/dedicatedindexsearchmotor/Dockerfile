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
# document: dockerfile dedicated index search motor
###

FROM python:3.10-slim
# For 32bits or low storage advice
# ENV PIP_NO_CACHE_DIR=1 \
#    PYTHONUNBUFFERED=1
WORKDIR /app
COPY docker/dedicatedindexsearchmotor/requirements.txt /tmp/
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
COPY ../src/DedicatedIndexSearchMotor.py /app/
COPY ../src/Listener.py /app/
COPY ../src/QueueManager.py /app/
COPY ../src/Logger.py /app/
COPY ../src/ParameterLoader.py /app/
COPY ../src/IndexFileManager.py /app/
# COPY ../src/SQLFileManager.py /app/
COPY ../src/DataFileManager.py /app/
COPY ../src/certs/server.crt /app/certs/
COPY ../src/certs/server.key /app/certs/
COPY ../src/Utils.py /app/
COPY ../src/UtilsEnum.py /app/
RUN chmod +x /app/DedicatedIndexSearchMotor.py
EXPOSE 443 80 8080 4443 5000-6000
# cd SIEMProject
# docker build -t ttdantett/siem_dedicatedindexsearchmotor -f docker/dedicatedindexsearchmotor/Dockerfile .


# Other possibility
# docker run -d --name log_dedicatedindexsearchmotor_container -v /chemin/local/vers/config:/app/config -p 5000-6000:5000-6000 --entrypoint python LogCollector.py


# FROM python
# import docker
# client = docker.from_env()
# container = client.containers.run("ttdantett/siem_dedicatedindexsearchmotor",name="dedicatedindexsearchmotor_1", stdin_open=True, tty=True, detach=True, ports={'443/tcp': 443}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/DedicatedIndexSearchMotor.py")
# OR
# container = client.containers.run("ttdantett/siem_dedicatedindexsearchmotor",name="logcollector_1", stdin_open=True, tty=True, detach=True, ports={'443/tcp': 443}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/LogCollector.py -i '{\"id\":\"logcollector1\",\"type\":\"logcollector\",\"logger\":{\"stats_file\":\"stats.txt\"},\"receiver\":{\"ip\":\"0.0.0.0\",\"protocol\":\"TCP\",\"port\":55555,\"timeout\":10},\"webhook\":{\"ip\":\"0.0.0.0\",\"port\":5000,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"queue\":{\"max_queue_size\":2048,\"backup_file\":\"data_backup_logcol.txt\",\"stats_file\":\"stats_logcol.txt\",\"max_backup_file\":50,\"max_backup_file_size\":1073741824}}'")