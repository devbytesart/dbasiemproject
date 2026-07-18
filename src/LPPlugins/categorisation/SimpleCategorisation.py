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
project: siem project
DOCUMENT: simple categorization

"""

from LPCategorizerInterface import LPCategorizerInterface
import traceback

class SimpleCategorisation(LPCategorizerInterface):
    def categorize(self, data, logger):
        try:
            # Take in parameter a json of key value to add the categorisation in the logs
            #EXTERNALID AUTHENTICATION
            self.add_category(data, "externalId", "4624", "catBehavior", "Authentication", logger)
            self.add_category(data, "externalId", "4625", "catBehavior", "Authentication", logger)
            self.add_category(data, "externalId", "4672", "catBehavior", "Privilege", logger)
            self.add_category(data, "externalId", "4688", "catBehavior", "Process", logger)
            self.add_category(data, "externalId", "4634", "catBehavior", "Account", logger)
            # TODO: to continue the list
            return data
        except:
            logger.log("error", f"Error while categorizing log: {traceback.format_exc()}")
            return data
    
        

