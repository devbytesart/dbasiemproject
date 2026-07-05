/*

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
title: siem project
document: dashboard_class
*/

class DashboardManager {
    constructor({
        index = "",
        tenant = "",
        technology = "",
        dashboard = "",
        dashboard_zone_id = `dashboard-${Math.floor(Math.random() * 1000000)}`,
        refresh_time = 30,
        limit = 10,
        legend = true,
        label = true,
        startDate = "1970-01-01 00:00:00",
        endDate = "2500-01-01 00:00:00",
    }) {
        this.index = index;
        this.tenant = tenant;
        this.technology = technology;
        this.dashboard = dashboard;
        this.dashboard_zone_id = dashboard_zone_id;
        this.refresh_time = refresh_time;
        this.limit = limit;
        this.legend = legend;
        this.label = label;
        this.startDate = startDate;
        this.endDate = endDate;
        this.page_id = Math.floor(Math.random() * 10000000000);

        this.old_datawidget = null;
        this.widgets = [];
        this.refreshTimer = null;

        this.dashboardZone = document.getElementById(this.dashboard_zone_id);
    }

    /**
     * Initi dashboard and tag system
     */
    init(tagInputSystem) {
        this.tagInputSystem = tagInputSystem;
        this.bindEvents();
        this.startAutoRefresh();
    }

    /**
     * Refresh dashboard
     */
    refreshDashboard() {
        const startDate = this.startDate;
        const endDate = this.endDate;

        let dashboard, indices, tenants, technologies;

        // If tagInputSystem is defined, get values from it
        if (this.tagInputSystem) {
            // Get raw values
            dashboard = this.tagInputSystem.getSelectedValue("Dashboard");
            indices = this.tagInputSystem.getSelectedValue("Index");
            tenants = this.tagInputSystem.getSelectedValue("Tenant");
            technologies = this.tagInputSystem.getSelectedValue("Technology");
        }
        // Else, use values from the constructor
        else {
            dashboard = this.dashboard;
            indices = this.index;
            tenants = this.tenant;
            technologies = this.technology;
        }

        fetch("/refresh_dashboard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                startDate,
                endDate,
                indices,
                tenants,
                technologies,
                dashboard,
                page_id: this.page_id
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            data.widgets = JSON.parse(data.widgets);

            // Render only if data changed
            if (JSON.stringify(this.old_datawidget) !== JSON.stringify(data.widgets)) {
                this.old_datawidget = data.widgets;
                this.renderDashboard(data.widgets);
            }

            // Refresh each widgets with current values
            this.widgets.forEach(widget => {
                widget.refresh(startDate, endDate, indices, tenants, technologies, this.page_id);
            });
        })
        .catch(error => console.error("Error refreshing dashboard:", error));
    }

    /**
     * Display widgets in the dashboard zone
     */
    renderDashboard(widgetsData) {
        console.log("Render dashboard");
        if (!this.dashboardZone) return;
        this.dashboardZone.innerHTML = "";
        this.widgets = widgetsData.map(config => {
            const widget = new Widget(config, this.dashboardZone);
            widget.render();
            return widget;
        });
    }

    /**
     * Refresh automatic of dashboard
     */
    startAutoRefresh() {
        if (this.refreshTimer) clearInterval(this.refreshTimer);
        this.refreshTimer = setInterval(() => this.refreshDashboard(), this.refresh_time * 1000);
    }

    /**
     * Manage events (button refresh and intervalle, etc)
     */
    bindEvents() {
        const refreshButton = document.getElementById("refresh-dashboard");
        const refreshIntervalInput = document.getElementById("refresh-interval");

        if (refreshButton) {
            refreshButton.addEventListener("click", () => this.refreshDashboard());
        }

        if (refreshIntervalInput) {
            refreshIntervalInput.addEventListener("input", () => {
                const newInterval = parseInt(refreshIntervalInput.value, 10);
                this.refresh_time = newInterval > 0 ? newInterval : this.refresh_time;
                this.startAutoRefresh();
            });
        }
    }

    /**
     * Refresh dashboard only if one critical parameter changes
     */
    handleTagSystemChange(newValues) {
        let needRefresh = false;

        ["index", "tenant", "technology", "dashboard"].forEach(param => {
            if (this[param] !== newValues[param]) {
                this[param] = newValues[param];
                needRefresh = true;
            }
        });

        if (needRefresh) {
            console.log("Tag system change detected — refreshing dashboard...");
            this.refreshDashboard();
        }
    }
}
