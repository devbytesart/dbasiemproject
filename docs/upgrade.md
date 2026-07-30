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
DOCUMENT: upragde doc
-->

# Upgrade application

In order to upgrade the application, it is required to upgrade the docker image of all components and create another docker with the new image for all docker image that have been modified on the version. 

The following procedure is temporary and will be modified to have more user friendly procedure.

## Procedure

Use docker pull to download new docker image

```
docker pull ttdantett/siem_soar
docker pull ttdantett/siem_authenticator
docker pull ttdantett/siem_indexsearchmotor
docker pull ttdantett/siem_userinterface
docker pull ttdantett/siem_slavecoordinator
docker pull ttdantett/siem_mastercoordinator
docker pull ttdantett/siem_logindexer
docker pull ttdantett/siem_logparser
docker pull ttdantett/siem_logcollector
docker pull ttdantett/siem_dedicatedindexsearchmotor
docker pull ttdantett/siem_cachesystem
```

## Case 1 : No slave coordinator or master coordinator has been updated in the new version

For all container where the image has been modified, just delete it. 
The application will recreate itself the components that have been deleted. 

## Case 2 : Slave coordinator and/or master coordinator has been updated in the new version

The simplest solution is to save the configuration file of the master and relaunch the slave and master coordinators in order to recreate all the infrastructure from scratch. 