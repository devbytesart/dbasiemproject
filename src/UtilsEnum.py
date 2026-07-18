"""
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
title: siem project
document: utilitaires
"""

from enum import Enum

class SIEM_SEARCH_FORMAT(Enum):
    """Format of the result for search request:
    result = {
        "type":"table|graph|...", 
        "data":[table of data], 
        "fields":[list of fields to display],
        "errors":[list of error],
        "warnings":[list of warnings],
        "indices":[list of incides for search],
        "tenants":[list of tenants for search],
        "technologies":[list of technologies for search],
        "request":"request for the result",
        "variables":{variables format}
    }
    return default value modifiable
    # TO UPDATE -> must copy in a variable and change the variable
    """
    result = {
            "type":"table",
            "data":[],
            "fields":[],
            "errors":[],
            "warnings":[],
            "indices":[],
            "tenants":[],
            "technologies":[],
            "request":[],
            "variables":{}
        }

class SIEM_Field_Format(Enum):
    """ Format class used on the siem to store file, image, base64..."""
    file = "filetype"
    image = "imagetype"
    link = "siem_linktype"
    # TODO to be completed

class SIEM_File_Type(Enum):
    """ Format used to define the type of file format"""
    pdf = "pdf"
    csv = "csv"
    jpg = "jpg"
    png = "png"
    html = "html"
    markdown = "md"
    url = "url"
    # TODO to be completed

class SIEM_Report_MAX_COLUMNS(Enum):
    """ Max columns for report """
    portrait = 10
    landscape = 15
    # TODO to be completed