<!-- 
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
project: siem project
DOCUMENT: installation doc
-->

# Installation tutorial

## Prerequisites

Before running the project, ensure you have the following installed and configured:

The application requires to have the docker images installed on the docker desktop or deamon. Each components must be compiled and available on the docker damon to create a container of it. 

Images: Download the required container images:
```
docker pull ttdantett/devbytesart:<image tag>
```

Security: Valid SSL certificates are mandatory:

server.crt (Certificate)
server.key (Private Key)

```
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -sha256 -days 365 -nodes
```

For selfsigned certificates:
```
openssl req -new -newkey rsa:2048 -keyout server.key -out server.csr -nodes
openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt
```

Storage disk:
Either local or virtual via docker volume (created before launch the configuration).
Copy the certificates on the docker volume.

Prepare the configuration files for the master and slave coordinators.

Open all the ports required and used by the application (see configuration file). Note that the slave coordinator can be used as reverse proxy and launch actions to the component.
It could be required to activate the network in the docker deamon (in docker desktop for example).

The slave coordinator on the machines must be the first component container created. Even before the mastercoordinator. As the master coordinator will send the configuration to the slave coordinator configured.

Prepare the following information to create the custom command line to launch the slave coordinator.

- name of the slavecoordinator (by default slavecoordinator1)
- hostname of the container (by default slavecoordinator1)
- volume of the data
- network host default gateway 
- the right permission on docker to let other container launch docker command (with docker.sock)
- the configuration file completed (by default the configuration file can be used as it is), but be careful to the following element however:
    - id of the slave coordinator
    - bridge 
    - network
    - volumes

Prepare the same information for the master coordinator and the information of the slave coordinators (id, hostname and ips).
And prepare the master password/passphrase for the master coordinator. 

## Installation slave coordinator

Use the following command to launch the slave coordinator:

The "i" parameter for the code python is used to enter the configuration in json text in the command line itself.

The "f" parameter for the code python is used to enter the configuration file path.


```
docker run 
    -v //var/run/docker.sock:/var/run/docker.sock 
    -d 
    --name slavecoordinator1 
    --hostname slavecoordinator1 
    -v dockervolume1:/data/:rw 
    -p 8443:8443 
    --network internal_network 
    --network host 
    --add-host 192.168.0.1:host-gateway 
    -it siem_slavecoordinator 
    
    python SlaveCoordinator.py 
    
    -i 
    
    '{
        \"version\":1,
        \"last_modified\":\"2024-10-2215:14:09\",
        \"infrastructure\":{
            \"id\":\"slavecoordinator1\",
            \"type\":\"slavecoordinator\",
            \"image\":\"siem_slavecoordinator\",
            \"queue\":{
                \"max_queue_size\":15,
                \"backup_file\":\"data_backup_2.txt\"
            },
            \"logger\":{
                \"log_level\":\"debug\",
                \"log_path\":\"slavecoordinator_mon.log\",
                \"max_queue_size\":4096,
                \"max_file\":50,
                \"max_file_size\":1048576,
                \"enable_print\":true,
                \"enable_queue\":true,
                \"enable_file\":true
            },
            \"bridge\":{
                \"enabled\":true
            },
            \"webhook\":{
                \"port\":8443,
                \"host\":\"slavecoordinator1\",
                \"auth_token\":\"my_secure_token\",
                \"certs\":{
                    \"certfile\":\"certs/server.crt\",
                    \"keyfile\":\"certs/server.key\"
                }
            },
            \"volumes\": {
                \"dockervolume1\": {
                    \"bind\": \"/data/\",
                    \"mode\": \"rw\"
                }
            },
            \"storage\": {
                \"path\": \"/data/storage/slavecoordinator1\"
            }, 
            \"sub-infrastructure\":{
                \"logcollectors\":[],
                \"logparsers\":[],
                \"logindexers\":[],
                \"cachesystems\":[],
                \"dedicatedindexsearchmotors\":[],
                \"indexsearchmotors\":[],
                \"userinterfaces\":[]
            }
        }
    }'
```

