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
document: soarcard

*/

class ResultInterpreter {
    constructor(result, containerId, flaskEndpoint = null, pageId = null, instance = null) {
        this.rawResult = result;
        this.containerId = containerId;
        this.flaskEndpoint = flaskEndpoint;
        this.pageId = pageId;
        this.instance = instance;
        this.interpret();
    }

    interpret() {
        // Report execution to ensure DOM is ready
        setTimeout(() => {
            let parsed;

            try {
                console.log("Before Parsing JSON:", this.rawResult);

                // If entry is already an object (and not null), using directly
                if (this.rawResult && typeof this.rawResult === 'object') {
                    console.log("already object json");
                    parsed = this.rawResult;
                } else if (typeof this.rawResult === 'string') {
                    // Entry link
                    try {
                        const siemMatch = this.rawResult.match(/siem_linktype\/url:(\S+)/);
                        if (siemMatch) {
                            return this.createLink(siemMatch[1]);
                        }
                    } catch (err) {
                        console.log("Not Link");
                    }
                    // Else parse JSON
                    try {
                        parsed = JSON.parse(this.rawResult);
                    } catch (err) {
                        console.log("Not JSON - send raw");
                        return this.displayRaw(this.rawResult);
                    }
                } else {
                    throw new Error("Unsupported rawResult type");
                }
            } catch (e) {
                console.error("Error parsing JSON:", e);
                return this.displayRaw(this.rawResult);
            }

            // Specific case depending on the JSON structure
            if (parsed && typeof parsed === 'object') {
                if (parsed.hasOwnProperty("soar_url")) {
                    this.createLink(parsed["soar_url"]);
                } else if(parsed.hasOwnProperty("soar_dashboard")) {
                    this.createDashboard(parsed);
                } else if (parsed.type === "table") {
                    const uniqueId = `table-${Math.random().toString(36).substr(2, 6)}`;
                    this.createTable(parsed, uniqueId);
                } else if(parsed.type === "editable_table") {
                    const uniqueId = `editable-table-${Math.random().toString(36).substr(2, 6)}`;
                    this.createEditableTable(parsed, uniqueId, this.instance);
                } else if (parsed.type === "graph") {
                    const canvasId = `graph-${Math.random().toString(36).substr(2, 6)}`;
                    this.createGraph(parsed, canvasId);
                } else {
                    console.log("displayJSON", parsed);
                    // JSON classic
                    this.displayJson(parsed);
                }
            } else {
                console.log("displayRaw in else");
                // Not an object (string, number, etc.)
                this.displayRaw(parsed);
            }
        }, 0); 
        // Async execution after insertion DOM
    }

    createLink(url) {
        const isAbsolute = /^(http|https):\/\//.test(url);
        const fullUrl = isAbsolute ? url : `${window.location.origin}${url}`;
        const linkElement = document.createElement("a");
        linkElement.href = fullUrl;
        linkElement.textContent = fullUrl;
        linkElement.target = "_blank";

        this.clearContainer();
        document.getElementById(this.containerId).appendChild(linkElement);
    }

    createTable(tableData, uniqueId) {
        const container = document.getElementById(this.containerId);
        const tableContainer = document.createElement("div");
        tableContainer.id = `content-${uniqueId}`;
        container.appendChild(tableContainer);

        const tableManager = new TableManager(uniqueId, this.flaskEndpoint, this.pageId);
        tableManager.initDataTable(tableData.data, tableData.fields || null);
    }

    createGraph(graphData, canvasId) {
        const container = document.getElementById(this.containerId);
        const canvas = document.createElement("canvas");
        canvas.id = canvasId;
        container.appendChild(canvas);

        const graph = new Graph(canvasId);
        graph.drawChart(graphData.data, graphData.graph_type || "bar");
    }

