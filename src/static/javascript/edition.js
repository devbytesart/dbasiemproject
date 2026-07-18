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
document: edition
*/

const MOV_RES_STEP = 20;

// var indices;
// var tenants;
// var technologies;
// var dateStartInput;
// var dateEndInput;
var page_id;
// var dashboardTypeInput = "dashboard";
// var dashboardNameInput;
// var reportFormat;
let tagInputSystem;


document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const form = document.getElementById("config-form");
    // dashboardNameInput = document.getElementById("dashboard-name");
    // const dashboardTypeInput = document.getElementById("dashboard-type");


    const saveDashboardButton = document.getElementById("save-dashboard");
    // const saveReportButton = document.getElementById("save-report");
    const isreport = document.getElementById("isreport");

    // const generateReport = document.getElementById("generate-report");
    let selectedWidget = null;

    page_id = Math.floor(Math.random() * 10000000000)

    // Launch TagSystem
    tagInputSystem = new TagsSystem([
        {
            "name": "Index",
            "id": "selectindex",
            "paramUrl": "index",
            "url": "/search_available_index",
            "params": {},
            "method": "GET",
            "multiple": false,
            "last": false
        },
        {
            "name": "Tenant",
            "id": "selecttenant",
            "paramUrl": "tenant",
            "url": "/search_available_tenant",
            "params": {},
            "method": "GET",
            "multiple": false,
            "last": false
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
            "enable": false
        },
        {
            "name": "Dashboard",
            "id": "selectdashboard",
            "paramUrl": "dashboard",
            "url": "/get_dashboard_list",
            "params": {
                "index": "",
                "tenant": "",
                "technology": "",
                "page_id":page_id
            },
            "method": "POST",
            "multiple": false,
            "last": true
        }
    ], loadDashboard, page_id)
    tagInputSystem.init();

    // Drag-and-drop logic
    document.querySelectorAll(".widget-edit").forEach(widget => {
        widget.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("widget-type", e.target.dataset.type);
        });
    });

    dropZone.addEventListener("dragover", (e) => e.preventDefault());

    // IS REPORT 
    tagInputSystem.tags["Technology"].setSelectedValues("template_dashboard");
    isreport.addEventListener("change", (event) => {
        // event.target.checked vaut true si la case est cochée, false sinon
        const value = event.target.checked ? "template_report" : "template_dashboard";
        // On passe la valeur dans un tableau puisque setSelectedValues attend généralement une liste
        tagInputSystem.tags["Technology"].setSelectedValues(value);
        loadDashboard();
    });
    tagInputSystem.tags["Technology"].disable();

    function addWidgetToDropZone(widgetData, dropZone, e) {
        let widgetInstance;

        console.log(widgetData);

        if (e) {
            // Cas 1 : New widget (Drag & Drop)
            let config = {};
            config.className = "widget-edit";
            config.id = `widget-${Date.now()}`;
            config.type = widgetData.type || "text";
            config.name = `widget-${Date.now()}`;
            config.index = "";
            config.tenant = "";
            config.technology = "";
            config.instance = "";
            config.playbook = false;
            config.start = "2000-01-01 00:00:00";
            config.end = "2500-01-01 00:00:00";

            config.config = {
                id: config.id,
                type: config.type,
                name: config.name,
                index: config.index,
                tenant: config.tenant,
                technology: config.technology,
                start: config.start,
                end: config.end,
                instance: config.instance,
                playbook: config.playbook,
                command: ""
            };

            widgetInstance = new Widget(config, dropZone);
            console.log("Creation new widget");
            console.log(widgetInstance);
        } else {
            // Cas 2 : Widget existing (Reload)
            widgetInstance = new Widget(widgetData, dropZone);
        }

        // Position widget
        if(e) {
            // Comput relative position in pixels compared to dropzone edge
            const relativeX = e.clientX - dropZone.getBoundingClientRect().left;
            const relativeY = e.clientY - dropZone.getBoundingClientRect().top;

            // Convert percentage (divide total width and multiplie by 100)
            widgetInstance.position.left = (relativeX / dropZone.offsetWidth) * 100;
            widgetInstance.position.top = (relativeY / dropZone.offsetHeight) * 100;

            // Optional : Limit value from 0 to 100 to avoid exit
            widgetInstance.position.left = Math.max(0, Math.min(100, widgetInstance.position.left));
            widgetInstance.position.top = Math.max(0, Math.min(100, widgetInstance.position.top));
        }

        // const widgetEl = widgetInstance.render();
        widgetInstance.render();
        widgetInstance.html._widgetInstance = widgetInstance;

        // Resize handle
        const resizeHandle = document.createElement("div");
        resizeHandle.className = "resize-handle";
        resizeHandle.textContent = "↔";
        widgetInstance.html.appendChild(resizeHandle);

        // Delte button
        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-button";
        deleteButton.textContent = "X";
        deleteButton.style.position = "absolute";
        deleteButton.style.right = "0";
        deleteButton.style.top = "0";
        widgetInstance.html.appendChild(deleteButton);

        enableWidgetFeatures(widgetInstance);
    }

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    const type = e.dataTransfer.getData("widget-type");
    if (type) {
        // Pass only type, function addWidgetToDropZone will complete the rest
        addWidgetToDropZone({ type: type }, dropZone, e);
    }
    else {
        console.log("No type");
    }
});



