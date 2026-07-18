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
# document: dockerfile log parser
###

FROM python:3.10-slim
# For 32bits or low storage advice
# ENV PIP_NO_CACHE_DIR=1 \
#    PYTHONUNBUFFERED=1
WORKDIR /app
COPY docker/logparser/requirements.txt /tmp/
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
# COPY ../src/logparserconfig.json /app
COPY ../src/LogParser.py /app/
COPY ../src/Listener.py /app/
COPY ../src/QueueManager.py /app/
COPY ../src/Logger.py /app/
COPY ../src/ParameterLoader.py /app/
COPY ../src/certs/server.crt /app/certs/
COPY ../src/certs/server.key /app/certs/
COPY ../src/LPParserInterface.py /app/
COPY ../src/LPFilterInterface.py /app/
COPY ../src/LPAgregatorInterface.py /app/
COPY ../src/LPCategorizerInterface.py /app/
# COPY ../src/LPMapperInterface.py /app/
COPY ../src/LPAnonymizerInterface.py /app/
COPY ../src/LPPlugins /app/LPPlugins/
COPY ../src/Utils.py /app/
COPY ../src/UtilsEnum.py /app/
COPY ../src/UtilsIndexing.py /app/
RUN chmod +x /app/LogParser.py
EXPOSE 443 80 8080 4443 5000-6000
# cd SIEMProject
# docker build -t ttdantett/siem_logparser -f docker/logparser/Dockerfile .


# Other possibility
# docker run -d --name log_collector_container -v /chemin/local/vers/config:/app/config -p 5000-6000:5000-6000 --entrypoint python LogParser.py


# FROM python
# import docker
# client = docker.from_env()
# container = client.containers.run("ttdantett/siem_logparser",name="logparser_1", stdin_open=True, tty=True, detach=True, ports={'5000/tcp': 5000}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/LogParser.py")
# OR
# container = client.containers.run("ttdantett/siem_logparser",name="logparser_1", stdin_open=True, tty=True, detach=True, ports={'5000/tcp': 5000}, volumes={"dockervolume1": {"bind": "/data/", "mode": "rw"}}, command="python /app/LogParser.py -i '{\"id\":\"logparser1\",\"type\":\"logparser\",\"delimiter\":\"\\n\",\"tenant\":\"Tenant-Customer1\",\"logger\":{\"stats_file\":\"stats.txt\"},\"webhook\":{\"ip\":\"0.0.0.0\",\"port\":5005,\"auth_token\":\"my_secure_token\",\"certs\":{\"certfile\":\"certs/server.crt\",\"keyfile\":\"certs/server.key\"}},\"logcollector\":{\"ip\":\"127.0.0.1\",\"port\":\"5000\",\"auth_token\":\"my_secure_token\",\"size\":1000},\"queue\":{\"max_queue_size\":2048,\"backup_file\":\"data_backup_parser.txt\",\"stats_file\":\"stats_parser.txt\",\"max_backup_file\":50,\"max_backup_file_size\":1073741824},\"plugins\":{\"parser_folder\":\"LPPlugins.parser\",\"prefilter_folder\":\"LPPlugins.prefiltering\",\"postfilter_folder\":\"LPPlugins.postfiltering\",\"categorizer_folder\":\"LPPlugins.categorisation\",\"anonymizer_folder\":\"LPPlugins.anonymization\",\"agregator_folder\":\"LPPlugins.agregation\",\"mapper_folder\":\"LPPlugins.mapping\"},\"parser\":{\"type\":\"regex\",\"name\":\"SimpleParser\",\"technology\":\"test\",\"version\":\"1.0\"},\"mapper\":{\"name\":\"SimpleMapping\"},\"agregator\":{\"name\":\"SimpleAgregation\"},\"prefilter\":{\"name\":\"SimplePreFilter\",\"filter\":\"CEF:0|Elastic|Vaporware\",\"out\":false},\"postfilter\":{\"name\":\"SimplePostFilter\",\"filter\":{},\"out\":false},\"categorizer\":{\"name\":\"SimpleCategorisation\"},\"anonymizer\":{\"name\":\"SimpleAnonymization\"}}'")