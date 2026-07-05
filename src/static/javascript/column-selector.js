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
document: column selector
*/

$(document).ready(function() {
    // Function of balance for all fields with the button "Select All"
    $('#toggleSelect').on('click', function() {
        console.log("Toggling select all...");
        $('#columnSelector input[type="checkbox"]').each(function() {
            $(this).prop('checked', selectAll);  // Check or uncheck all boxes
            const columnName = $(this).parent().text().trim();
            columnVisibility[columnName] = selectAll;
        });

        selectAll = !selectAll;  // Reverse button states
        $('#toggleSelect').text(selectAll ? 'Select All' : 'Select None');
        updateTableVisibility();  
        // Update visibility of columns in table
    });
});

// Function to reinitialise the columns selector
function resetColumnSelector() {
    // Logic to erase or reinitialise the columns selector
    console.log("Réinitialisation du sélecteur de colonnes.");
    $('#columnSelector').empty();  
    // Example: Empty the element of the columns selector
}

// Function of update columns visibility
async function updateTableVisibility() {
    loadingSpinnerShow("Updating Data Table Columns ...");
    await sleep(500);

    if (!datatable) {
        console.error("Table instance is not defined.");
        return;
    }
    datatable.columns().every(function(index) {
        const column = datatable.column(index);
        const headerText = $(column.header()).text().trim();
        column.visible(columnVisibility[headerText] !== undefined ? columnVisibility[headerText] : true);
    });
    datatable.draw(false);
    loadingSpinnerHide();
}

function createColumnSelector(fieldsProjected) {
    const columnSelector = $('#columnSelector');
    columnSelector.empty();

    fieldsProjected.forEach(key => {
        // Determine if the column is visible based on "fieldsProjected"
        if (fieldsProjected && fieldsProjected.length > 0) {
            columnVisibility[key] = fieldsProjected.includes(key);
        } else if (initialLoad) {
            columnVisibility[key] = true;
        } else {
            columnVisibility[key] = columnVisibility[key] ?? false;  
            // Keep previous visbility
        }

        const item = $('<div class="item"></div>');
        const label = $('<label></label>').text(key);
        const checkbox = $('<input type="checkbox">');

        checkbox.prop('checked', columnVisibility[key]);
        checkbox.on('change', function() {
            columnVisibility[key] = this.checked;
            updateTableVisibility();
        });

        label.prepend(checkbox);
        item.append(label);
        columnSelector.append(item);
    });

    initialLoad = false;

    $('#columnSearch').on('keyup', function() {
        const searchValue = $(this).val().toLowerCase();
        columnSelector.children('.item').each(function() {
            const labelText = $(this).text().toLowerCase();
            $(this).toggle(labelText.includes(searchValue));
        });
    });
}

