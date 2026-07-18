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
document: widgets
*/

/**
 * Class Widget
 */
class Widget {
    constructor(config, container) {
        this.id = config.id;
        this.type = config.type;
        this.position = config.position || {left: 0, top: 0};
        this.size = config.size || {width: 50, height: 50};
        this.config = config.config;
        this.container = container;
        this.page_id = config.page_id;
        this.html = null;

        this.indices = (config.config?.index ?? "")
            .split(",")
            .map(item => item.trim())
            .filter(item => item.length > 0);

        this.tenants = (config.config?.tenant ?? "")
            .split(",")
            .map(item => item.trim())
            .filter(item => item.length > 0);

        this.technologies = (config.config?.technology ?? "")
            .split(",")
            .map(item => item.trim())
            .filter(item => item.length > 0);

        this.instance = (config.config?.instance ?? "");

        this.chartInstance = null; // store instance of chartjs if widget is a graph
    }

    // Render the dashboard layout
    render() {
        const dashboardZoneRect = this.container.getBoundingClientRect();
        const widgetElement = document.createElement("div");
        widgetElement.className = "widget";
        widgetElement.dataset.id = this.id;

        // Position & size
        const left = (this.position.left / 100) * dashboardZoneRect.width;
        const top = (this.position.top / 100) * dashboardZoneRect.height;
        const width = (this.size.width / 100) * dashboardZoneRect.width;
        const height = (this.size.height / 100) * dashboardZoneRect.height;

        Object.assign(widgetElement.style, {
            left: `${left}px`,
            top: `${top}px`,
            width: `${width}px`,
            height: `${height}px`,
            position: "absolute"
        });

        // Content
        const contentDiv = document.createElement("div");
        contentDiv.id = `content-${this.id}`;
        contentDiv.className = "widget-content";
        widgetElement.appendChild(contentDiv);

        if (this.type === "query") {
            const canvas = document.createElement("canvas");
            canvas.id = `canvas-${this.id}`;
            canvas.className = "widget-canvas";
            contentDiv.appendChild(canvas);
        }

        this.html = widgetElement;
        this.container.appendChild(widgetElement);
    }

    // Refresh the widget content depending on the widget type
    async refresh(startDate, endDate, indices, tenants, technologies, page_id) {
        const content = document.getElementById(`content-${this.id}`);

        if (this.type === "query") {
            await this.runQuery(startDate, endDate, this.indices, this.tenants, this.technologies, page_id);
        } else if(this.type === "soar") {
            await this.runQuerySOAR(this.indices[0], this.tenants[0], this.instance, page_id)
        } else if (this.type === "text") {
            content.textContent = this.config.content;
        } else if (this.type === "html") {
            content.innerHTML = this.config.content;
        } else if (this.type === "image") {
            content.innerHTML = `<img src="${this.config.content}" alt="widget image"/>`;
        } else if (this.type === "markdown") {
            content.innerHTML = simpleMarkdownToHTML(this.config.content);
        }
    }

    // Launch query and render results
    async runQuery(startDate, endDate, indices, tenants, technologies, page_id) {
        const query = this.config.command;
        const current_id = page_id + "-" + this.id;

        try {
            const response = await fetch("query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    startTime: startDate,
                    endTime: endDate,
                    index: this.indices,
                    tenant: this.tenants,
                    technology: this.technologies,
                    page_id: current_id
                }),
            });

            const result = await response.json();
            console.log("Query result for widget", this.id, result);
            if (!result) return;

            if (result.type === "graph") {
                const containerId = "canvas-" + this.id;
                const canvas = document.getElementById(containerId);

                if (!canvas) {
                    console.error("Canvas not found for widget:", this.id);
                    return;
                }

                // Destroy old graphic to avoid error Chart.js
                if (this.chartInstance) {
                    this.chartInstance.destroy();
                }

                const graph = new Graph(containerId);
                this.chartInstance = graph.drawChart(result.data, result.graph_type);
            } else if (result.type === "table") {
                const containerId = `canvas-${this.id}`;
                const existingCanvas = document.getElementById(containerId);
                if (existingCanvas) existingCanvas.remove();

                const table = new TableManager(this.id, "/get_page", page_id);
                table.initDataTable(result.data, result.fields || null);
            }
        } catch (error) {
            console.error(`Error querying widget ${this.id}:`, error);
        }
    }

    // Launch query on SOAR and render results
    async runQuerySOAR(indices, tenants, instance, page_id) {
        console.log("runQuerySOAR");
        console.log(this.playbook);
        const query = this.config.command;
        const current_id = `${page_id}-${this.id}`;

        try {
            const response = await fetch("soar_command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: 0,
                    command: query.replace(/&quot;/g, '"'),
                    index: this.indices[0],
                    tenant: this.tenants[0],
                    vault: this.instance,
                    playbook_mode: this.playbook,
                    display: true,
                    page_id: current_id, 
                    history: this.id
                }),
            });

            const result = await response.json();
            console.log("Query result for widget", this.id, result);
            if (!result || !result.history) return;

            // Main container selector
            const containerId = `content-${this.id}`;
            const container = document.getElementById(containerId);
            if (!container) {
                console.error("Container not found for widget:", this.id);
                return;
            }

            // Empty container before add new cards
            container.innerHTML = "";

            // Create a SOAR card for each elements from the history 
            result.history.forEach(entry => {
                // Keep only last answer
                entry.answer = entry.answer?.at(-1);

                console.log(`Creation SOAR Card for entry ${entry.id}`);
                var card = null;

                console.log("Card details:");
                console.log(card);
                console.log(entry.answer);

                // Editable widget if table
                if (entry.answer) {
                    var answer = JSON.parse(entry.answer);
                    var new_card = entry;
                    if (answer.type === "table") {
                        console.log("Adding editable table widget");
                        answer.type = "editable_table";
                        new_card.answer = JSON.stringify(answer);
                        card = new SOARCard(new_card, true).render();
                    }
                    else {
                        card = new SOARCard(entry, false).render();
                    }
                }
                else {
                    card = new SOARCard(entry, true).render();
                }

                // Add card to the main container
                container.appendChild(card);
            });

        } catch (error) {
            console.error(`Error querying widget ${this.id}:`, error);
        }
    }


}

