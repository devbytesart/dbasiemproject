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
DOCUMENT: logcollector doc
-->

# Log Collector

The log collector is a component responsible for receiving and storing log data. Its main purpose is to handle large volumes of incoming logs and prevent data loss when a device generates logs at a rate higher than the system can immediately process.

## Type of collection

The log collector is able to get logs from different type of protocol and sources such as UDP or TCP listener or file reader.

### Listener TCP/UDP

The selection of type listener is done in the configuration file with the host, the port, the protocol, certificates and timeout.

The log collector will listen logs on the port configured and store the logs in queue.

Only one port listening is possible per log collector.

### File reader

The file reader is used to read file that contains logs and can be configured in the configuration file by specifying the file path.

## High volume data management

In order to manage high volume of data received and not loose data by the log collector, two features are implemented in this order queue and file storage.

### Queue

First, when logs are received by the log collector, they are stored in the memory with queue that let the log collector to send these logs fast to the log parser when requested.

The queue has a limited size configurable in the configuration file.

### File storage

When the queue is full, the recent logs are stored in the files to respect the order of reception of logs. Older logs are sent to before the recents one. 

The size and the number of files are configurable in the configuration file. 

When file are full, the recents logs are lost. 

Files are regularly emptied to feed the queue in order to keep the logs forwarding to the log parser as fast as possible. 

Only logs in queues are sent to log parser, then the file is transfer to the queue.

## Log Preparsing

In order to prepare the log parsing and be able to parse multiline logs, it is possible to configure a regex to define the end of the logs. 

By default, the line break is used but another regex is possible in order to parse multiline logs.

The regex won't modify the log itself but add a specific BREAKLINE caracter/word to segregate the logs and keep the regex in the line of log.