    createDashboard(dashboardData) {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with id '${this.containerId}' not found.`);
            return;
        }

        // Extract data
        const data = dashboardData.soar_dashboard;
        if (!data) {
            console.error("Invalid dashboardData: missing 'soar_dashboard' property.");
            return;
        }

        // Create dynamically dashboard container
        const dashboardZoneId = data.dashboard_zone || `dashboard-zone-${Math.floor(Math.random() * 1000000)}`;
        const dashboardDiv = document.createElement("div");
        dashboardDiv.id = dashboardZoneId;
        dashboardDiv.className = "dashboard-zone";
        dashboardDiv.style.minHeight = "500px";
        container.appendChild(dashboardDiv);

        // Create and launch dashboard manager
        const dashboardManager = new DashboardManager({
            index: data.index || "",
            tenant: data.tenant || "",
            technology: data.technology || "",
            dashboard: data.dashboard || "",
            dashboard_zone_id: dashboardZoneId,
            refresh_time: data.refresh || 30,
            limit: data.limit || 10,
            legend: data.legend ?? true,
            label: data.label ?? true,
            startDate: data.start || "1970-01-01 00:00:00",
            endDate: data.end || "2500-01-01 00:00:00"
        });

        dashboardManager.init();
        dashboardManager.refreshDashboard();

        console.log(`Dashboard "${data.dashboard}" launched in #${dashboardZoneId}.`);
    }


    displayRaw(content) {
        const container = document.getElementById(this.containerId);
        this.clearContainer();
        const pre = document.createElement("pre");
        pre.textContent = (typeof content === "string") ? content : JSON.stringify(content, null, 2);
        container.appendChild(pre);
    }

    clearContainer() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = "";
        }
    }

    displayJson(data) {
        const container = document.getElementById(this.containerId);
        this.clearContainer();
        const JSONContainer = document.createElement("div");
        JSONContainer.innerHTML = renderJsonAsExpandableHtml(data);
        container.appendChild(JSONContainer); 
    }

    createEditableTable(tableData, uniqueId, instance) {
        const container = document.getElementById(this.containerId);
        const tableContainer = document.createElement("div");
        tableContainer.id = `content-${uniqueId}`;
        container.appendChild(tableContainer);

        const tableEl = document.createElement("table");
        tableEl.id = `editable-table-${uniqueId}`;
        tableEl.className = "display editable-table w-full";
        tableContainer.appendChild(tableEl);

        // Wait insertion DOM before init dataTable
        setTimeout(() => {
            const headers = Object.keys(tableData.data[0] || {});
            const columns = headers.map(h => ({ title: h, data: h }));

            const table = $(tableEl).DataTable({
                data: tableData.data,
                columns,
                paging: true,
                searching: false,
                info: false,
                autoWidth: true,
            });

            // Manage direct edition
            // Gestion de l'édition directe
            $(tableEl).on("click", "tbody td", function () {
                const cell = table.cell(this);
                const colName = table.column(this).dataSrc();
                if (colName === "id") return;

                const originalValue = cell.data();
                $(this).attr("contenteditable", true).focus();

                $(this).one("blur", async function () {
                    const newValue = $(this).text().trim();
                    $(this).removeAttr("contenteditable");

                    if (newValue === originalValue) return;

                    // Update local model
                    cell.data(newValue).draw(false);
                    const rowData = table.row(this).data();
                    rowData[colName] = newValue;

                    // Visual Feedback
                    $(this).css("background-color", "#d4edda");
                    setTimeout(() => $(this).css("background-color", ""), 600);

                    // Create the content
                    var command = "siem_modify_log";
                    command += " instance=" + instance;
                    command += " index=" + rowData.index;
                    command += " tenant=" + rowData.tenant;
                    command += " technology=" + rowData.technology;
                    command += " id=" + rowData.id;
                    command += " data=" + JSON.stringify(rowData);

                    // Save with soar command 
                    try {
                        const response = await fetch("soar_command", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                command: command,
                                widget_id: uniqueId,
                                // data: rowData,
                                index: Math.floor(Math.random() * 10000000),
                                tenant: Math.floor(Math.random() * 10000000),
                                vault: instance,
                                technology: null,
                                display: false
                            }),
                        });

                        if (!response.ok) throw new Error(await response.text());
                        console.log(`✔️ Modification saved : ${colName} = ${newValue}`);
                    } catch (err) {
                        console.error("❌ Error during saving:", err);
                        $(this).css("background-color", "#f8d7da");
                        setTimeout(() => $(this).css("background-color", ""), 800);
                    }
                });
            });
        }, 0);
    }


}