If the configuration is set on a file, the command used can be the following:

```
 docker run 
    -v //var/run/docker.sock:/var/run/docker.sock 
    -d 
    --name slavecoordinator1 
    --hostname slavecoordinator1 
    -v dockervolume1:/data/:rw 
    -p 8443:8443 
    --network internal_network 
    --network host 
    --add-host 192.168.0.1:host-gateway 
    -it siem_slavecoordinator 

    python SlaveCoordinator.py 
    
    -f <configuration file.json>
```

## Installation master coordinator

Use the following command to launch the coordinator master:

The "i" parameter for the code python is used to enter the configuration in json text in the command line itself.

The "f" parameter for the code python is used to enter the configuration file path.

The "p" parameter for the code python id used to indicates if the master is primary (by default yes).

The "s" is the secret key used for the master coordinator.

```
docker run 
    -d 
    --name mastercoordinator1 
    --hostname mastercoordinator1 
    -v dockervolume1:/data/:rw 
    -p 6000:6000 
    --network internal_network 
    --network host 
    --add-host 192.168.0.1:host-gateway 
    -it siem_mastercoordinator 
    
    python MasterCoordinator.py 
    
    -i '{
        \"version\":1,
        \"last_modified\":\"2024-10-22T17:45:52\",
        \"infrastructure\":{
            \"mastercoordinators\":[
                {\"id\":\"mastercoordinator1\",
                \"type\":\"mastercoordinator\",
                \"primary\":true,
                \"image\":\"siem_mastercoordinator\",
                \"logger\":{
                    \"log_level\":\"debug\",
                    \"log_path\":\"mastercoordinator_mon.log\",
                    \"max_queue_size\":4096,
                    \"max_file\":50,
                    \"max_file_size\":1048576,
                    \"enable_print\":true,
                    \"enable_queue\":true,
                    \"enable_file\":true
                },
                \"volumes\":{
                    \"dockervolume1\":{
                        \"bind\":\"/data/\",
                        \"mode\":\"rw\"
                    }
                },
                \"storage\":{
                    \"path\":\"/data/storage/mastercoordinator1\"
                },
                \"webhook\":{
                    \"host\":\"mastercoordinator1\",
                    \"port\":6000,
                    \"auth_token\":\"my_secure_token\",
                    \"certs\":{
                        \"certfile\":\"certs/server.crt\",
                        \"keyfile\":\"certs/server.key\"
                    }
                }
            }
        ],
        \"slavecoordinators\":[
            {\"id\":\"slavecoordinator1\",
            \"type\":\"slavecoordinator\",
            \"image\":\"siem_slavecoordinator\",
            \"queue\":{
                \"max_queue_size\":15,
                \"backup_file\":\"data_backup_slv_coord_1.txt\"
            },
            \"logger\":{
                \"stats_file\":\"stats_2.txt\",
                \"log_level\":\"debug\",
                \"log_path\":\"mastercoordinator.log\",
                \"max_queue_size\":8192,
                \"max_file\":50,
                \"max_file_size\":1048576,
                \"enable_print\":true,
                \"enable_queue\":true,
                \"enable_file\":true
            },
            \"bridge\":{
                \"enabled\":true
            },
            \"webhook\":{
                \"host\":\"slavecoordinator1\",
                \"port\":8443,
                \"auth_token\":\"my_secure_token\",
                \"certs\":{
                    \"certfile\":\"certs/server.crt\",
                    \"keyfile\":\"certs/server.key\"
                }
            },
            \"storage\":{
                \"path\":\"/data/storage/slavecoordinator1\"
            },
            \"masters\":[
                {\"id\":\"&mastercoordinator1\"}
            ],
            \"sub-infrastructure\":{
                \"logcollectors\":[],
                \"logparsers\":[],
                \"logindexers\":[],
                \"cachesystems\":[],
                \"dedicatedindexsearchmotors\":[],
                \"indexsearchmotors\":[],
                \"userinterfaces\":[
                    {\"id\":\"userinterface1\",
                    \"type\":\"userinterface\",
                    \"image\":\"siem_userinterface\",
                    \"volumes\":{
                        \"dockervolume1\":{
                            \"bind\":\"/data/\",
                            \"mode\":\"rw\"
                        }
                    },
                    \"slavecoordinator\":{
                        \"id\":\"&slavecoordinator1\"
                    },
                    \"queue\":{
                        \"max_queue_size\":8192,
                        \"backup_file\":\"/data/data_backup_userinterface_1.txt\",
                        \"backup_max_file\":50,
                        \"max_backup_file_size\":1073741824
                    },
                    \"logger\":{
                        \"stats_file\":\"stats_2.txt\",
                        \"log_level\":\"debug\",
                        \"log_path\":\"userinterface.log\",
                        \"max_queue_size\":8192,
                        \"max_file\":50,
                        \"max_file_size\":1048576,
                        \"enable_print\":true,
                        \"enable_queue\":true,
                        \"enable_file\":true
                    },
                    \"webrequester\":{
                        \"timeout\":120,
                        \"proxy\":\"None\",
                        \"slave_reverse\":{
                            \"id\":\"None\"
                        }
                    },
                    \"webserver\":{
                        \"host\":\"userinterface1\",
                        \"port\":443,
                        \"auth_token\":\"my_secure_token\",
                        \"certs\":{
                            \"certfile\":\"certs/server.crt\",
                            \"keyfile\":\"certs/server.key\"
                        }
                    },
                    \"webhook\":{
                        \"host\":\"userinterface1\",
                        \"port\":444,
                        \"auth_token\":\"my_secure_token\",
                        \"certs\":{
                            \"certfile\":\"certs/server.crt\",
                            \"keyfile\":\"certs/server.key\"
                        }
                    },
                    \"indexsearchmotor\":{},
                    \"soar\":{},
                    \"authenticator\":{
                        \"id\":\"&authenticator1\"
                    }
                    }
                ],
                \"authenticators\":[
                    {\"id\":\"authenticator1\",
                    \"type\":\"authenticator\",
                    \"image\":\"siem_authenticator\",
                    \"webrequester\":{
                        \"timeout\":120,
                        \"proxy\":\"None\",
                        \"slave_reverse\":{
                            \"id\":\"None\"
                        }
                    },
                    \"volumes\":{
                        \"dockervolume1\":{
                            \"bind\":\"/data/\",
                            \"mode\":\"rw\"
                        }
                    },
                    \"storage\":{
                        \"path\":\"/data/storage/authenticator1\"
                    },
                    \"logger\":{
                        \"log_level\":\"debug\",
                        \"log_path\":\"mastercoordinator_mon.log\",
                        \"max_queue_size\":4096,
                        \"max_file\":50,
                        \"max_file_size\":1048576,
                        \"enable_print\":true,
                        \"enable_queue\":true,
                        \"enable_file\":true
                    },
                    \"webhook\":{
                        \"host\":\"authenticator1\",
                        \"port\":7000,
                        \"auth_token\":\"my_secure_token\",
                        \"certs\":{
                            \"certfile\":\"certs/server.crt\",
                            \"keyfile\":\"certs/server.key\"
                        }
                    },
                    \"slavecoordinator\":{
                        \"id\":\"&slavecoordinator1\"
                    }
                }
            ]
        }
    }
]
}
}
' 
-p True 
-s "changeit"
```

If a configuration file is available, use the following command:

```
docker run 
    -d 
    --name mastercoordinator1 
    --hostname mastercoordinator1 
    -v dockervolume1:/data/:rw 
    -p 6000:6000 
    --network internal_network 
    --network host 
    --add-host 192.168.0.1:host-gateway 
    -it siem_mastercoordinator 
    
    python MasterCoordinator.py 
    
    -f <configuration file path.json>
    -p True 
    -s "changeit"
```

## Example of configuration

These are example of configuration file to use to create basic infrastructure.

- **Default configuration**: User interface, Authenticator, Master coordinator, Slave coordinator. TODO
- SIEM minimal configuration: TODO
- SIEM log collection syslog and SIEM configuration: TODO