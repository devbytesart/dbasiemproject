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
document: table
*/
var datatable = null;
let currentAction = "first";  // Action (first, previous, next, last)
let currentSearch = ""; 
let currentPage = 0;  
let fieldsProjected = null;  
let currentPageSize = 10;  // Number of elements displayed per page

// Function to destroy existing datatable
function destroyTable() {
    if ($.fn.DataTable.isDataTable('#dataTable')) {
        // Destroy table if already exists
        $('#dataTable').DataTable().clear().destroy();
    }

    // Restore structure base table after destruction
    $('#dataTable').empty().html(`
        <thead>
            <tr></tr>
        </thead>
        <tbody></tbody>
    `);
}

// Function to init datatable
function initDataTable(data, fields = null) {
    destroyTable();  

    const keys = new Set();
    if (!fields) {
        // Get all unique fields if not provided
        data.forEach(obj => Object.keys(obj).forEach(key => keys.add(key)));
    } else {
        fields.forEach(key => keys.add(key));
    }

    const validatedData = validateAndCorrectData(data, Array.from(keys)); 
    const columns = Array.from(keys).map(key => ({ title: key, data: key }));

    // Initi datatable with new data
    datatable = $('#dataTable').DataTable({
        data: validatedData,
        columns: columns,
        paging: false, // Disable automatic pagination
        searching: false, // Disable automatic search
        ordering: true, // Autorise sorting
        scrollX: true, // Enable scrolling horizontal
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
}

// Function to load data from Flask depending on action (next, previous, ...)
function loadData(action = "first") {
    loadingSpinnerShow("Getting data from server ...");
    
    $.ajax({
        url: '/get_page', 
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ action: action, currentPage: currentPage, itemsPerPage: currentPageSize, page_id: page_id }),
        success: function(response) {
            if (response) {
                response = JSON.parse(response);
                if (response.type === 'table') {
                    console.log("Data received:", response);
                    const data = response.data;
                    console.log("Data received:", data);
                    currentPage = response.current_page;
                    $('#currentPage').val(currentPage);
                    $("#totalpages")[0].innerText = "Total Pages: " + response.total_pages;
                    $("#totalitems")[0].innerText = "Total Items: " + response.total_items;
                    $("#startindex")[0].innerText = "Start Items: " + response.start_index;
                    $("#endindex")[0].innerText = "End Items: " + response.end_index;
                    console.log("Current page:", currentPage);
                    fieldsProjected = response.fields;
                    console.log("Fields projected :", fieldsProjected);

                    // Reset the column selector if not data
                    if (data && data.length > 0) {
                        createColumnSelector(fieldsProjected);  // Update columns selector
                        initDataTable(data.map(item => {return {...item}}), fieldsProjected);  // Init table with new data
                    } else {
                        console.warn("No data in table.");
                        destroyTable();  
                        resetColumnSelector(); 
                    }
                }
            } else {
                console.error("Error during collecting data :", response);
            }
        },
        error: function(error) {
            console.error("Error during collecting data :", error);
        },
        complete: function() {
            loadingSpinnerHide();
        }
    });
}

// Management browsing buttons 
$(document).ready(function() {

    $('#first').click(() => {
        loadData("first");
    });
    $('#previous').click(() => {
        loadData("previous");
    });
    $('#next').click(() => {
        loadData("next");
    });
    $('#last').click(() => {
        loadData("last");
    });
    $('#currentPage').on('change', function() {
        currentPage = parseInt($(this).val());
        console.log("Current page :", currentPage);
        loadData("go_to_page");
    });
    $('#pageSize').on('change', function() {
        currentPageSize = parseInt($(this).val());
        console.log("Page size :", currentPageSize);
        loadData("change_page_size");
    });
});

function displayTablePanel(visible = true) {
    if (visible) {
        $('#tableContainer').show();
    } else {
        $('#tableContainer').hide();
        resetColumnSelector();
    }
}