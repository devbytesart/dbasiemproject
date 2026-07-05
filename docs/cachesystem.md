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
DOCUMENT: cache system doc
-->

# Cache System

Cache system is a component reachable via the network that can store logs associated by the ids and help to find data of the logs (parsed or unparsed), based on the ids.

A cache system must be dedicated to one index in order to avoir data leaks.

This cache system is not as efficient as a true cache system as the component uses the network to be reached. However, this system let several others components from the network to store data from the same index on the same location and reduce space used for the cache.

## Configuration

The cache stores parsed or raw data in seperate fields. 

The max size of the cache is configurable on the configuration file for each type of data. However, it is the **number of log** that can be configured and not the **size in bytes**. 

## Storing and retrieving

Any component from the infrastructure configured with the right token access can store ids and data in the cache system only if the index is the authorized one. 