function enableWidgetFeatures(widget) {
    // Define "el" to reduce the code and be sure to target the html
    const el = widget.html;

    // --- 1. Moving ---
    el.addEventListener("mousedown", (e) => {
        // Security : Don't move if click on button or resize handle
        if (e.target.classList.contains("resize-handle") || e.target.tagName === "BUTTON") return;
        
        const startX = e.clientX;
        const startY = e.clientY;
        
        // Get positions
        const startLeft = parseInt(el.style.left, 10) || 0;
        const startTop = parseInt(el.style.top, 10) || 0;

        function moveWidget(ev) {
            const deltaX = Math.floor((ev.clientX - startX) / MOV_RES_STEP) * MOV_RES_STEP;
            const deltaY = Math.floor((ev.clientY - startY) / MOV_RES_STEP) * MOV_RES_STEP;

            const newLeft = startLeft + deltaX;
            const newTop = startTop + deltaY;

            // Apply styles and el.style and use el.offsetWidth
            el.style.left = `${Math.max(0, Math.min(newLeft, dropZone.offsetWidth - el.offsetWidth))}px`;
            el.style.top = `${Math.max(0, Math.min(newTop, dropZone.offsetHeight - el.offsetHeight))}px`;
        }

        function stopMove() {
            document.removeEventListener("mousemove", moveWidget);
            document.removeEventListener("mouseup", stopMove);
        }

        document.addEventListener("mousemove", moveWidget);
        document.addEventListener("mouseup", stopMove);
    });

    // --- 2. Resizing ---
    const handle = el.querySelector(".resize-handle");
    if (handle) {
        handle.addEventListener("mousedown", (e) => {
            e.preventDefault();
            const startX = e.clientX;
            const startY = e.clientY;
            const startWidth = parseInt(el.style.width, 10) || 100;
            const startHeight = parseInt(el.style.height, 10) || 100;

            function resizeWidget(ev) {
                const deltaX = Math.floor((ev.clientX - startX) / MOV_RES_STEP) * MOV_RES_STEP;
                const deltaY = Math.floor((ev.clientY - startY) / MOV_RES_STEP) * MOV_RES_STEP;

                const newWidth = startWidth + deltaX;
                const newHeight = startHeight + deltaY;

                // Using el.style to read coordinates 
                const currentLeft = parseInt(el.style.left, 10) || 0;
                const currentTop = parseInt(el.style.top, 10) || 0;

                el.style.width = `${Math.max(50, Math.min(newWidth, dropZone.offsetWidth - currentLeft))}px`;
                el.style.height = `${Math.max(50, Math.min(newHeight, dropZone.offsetHeight - currentTop))}px`;
            }

            function stopResize() {
                document.removeEventListener("mousemove", resizeWidget);
                document.removeEventListener("mouseup", stopResize);
            }

            document.addEventListener("mousemove", resizeWidget);
            document.addEventListener("mouseup", stopResize);
        });
    }

    // --- 3. Selection (Click) ---
    el.addEventListener("click", () => {
        selectedWidget = widget; // Store entire object 

        const config = widget.config; 
        
        form.innerHTML = generateFormFields(config.type);
        // Complete form
        form["widget-id"].value = config.id || "";
        if(form["widget-name"]) {
            form["widget-name"].value = config.name || "";
        }
        if(form["widget-index"]) {
            form["widget-index"].value = config.index || "";
        }
        if(form["widget-tenant"]) {
            form["widget-tenant"].value = config.tenant || "";
        }
        if(form["widget-technology"]) {
            form["widget-technology"].value = config.technology || "";
        }
        if(form["widget-start"]) {
            form["widget-start"].value = config.start || "";
        }
        if(form["widget-end"]) {
            form["widget-end"].value = config.end || "";
        }
        if(form["widget-instance"]) {
            form["widget-instance"].value = config.instance || "";
        }
        if(form["widget-playbook"]) {
            form["widget-playbook"].value = config.playbook || "";
        }
        if(config.type === "query" || config.type === "soar") {
            form["command"].innerHTML = config.command || "";
        }
        else if(config.type === "text") {
            form["content"].innerHTML = config.content || "";
        }
    });

    // --- 4. Deletion ---
    const delBtn = el.querySelector(".delete-button");
    if (delBtn) {
        delBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Avoid selection widget when deletion
            
            // Call remove() if class widget has it
            if (typeof widget.remove === "function") {
                widget.remove(); 
            } else {
                // Else, delete HTML and clean
                widget.html.remove();
                widget = null;
            }
        });
    }
}

    // Generate form fields based on widget type
    function generateFormFields(type) {
        if (type === "query") {
            return `
            <form id="config-form">
                <label>Widget ID: <input name="widget-id" readonly/></label>
                <br/>
                <label>Widget Name: <input name="widget-name" /></label>
                <br/>
                <label>Indices:<input name="widget-index" /></label>
                <br/>
                <label>Tenants:<input name="widget-tenant" /></label>
                <br/>
                <label>Technologies:<input name="widget-technology" /></label>
                <br/>
                <label>Start:<input type="datetime" name="widget-start" /></label>
                <br/>
                <label>End:<input type="datetime" name="widget-end" /></label>
                <br/>
                <label>Command: <br/><textarea name="command" /></textarea></label>
            </form>
            `;
        }
        else if (type === "text") {
            return `
            <form id="config-form">
                <label>Widget ID: <br/><input name="widget-id" readonly/></label>
                <br/>
                <label>Content: <br/><textarea name="content"></textarea></label>
            </form>
            `
        }
        else if (type === "image") {
            return `
            <form id="config-form">
                <label>Widget ID: <br/><input name="widget-id" readonly/></label>
                <br/>
                <label>Widget Name: <br/><input name="widget-name" /></label>
                <br/>
                <label>Image URL: <br/><textarea name="content" /></textarea></label>
            </form>
            `
        }
        else if (type === "markdown") {
            return `
            <form id="config-form">
            <label>Widget ID: <br/><input name="widget-id" readonly/></label>
            <br/>
            <label>Widget Name: <br/><input name="widget-name" /></label>
            <br/>
            <label>Markdown Content: <br/><textarea name="content"></textarea></label>
            </form>
            `
        }
        else if(type === "soar") {
            return `
            <form id="config-form">
                <label>Widget ID: <input name="widget-id" readonly/></label>
                <br/>
                <label>Widget Name: <input name="widget-name" /></label>
                <br/>
                <label>Indices:<input name="widget-index" /></label>
                <br/>
                <label>Tenants:<input name="widget-tenant" /></label>
                <br/>
                <label>Instance:<input name="widget-instance" /></label>
                <br/>
                <label>Playbook:<input type="checkbox" name="widget-playbook" /></label>
                <br/>
                <label>Command: <br/><textarea name="command" /></textarea></label>
            </form>
            `
        }
        // Add more conditions for other widget types if needed
        return `<p>No configuration required for this widget.</p>`;
    }

