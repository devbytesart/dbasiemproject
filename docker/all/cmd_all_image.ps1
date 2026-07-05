# ##
# Copyright 2026 ttdantett DevBytesArt

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
# document: dockerfile launch all
# ##
docker build -t ttdantett/siem_cachesystem -f docker/cachesystem/Dockerfile .
docker build -t ttdantett/siem_dedicatedindexsearchmotor -f docker/dedicatedindexsearchmotor/Dockerfile .
docker build -t ttdantett/siem_indexsearchmotor -f docker/indexsearchmotor/Dockerfile .
docker build -t ttdantett/siem_logcollector -f docker/logcollector/Dockerfile .
docker build -t ttdantett/siem_logindexer -f docker/logindexer/Dockerfile .
docker build -t ttdantett/siem_logparser -f docker/logparser/Dockerfile .
docker build -t ttdantett/siem_mastercoordinator -f docker/mastercoordinator/Dockerfile .
docker build -t ttdantett/siem_slavecoordinator -f docker/slavecoordinator/Dockerfile .
docker build -t ttdantett/siem_userinterface -f docker/userinterface/Dockerfile .
docker build -t ttdantett/siem_authenticator -f docker/authenticator/Dockerfile .
docker build -t ttdantett/siem_soar -f docker/soar/Dockerfile .


docker save -o ttdantett/siem_mastercoordinator ttdantett/siem_mastercoordinator
docker save -o ttdantett/siem_slavecoordinator ttdantett/siem_slavecoordinator
docker save -o ttdantett/siem_authenticator ttdantett/siem_authenticator
docker save -o ttdantett/siem_cachesystem ttdantett/siem_cachesystem
docker save -o ttdantett/siem_dedicatedindexsearchmotor ttdantett/siem_dedicatedindexsearchmotor
docker save -o ttdantett/siem_indexsearchmotor ttdantett/siem_indexsearchmotor
docker save -o ttdantett/siem_logcollector ttdantett/siem_logcollector
docker save -o ttdantett/siem_logindexer ttdantett/siem_logindexer
docker save -o ttdantett/siem_logparser ttdantett/siem_logparser
docker save -o ttdantett/siem_userinterface ttdantett/siem_userinterface
docker save -o ttdantett/siem_soar ttdantett/siem_soar