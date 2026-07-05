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
DOCUMENT: index search motor doc
-->

# Index Search Motor

The Index Search Motor (ISM) is the element that will interpret the request for the SIEM, launch the research and keep results in memory waiting the user interface to request the page or all results.

ISM will divide the researches between DISM (Dedicated Index Search Motor) and concatenate results.

The request sent to the ISM can results in differents type of data that follow a specific json structure.

Type of results:
- table of data
- graph
    - pie chart
    - donuts chart
    - line chart
    - bar chart 
    - polar chart
    - ...
- modifiable table (with SOAR only)

## Request Interpretation

The ISM will interpret the search request sent from the user interface and uses the design pattern (**Chain of Responsibility**). The request pass through differents operations that interpret the keyword of the request and execute the operation to send the result to the next operation.

The pipe "|" is used to split the differents operations to construct a results.

## Suggestions

Each operations will propose help and suggestions that will be displayed in the search bar in order to help the user to create his request.

## Help

Help gives more details about the operations and the way to formulate it. It can give specific advises in its using too. 

## Operations

Several type of operations are available which start with a specific keyword. By default the keyword starts with "!".

However, it is possible to change the keyword, but it can create others changes to perform in the SOAR commands.

Each operation is able to perform a specific action on the result of the previous commands and are split by the pipe key.

The following operations are available:
- Advanced conditions
- Projection
- Rendering
- Counting
- Transformation
- Variables

### Advanced Conditions Operation

The advanced conditions is the main operation as it must be used in each researches. This command will get the conditions of the researches to filter and display data. 

It can contains all data or filtered data with certains conditions.

The filtering can be done with: 

- ***field:value***
- ***field:value CONDITION field:value***
- ...

The help function in the "Search" webpage gives you more detailed about this features.

The results is sent on form of json structure with a simple list of data.

### Project Operation

The projection operation is used to limit the fields displayed in the research. It reduces the list of data to useful column only and must be used as soon as possible in the request in order to increase efficiency of the request.

columns fields are split with "," and will displays only columns mentioned.

### Render Operation

The rendering operation is used to display graph such as:
- bar graph
- line graph
- polar graph
- ... 

A json specific structure is used to indicates to the SIEM to display the result in a graph form and not a table form.

### Count Operation

The count operation is used to count a specific field and perform agregation of data. 

It is possible to agregate several fields in the same request in order to display counts depending on several fields. 

(**not implemented yet**). With the operation count, it will be possible to use count or sum or average by fields too.

### Transform Operation 

The transform operation will create temporary fields to perform transformation operation. 

Yet only the substring is available. 

This operation is also available on raw data and can help to perform operation and rendering with raw data by using (**future available transformation**) match regex to create a fields that can be used as columns.

### Variables Operation

The variable operation is used to create results that can be reused later in the request to perform operation on sets of data. 

Several variable can be used in the same researches. Be careful to limit the number of variables as variables is a full researches and can store all data in the result that can slow the entire research.

### Others (not implemented yet)

Other operations will be added in the application that let the user perform several others useful operations on the data and the results. 

## Reports and dashboards

Reports and dashboards are also type of research that pass through the SIEM search page and the ISM. 

Dashboards and reports are a set of queries that will be sent by the User Interface to display results in widgets. 

## Download documents

In the SIEM research, when a dashboard result is saved in the index, a specific format is used to store the data.

The ISM will create a link where the document can be download and it stores the data in memory to let the user download the document in a file format (csv, pdf, ...). 

Be careful to limit the number of document loaded in the request to avoid the memory capacity of variables, results and document.

## Session management

Each page and request uses a page id and the session of the user to segregate the data. However, if several users uses the same ISM, the memory can exceed the capacity of the physical machine and create unwanted behavior.

It is advised to segregated ISM and User Interface to limit this problem and monitor memory capacities of the machine with the infrastructure monitoring.

Widgets are stored in the same way of the SIEM page results.

Data display are often limited (in case of list of value) and data displayed are limited to 10 by default to limit the display memomry on the browser. 

However, all the data are stored in the memory of the ISM and ask for the next page will be faster with this system. 

Thus, all data:
- widgets results
- variables 
- documents
- researches users on differents pages
are stored in the same memory of the ISM identified by the current id unique.

## Check permissions

As all data are stored in the same memory, users permissions must be checked at each requests, even get page data. 

(**This feature must be tested more**)