form.addEventListener("input", () => {
    if (!selectedWidget) return;

    // Update object directly
    const cfg = selectedWidget.config;

    cfg.name       = form.querySelector("[name='widget-name']")?.value ?? cfg.name;
    cfg.index      = form.querySelector("[name='widget-index']")?.value ?? cfg.index;
    cfg.tenant     = form.querySelector("[name='widget-tenant']")?.value ?? cfg.tenant;
    cfg.technology = form.querySelector("[name='widget-technology']")?.value ?? cfg.technology;
    cfg.instance   = form.querySelector("[name='widget-instance']")?.value ?? cfg.instance;
    cfg.playbook   = form.querySelector("[name='widget-playbook']")?.checked ?? cfg.playbook;
    cfg.start      = form.querySelector("[name='widget-start']")?.value ?? cfg.start;
    cfg.end        = form.querySelector("[name='widget-end']")?.value ?? cfg.end;
    cfg.command    = form.querySelector("[name='command']")?.value ?? cfg.command;
    cfg.content    = form.querySelector("[name='content']")?.value ?? cfg.content;

    // Sync attribute parsing (indices, tenant, technologies)
    selectedWidget.indices     = (cfg.index ?? "").split(",").map(s => s.trim()).filter(Boolean);
    selectedWidget.tenants     = (cfg.tenant ?? "").split(",").map(s => s.trim()).filter(Boolean);
    selectedWidget.technologies = (cfg.technology ?? "").split(",").map(s => s.trim()).filter(Boolean);
    selectedWidget.instance    = cfg.instance ?? "";
    selectedWidget.playbook    = cfg.playbook ?? false;
});

    function saveLayout({ dropZone, nameInput, typeInput, pageId, url }) {
        // Get dimensions and positions of drop zone
        const dropZoneRect = dropZone.getBoundingClientRect();

        // Extract widgets and compute position and size in percentage
        const widgets = Array.from(dropZone.querySelectorAll(".widget")).map(widget => {
            const widgetRect = widget.getBoundingClientRect();

            // Compute percentage relative to drop zone
            const leftPercent = Math.floor(((widgetRect.left - dropZoneRect.left) / dropZoneRect.width) * 100);
            const topPercent = Math.floor(((widgetRect.top - dropZoneRect.top) / dropZoneRect.height) * 100);
            const widthPercent = Math.floor((widgetRect.width / dropZoneRect.width) * 100);
            const heightPercent = Math.floor((widgetRect.height / dropZoneRect.height) * 100);


        const instance = widget._widgetInstance;
        if (!instance) return null;

        return {
            id: instance.id,
            type: instance.type,
            position: { left: leftPercent, top: topPercent },
            size: { width: widthPercent, height: heightPercent },
            config: instance.config,   
            name: instance.config?.name,
        };

        });

        // Build object to save 
        const payload = {
            name: tagInputSystem.getSelectedValue("Dashboard"),
            index: tagInputSystem.getSelectedValue("Index"),
            tenant: tagInputSystem.getSelectedValue("Tenant"),
            technology: tagInputSystem.getSelectedValue("Technology"),
            widgets: widgets,
            type: typeInput,
            page_id: pageId
        };

        // Send saving request
        fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
        .then(response => response.json())
        .then(data => {
                alert(JSON.stringify(data, null, 2));
            }
        )
        .catch(error => console.error("Error saving:", error));
    }

    // Listener for dashboard
    saveDashboardButton.addEventListener("click", () => {
        let _url = "/save_dashboard";
        let _type = "dashboard_template";
        if(isreport.checked) {
            _url = "/save_report";
            _type = "report_template";
        }
        saveLayout({
            dropZone: dropZone,
            nameInput: tagInputSystem.getSelectedValue("Dashboard"),
            typeInput: _type,
            pageId: page_id,
            url: _url
        });
    });

    // // Listener for report
    // saveReportButton.addEventListener("click", () => {
    //     saveLayout({
    //         dropZone: dropZone,
    //         nameInput: dashboardNameInput, 
    //         typeInput: dashboardTypeInput, 
    //         pageId: page_id,
    //         url: "/save_report"
    //     });
    // });

    // const tabButtons = document.querySelectorAll(".tab-button");
    // const tabContents = document.querySelectorAll(".tab-content");

    // tabButtons.forEach(button => {
    //     button.addEventListener("click", function () {
    //         tabButtons.forEach(btn => btn.classList.remove("active"));
    //         tabContents.forEach(tab => tab.style.display = "none");

    //         this.classList.add("active");
    //         document.getElementById(this.dataset.target).style.display = "block";

    //         dashboardTypeInput = this.outerText.toLowerCase();
    //         console.log(dashboardTypeInput);
    //     });
    // });

function loadDashboard() {
    let _techno = "template_dashboard"
    if(isreport.checked) {
        _techno = "template_report"
    }
    const index = tagInputSystem.getSelectedValue("Index");
    const tenant = tagInputSystem.getSelectedValue("Tenant");
    const technology = _techno;
    const dashboard = tagInputSystem.getSelectedValue("Dashboard");
    const startDate = "1970-01-01 00:00:00";
    const endDate = "2500-01-01 00:00:00";

    fetch("/refresh_dashboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            startDate, endDate,
            indices: index,
            tenants: tenant,
            technologies: technology,
            dashboard, page_id
        }),
    })
    .then(response => response.json())
    .then(data => {
        dropZone.innerHTML = ""; // Clean zone before loading
        const widgetsData = typeof data.widgets === "string" ? JSON.parse(data.widgets) : data.widgets;

        widgetsData.forEach(wData => {
            addWidgetToDropZone(wData, dropZone);
        });
    });
}

});


