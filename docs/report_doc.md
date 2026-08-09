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
DOCUMENT: report doc
-->

# Report Tutorial

Report are an important part for a SIEM. In this application, it is possible to create the report from the Edition page.
Find documentation to create dashboards and reports template on the page [Report template](./edition_doc).

## Prerequisites

In order to create a report, it is required to:
- have created the template on the Edition.
- have the name of the template.
- have a instance key with rights permissions to generate the report
- have the location of the report (index and tenant)


## Generate the report and download it

In order to generate the report, use the following command:
´´´
siem_generate_report index=<index> tenant=<tenant> instance=<instance> name=<name of the new template> template_name=<template_name>
´´´
Those are the minimum requirements for the parameters.

Depending on the parameters raw, the results can be showed as url to download the report or raw in hexadecimal to save the report from text to file.

The generation of the report is saved on logs (if the parameters save is true which is the default value), it is possible to find the download link direcly from the search view with searching the name of the report on the right tenant and index.

**A new download link is generated at each researches.**

