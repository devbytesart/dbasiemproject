/*

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
document: dashboard
*/

/* ============================
   GLOBAL INITIALISATION
============================ */

document.addEventListener("DOMContentLoaded", () => {
    const dashboardManager = new DashboardManager({
        dashboard_zone_id: "dashboard-zone"
    });

    const tagInputSystem = new TagsSystem([
        {
            "name": "Index",
            "id": "selectindex",
            "paramUrl": "index",
            "url": "/search_available_index",
            "params": {},
            "method": "GET",
            "multiple": false,
            "last": false,
        },
        {
            "name": "Tenant",
            "id": "selecttenant",
            "paramUrl": "tenant",
            "url": "/search_available_tenant",
            "params": {},
            "method": "GET",
            "multiple": false,
            "last": false,
        },
        {
            "name": "Technology",
            "id": "selecttechnology",
            "paramUrl": "technology",
            "url": null,
            "params": {},
            "method": "GET",
            "multiple": false,
            "last": false,
        },
        {
            "name": "Dashboard",
            "id": "selectdashboard",
            "paramUrl": "dashboard",
            "url": "/get_dashboard_list",
            "params": {},
            "method": "POST",
            "multiple": false,
            "last": true
        }
    ], () => dashboardManager.refreshDashboard(), dashboardManager.page_id);

    tagInputSystem.tags["Technology"].setSelectedValues("template_dashboard");
    tagInputSystem.tags["Technology"].disable();

    // Callback during change of TagSystem
    tagInputSystem.onChange = (newValues) => dashboardManager.handleTagSystemChange(newValues);

    tagInputSystem.init();
    dashboardManager.init(tagInputSystem);
});
