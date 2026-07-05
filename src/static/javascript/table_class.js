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
document: table class
*/

class TableManager {
    constructor(uniqueId, flaskEndpoint, page_id) {
        this.uniqueId = uniqueId; // Unique identifier for each table
        this.uniqueIdSelector = "content-" + uniqueId; // Unique selector for the table
        this.flaskEndpoint = flaskEndpoint; // Endpoint flask for load data
        this.tableSelector = `#dataTable-${this.uniqueIdSelector}`; // Table selector
        this.datatable = null; // Datatable instance
        this.currentAction = "first";
        this.currentSearch = "";
        this.currentPage = 0; 
        this.fieldsProjected = null; 
        this.currentPageSize = 10; // Number of elements displayed per page
        this.page_id = page_id; // ID of page

        // Dynamic creation of container and elements associated in the parent div
        this.createTableContainer();

        // Init events managements
        this.initEventHandlers();
    }

    createTableContainer() {
        //Parent div selection from id
        const parentContainer = $(`#${this.uniqueIdSelector}`);
        if (!parentContainer.length) {
            console.error(`Parent container with id '${this.uniqueIdSelector}' not found.`);
            return;
        }

        // HTML container for table and controls
        const containerHTML = `
            <div id="tableContainer-${this.uniqueIdSelector}" class="table-container">
                <table id="dataTable-${this.uniqueIdSelector}" class="ui celled table" style="width:100%"></table>
                <!-- <div class="pagination-controls">
                    <button id="first-${this.uniqueIdSelector}">First</button>
                    <button id="previous-${this.uniqueIdSelector}">Previous</button>
                    <button id="next-${this.uniqueIdSelector}">Next</button>
                    <button id="last-${this.uniqueIdSelector}">Last</button>
                    <input id="currentPage-${this.uniqueIdSelector}" type="number" value="1" class="page-input">
                    <select id="pageSize-${this.uniqueIdSelector}">
                        <option value="10" selected>10</option>
                        <option value="20">20</option>
                        <option value="50">50</option>
                    </select>
                    <span id="totalpages-${this.uniqueIdSelector}"></span>
                    <span id="totalitems-${this.uniqueIdSelector}"></span>
                    <span id="startindex-${this.uniqueIdSelector}"></span>
                    <span id="endindex-${this.uniqueIdSelector}"></span>
                </div> -->
            </div>
        `;

        // Display container 
        parentContainer.html(containerHTML);
    }

    destroyTable() {
        if ($.fn.DataTable.isDataTable(this.tableSelector)) {
            $(this.tableSelector).DataTable().clear().destroy();
        }

        // Restore base structure of table after desctruction
        $(this.tableSelector).empty().html(`
            <thead>
                <tr></tr>
            </thead>
            <tbody></tbody>
        `);
    }

    initDataTable(data, fields = null) {
        console.log("Initializing DataTable with data");
        const keys = new Set();
        if (!fields) {
            data.forEach(obj => Object.keys(obj).forEach(key => keys.add(key)));
        } else {
            fields.forEach(key => keys.add(key));
        }

        const validatedData = this.validateAndCorrectData(data, Array.from(keys));
        const columns = Array.from(keys).map(key => ({ title: key, data: key }));

        this.destroyTable();

        this.datatable = $(this.tableSelector).DataTable({
            data: validatedData,
            columns: columns,
            paging: false,
            searching: false,
            ordering: true,
            scrollX: true,
            language: {
                lengthMenu: "Display _MENU_ elements per page",
                zeroRecords: "No data available in table",
                info: "Display from _START_ to _END_ elements",
                infoEmpty: "No data available in table",
                infoFiltered: "(filtered on _MAX_ elements in total)",
                search: "Search into table :",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
        console.log("DataTable initialized");
    }

    validateAndCorrectData(data, keys) {
        return data.map(item => {
            const correctedItem = {};
            keys.forEach(key => {
                correctedItem[key] = item[key] !== undefined ? item[key] : null;
            });
            return correctedItem;
        });
    }

    loadData(action = "first") {
        loadingSpinnerShow(`Getting data from server for table: ${this.uniqueIdSelector} ...`);

        $.ajax({
            url: this.flaskEndpoint,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                action: action,
                currentPage: this.currentPage,
                itemsPerPage: this.currentPageSize,
                currentId: this.uniqueId,
                page_id: this.page_id
            }),
            success: (response) => {
                if (response) {
                    console.log("Received data in table class:", response);
                    // Ensure json is received
                    if (typeof response === "string") {
                        response = JSON.parse(response);
                    }

                    // Extract data from this specific table
                    const tableData = response["variables"]?.[this.uniqueId];
                    if (!tableData) {
                        console.error("Data not found for table:", this.uniqueId);
                        return;
                    }
                    if (tableData.type === 'table') {
                        const data = tableData.data.map(item => ({ ...item }));
                        console.log("Received data in table class:", tableData);
                        this.currentPage = tableData.current_page;
                        this.fieldsProjected = tableData.fields;

                        // Update indicators on each tables
                        $(`#currentPage-${this.uniqueIdSelector}`).val(this.currentPage);
                        $(`#totalpages-${this.uniqueIdSelector}`).text(`Total Pages: ${tableData.total_pages}`);
                        $(`#totalitems-${this.uniqueIdSelector}`).text(`Total Items: ${tableData.total_items}`);
                        $(`#startindex-${this.uniqueIdSelector}`).text(`Start Items: ${tableData.start_index}`);
                        $(`#endindex-${this.uniqueIdSelector}`).text(`End Items: ${tableData.end_index}`);

                        if (data && data.length > 0) {
                            this.initDataTable(data, this.fieldsProjected);
                        } else {
                            this.destroyTable();
                        }
                    }
                } else {
                    console.error("Error during collecting data:", this.tableData);
                }
            },
            error: (error) => {
                console.error("Error during collecting data:", error);
            },
            complete: () => {
                loadingSpinnerHide();
            }
        });
    }

    initEventHandlers() {
        $(`#first-${this.uniqueIdSelector}`).click(() => this.loadData("first"));
        $(`#previous-${this.uniqueIdSelector}`).click(() => this.loadData("previous"));
        $(`#next-${this.uniqueIdSelector}`).click(() => this.loadData("next"));
        $(`#last-${this.uniqueIdSelector}`).click(() => this.loadData("last"));
        $(`#currentPage-${this.uniqueIdSelector}`).on('change', (event) => {
            this.currentPage = parseInt($(event.target).val());
            this.loadData("go_to_page");
        });
        $(`#pageSize-${this.uniqueIdSelector}`).on('change', (event) => {
            this.currentPageSize = parseInt($(event.target).val());
            this.loadData("change_page_size");
        });
    }

    toggleTableVisibility(visible = true) {
        if (visible) {
            $(`#tableContainer-${this.uniqueIdSelector}`).show();
        } else {
            $(`#tableContainer-${this.uniqueIdSelector}`).hide();
        }
    }
}
