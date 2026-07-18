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
document: app
*/

let selectAll = false;
let columnVisibility = {};
let initialLoad = true;

var indices;
var tenants;
var technologies;
var dateStartInput;
var dateEndInput;
var page_id;

$(document).ready(function() {

    indices = new DropdownList('Index', '/search_available_index', 'dropdownindex');
    tenants = new DropdownList('Tenant', '/search_available_tenant', 'dropdowntenant');
    technologies = new DropdownList('Technology', '/search_available_technologies', 'dropdowntechnology');
    dateStartInput = document.getElementById("startPicker");
    dateEndInput = document.getElementById("endPicker");
    page_id = Math.floor(Math.random() * 10000000000)


    // Add listener to listen for Ctrl+Enter key combination
    document.addEventListener('keydown', function (event) {
        if (event.ctrlKey && event.key === 'Enter') {
                event.preventDefault();
                $("#searchForm").submit();
            }
        });


    // Initialise behavior for fields start and end time
    toggleFieldset('toggleStartTime', 'start_time', 'startTimeNumber', 'startTimePreset');
    toggleFieldset('toggleEndTime', 'end_time', 'endTimeNumber', 'endTimePreset');
    linkCalendarAndPreset('start_time', 'startTimeNumber', 'startTimePreset');
    linkCalendarAndPreset('end_time', 'endTimeNumber', 'endTimePreset');


    
    // Execute immediately and then every 30 seconds
    resetResearchTimeout();
    setInterval(resetResearchTimeout, 30000);

    // Function for the search submission
    $('#searchForm').on('submit', function(event) {
        event.preventDefault();

        const query = $('#searchQuery').text();
        // const startTime = getActiveDate('start_time', 'startTimeNumber', 'startTimePreset');
        const startTime = dateStartInput.getActiveDate();
        const endTime = dateEndInput.getActiveDate();
        // const endTime = getActiveDate('end_time', 'endTimeNumber', 'endTimePreset');
        if (startTime && endTime) {
            console.log(`Start Time: ${startTime}, End Time: ${endTime}`);
            // Submit your form or use these variables as needed
        } else {
            console.log('Please select valid start and end times.');
        }
        // const index = $('#indexSelect').val();
        // const tenant = $('#tenantSelect').val();
        const index = indices.getSelectedValues();
        const tenant = tenants.getSelectedValues();
        const technology = technologies.getSelectedValues();

        loadingSpinnerShow("Waiting search results ...");

        fetch(`query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, startTime, endTime, index, tenant, technology, page_id })
        })
        .then(response => response.json())
        .then(data => {

            //Delete data
            userinterfaceclean();
            console.log(data);
            loadingSpinnerHide();

            if (data && Array.isArray(data.data) && data.type === 'table') {
                // Display table panel
                displayTablePanel(true);
                fieldsProjected = data.fields || {};
                loadingSpinnerHide();
                loadData("first");
                updateTableVisibility();
            }
            else if (data && data.type === 'graph') {
                // hide table panel
                displayTablePanel(false);
                // create data
                let parsedData = data.data.map(item => {
                    let fields;
                    try {
                        // fields = JSON.parse(item);
                        fields = item;
                    } catch (error) {
                        console.error("Erreur de parsing JSON:", error);
                        fields = {};
                    }
                    return {...fields};
                });
                drawChart(parsedData, data.graph_type, "myChart");
            }
            else {
                destroyChart();
                destroyTable();
                $('#result').text("Invalid data format.");
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            loadingSpinnerHide();  // Hide the global spinner global after received the error
        });
    });    
});
