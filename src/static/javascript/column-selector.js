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
document: column selector
*/

$(document).ready(function() {
    // Function to toggle balance for all fields with the "Select All / Deselect All" button
    $('#toggleSelect').on('click', function() {
        console.log("Toggling select all...");
        // Determine the target state based on the current selectAll state
        const targetState = selectAll;
        $('#columnSelector input[type="checkbox"]').each(function() {
            // Set the checkbox state
            $(this).prop('checked', targetState);
            
            // Retrieve the text from the main parent label
            //const columnName = $(this).closest('label').text().trim();
            const columnName = $(this).data('column');
            
            if (columnName) {
                columnVisibility[columnName] = targetState;
            }
        });
        // Toggle state for next click
        selectAll = !selectAll;
        // Update button label dynamically based on next action
        $('#toggleSelect').text(selectAll ? 'Select All' : 'Select None');
        // Apply column visibility to the DOM table
        updateTableVisibility();  
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

function createColumnSelector(fieldsProjected, keepSelected = false) {
    const columnSelector = $('#columnSelector');
    columnSelector.empty();

    // Si on réinitialise (action == "first"), on peut vider l'objet pour repartir propre
    if (!keepSelected) {
        columnVisibility = {};
    }

    fieldsProjected.forEach(key => {
        if (keepSelected) {
            // Si le champ avait déjà un état (true/false), on le conserve.
            // S'il n'existait pas encore dans columnVisibility, on le met à true par défaut.
            columnVisibility[key] = columnVisibility[key] ?? true;
        } else {
            // Action "first" -> Remise à zéro : tous les champs projetés sont visibles par défaut
            columnVisibility[key] = true;
        }

        const item = $('<div class="item"></div>')
        const label = $('<label></label>').text(key);

        const toggleContainer = $('<label class="toggle-container"><span class="toggle-slider"><p> </p></span></label>');
        const input = $('<input type="checkbox">')
            .attr('data-column', key)
            .prop('checked', columnVisibility[key]);

        input.on('change', function() {
            columnVisibility[key] = this.checked;
            updateTableVisibility();
        });
        
        toggleContainer.prepend(input);
        label.prepend(toggleContainer);
        item.append(label);
        columnSelector.append(item);
    });

    $('#columnSearch').off('keyup').on('keyup', function() {
        const searchValue = $(this).val().toLowerCase();
        columnSelector.children('.item').each(function() {
            const labelText = $(this).text().toLowerCase();
            $(this).toggle(labelText.includes(searchValue));
        });
    });
}

