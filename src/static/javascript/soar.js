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
document: soar
*/


// VARIABLES DECLARATION

    let context = {
        history: [],
        variables: {}
    };
    let jsonEditorInstance = null;
    let indexInput, tenantInput, historyInput; //vaultInput, 


    // Export Function
    function exportContext() {
        //TODO change self.context to take all and result card to display only last value
        // Transformation answer in table 
        if (context.history && Array.isArray(context.history)) {
            context.history = context.history.map(item => {
                if (item && typeof item.answer !== "undefined") {
                    if (!Array.isArray(item.answer)) {
                        item.answer = [item.answer];
                    }
                }
                return item;
            });
        }
        const dataStr = JSON.stringify(context, null, 2);
        const blob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "context.json";
        a.click();

        URL.revokeObjectURL(url);
    }

    // FUNCTIONS DECLARATION
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Init JSONEditor on readonly
    function initJSONEditor() {
        const container = document.getElementById("jsoneditor");

        const options = {
            mode: "view",              // Readonly
            mainMenuBar: false,        // No main menu
            navigationBar: true,       // Browse JSON
            statusBar: false,
            search: true               // Activate search
        };

        jsonEditorInstance = new JSONEditor(container, options);
    }


    function updateJSONViewer() {
        if (!jsonEditorInstance) return;

        try {
            if (Array.isArray(context.history)) {
                jsonEditorInstance.set({
                    // history: context.history,
                    // variables: typeof context.variables !== 'undefined' ? context.variables : {}
                    context: context
                });
            } else {
                jsonEditorInstance.set({ error: "context.history is not a table" });
            }
        } catch (e) {
            jsonEditorInstance.set({ error: "Error during JSON parsing : " + e.message });
        }
    }


    // TODO factorise function
    function loadingSpinnerShow(label) {
        //  Save hour of loading
        loadingStartTime = new Date();

        // Display spinner
        $('#loadingSpinner').show();
        $('#loadingSpinnerLabel').text(label);

        // Start interval to update at the end of the timer
        loadingInterval = setInterval(() => {
            const elapsedTime = Math.floor((new Date() - loadingStartTime) / 1000); 
            $('#loadingSpinnerLabel').text(`${label} (${elapsedTime}s)`);
        }, 1000); // Update each seconds
    }

        // TODO factorise this function
        function loadingSpinnerHide() {
            $('#loadingSpinner').hide();
            $('#loadingSpinnerLabel').text('');
            clearInterval(loadingInterval);
        }

        // COPY COMMAND AND ANSWER BUTTON
        function copyToClipboard(elementId) {
            const input = document.getElementById(elementId);
            if (input) {
                navigator.clipboard.writeText(input.value)
                    .then(() => console.log('Command copied!'))
                    .catch(err => console.error('Copy failed:', err));
            }
        }

        function copyAnswer(entryId) {
            const pre = document.getElementById(`answer-${entryId}`);
            if (pre) {
                navigator.clipboard.writeText(pre.innerText)
                    .then(() => console.log('Answer copied!'))
                    .catch(err => console.error('Copy failed:', err));
            }
        }

    function renderResults() {
        const resultContainer = document.getElementById('result');

        if (!context.history || context.history.length === 0) {
            console.warn('Context history is empty or undefined.');
            resultContainer.innerHTML = '';
            return;
        }

        // Sort list of historic by id
        context.history.sort((a, b) => a.id - b.id);

        const existingCards = Array.from(resultContainer.querySelectorAll('.result-card'));
        const historyIds = context.history.map(entry => entry.id);

        // Delete cards that are no more in context.history
        existingCards.forEach(card => {
            const id = parseInt(card.dataset.id);
            if (!historyIds.includes(id)) {
                console.log(`Delete card with id ${id}`);
                card.remove();
            }
        });

        // Browse each elements of the context or update cards
        context.history.forEach(entry => {
            let card = resultContainer.querySelector(`.result-card[data-id="${entry.id}"]`);

            const newAnswerText = JSON.stringify(entry.answer.at(-1), null, 2);
            const existingAnswerElem = card ? card.querySelector(`#answer-${entry.id}`) : null;
            const existingCommandElem = card ? card.querySelector(`#cmd-input-${entry.id}`) : null;
            const existingAnswerText = existingAnswerElem ? existingAnswerElem.textContent : '';
            const existingCommandText = existingCommandElem ? existingCommandElem.value : '';
            // Update to take only the last element
            entry.answer = entry.answer.at(-1);

            // If cards does not exists, create it 
            if (!card) {
                console.log(`Card creation with id ${entry.id}`);
                const newCard = new SOARCard(entry).render();
                resultContainer.appendChild(newCard);
            } 
            // Else, if command or result has been modified
            else if (existingCommandText !== entry.command || existingAnswerText !== newAnswerText) {
 
                console.log(`Update card with id ${entry.id}`);
                const updatedCard = new SOARCard(entry).render();
                resultContainer.replaceChild(updatedCard, card);
            }
        });
    }


    async function stopExecution() {
        try {
            const command = "soar_stop_execution";
            await replayCommand(null, command, false);
        } catch (error) {
            console.error('Error in eraseContext:', error);
        } finally {
            loadingSpinnerHide();
        }
    }

    
    async function eraseContext(id = -1) {
        console.log("eraseContext called with id:", id);
        loadingSpinnerShow("Clearing history...");
        if (id === -1) {
            const userConfirmed = window.confirm("Confirm clear all context?");
            if (!userConfirmed) {
                return; 
            }

            try {
                const command = "soar_erase_context";
                await replayCommand(null, command, false);
            } catch (error) {
                console.error('Error in eraseContext:', error);
            } finally {
                loadingSpinnerHide();
            }
        }
        else {
            try {
                const userConfirmed = window.confirm("Confirm clear context for id: " + id + " ?");
                if(!userConfirmed) {
                    return; 
                }
                const command = "soar_erase_context id=" + id;
                await replayCommand(null, command, false);
            } catch (error) {
                console.error('Error in eraseContext: ' + id, error);
            } finally {
                loadingSpinnerHide();
            }
        }
    }

    async function swap_ids(old_id, new_id) {
        try {
            const command = `soar_swap_ids old_id=${old_id} new_id=${new_id}`;
            await replayCommand(null, command, false);
        } catch (error) {
            console.error('Error in swap_id:', error);
        }
    }



    async function playAllFunctions(replay=false) {
        console.log("playAllFunctions called with replay:", replay);
        if (context.length === 0) return;
        if (!context.variables || typeof context.variables.next_id !== 'number') {
            console.error("Invalid or missing variables.next_id");
            loadingSpinnerHide();
            return;
        }

        loadingSpinnerShow("Playing all commands...");
        // let previousId = null;

        if (replay) {
            // Replay from the beginning
            const command = "soar_reset_context";
            await replayCommand(null, command, false);
        }
        await replayCommand(null, "soar_start_execution", false);
        // context.variables._running = true;

        // Prepare context id
        var name = historyInput.getSelectedValues()[0] || "Main";
        var index= indexInput.getSelectedValues()[0] || "";
        var tenant= tenantInput.getSelectedValues()[0] || "";
        // var instance= vaultInput.getSelectedValues()[0] || "";
        var soarModeEnabled = $('#soarModeCheckbox').is(':checked');
        replayCommand(null, `soar_play_context name=${name} instance=${instance} index=${index} tenant=${tenant} playbook=${soarModeEnabled}`, false);

        // Reload the context
        const command_reload = `soar_load_context name=${name} instance=${instance} index=${index} tenant=${tenant}`
        await replayCommand(null, command_reload, false);

        let attempts = 0;
        const maxAttempts = 10;
        while (context.variables._running && attempts < maxAttempts) {

            const command = `soar_load_context name=${name} instance=${instance} index=${index} tenant=${tenant}`
            await replayCommand(null, command, false);

            await updateJSONViewer();

            await sleep(3000);

            attempts++;
        }

        loadingSpinnerHide();
    }


function updateURLParam(key, value) {
    const url = new URL(window.location);
    if (value) {
        url.searchParams.set(key, value);
    } else {
        url.searchParams.delete(key);
    }
    window.history.replaceState({}, '', url);
}


async function replayCommand(id = null, fallbackCommand = null, display = true) {
    let command = fallbackCommand;
    let replayId = id;

    // If id provided, search id
    if (id !== null) {
        const entry = context.history.find(e => e.id === id);
        if (!entry) return;
        command = entry.command;
        replayId = entry.id;
    }

    const soarModeEnabled = $('#soarModeCheckbox').is(':checked');

    const index = indexInput.getSelectedValues()[0] || "";
    const tenant = tenantInput.getSelectedValues()[0] || "";
    // const vault = vaultInput.getSelectedValues()[0] || "";
    const historyName = historyInput.getSelectedValues()[0] || "";
    // const display = window.__displayFlag === true;

    loadingSpinnerShow(id !== null ? "Replaying command..." : "Executing command...");

    try {
        const response = await fetch(`soar_command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                command,
                id: replayId ?? -1,
                playbook_mode: soarModeEnabled,
                index,
                tenant,
                // vault,
                history: historyName,
                display
            })
        });

        const data = await response.json();
        loadingSpinnerHide();

        if (data && typeof data === 'object') {
            // context.history = data["history"];
            // context.variables = data["variables"];
            context = data;
        }

        updateJSONViewer();
        renderResults();

        return data;

    } catch (error) {
        console.error('Error during execution :', error);
        loadingSpinnerHide();
    }
}


$(document).ready(function () {
    initJSONEditor();

    // PLAYBOOK BUTTONS
    const soarModeCheckbox = document.getElementById('soarModeCheckbox');
    const playAllBtn = document.getElementById('playall_button');
    const replayAllBtn = document.getElementById('replayall_button');
    const stopBtn = document.getElementById('stop_button');


    // Fonction pour mettre à jour l'état des boutons
    function toggleButtons() {
        const isPlaybookActive = soarModeCheckbox.checked;
        
        // Désactive ou active l'attribut HTML "disabled"
        playAllBtn.disabled = isPlaybookActive;
        replayAllBtn.disabled = isPlaybookActive;
        stopBtn.disabled = isPlaybookActive;

        // Optionnel : Ajoute/retire la classe CSS "disabled" de Semantic UI pour l'aspect visuel
        [playAllBtn, replayAllBtn, stopBtn].forEach(btn => {
            if (isPlaybookActive) {
                btn.classList.add('disabled');
            } else {
                btn.classList.remove('disabled');
            }
        });
    }

    // Écoute les changements sur la checkbox
    soarModeCheckbox.addEventListener('change', toggleButtons);

    // Exécute la fonction au chargement de la page pour s'aligner sur l'état initial
    toggleButtons();

    // Instantiate TagInputList
    indexInput = new TagInputList("Index", "/search_available_index", "selectindex", false, {}, 'GET');
    tenantInput = new TagInputList("Tenant", "/search_available_tenant", "selecttenant", false, {}, 'GET');
    // vaultInput = new TagInputList("Vault Instance", "/search_available_vault_instances", "selectinstance", false, {}, 'GET');
    historyInput = new TagInputList("Context Name", "/get_history_list", "selectname", false, () => ({
        index: indexInput.getSelectedValues()[0] || "",
        tenant: tenantInput.getSelectedValues()[0] || "",
        // vault: vaultInput.getSelectedValues()[0] || ""
    }), 'GET');


const urlParams = new URLSearchParams(window.location.search);

// Collect parameters
const paramIndex = urlParams.get("index");
const paramTenant = urlParams.get("tenant");
// const paramVault = urlParams.get("vault");
const paramHistory = urlParams.get("history");

const promises = [];

// INDEX
if (paramIndex) {
    indexInput.setSelectedValues(paramIndex);
} else {
    promises.push(
        indexInput.loadData().then(() => {
            if (selectedIndex && indexInput.suggestions.includes(selectedIndex)) {
                indexInput.setSelectedValues(selectedIndex);
            } else if (indexInput.suggestions.length > 0) {
                indexInput.setSelectedValues(indexInput.suggestions[0]);
            }
        })
    );
}

// TENANT
if (paramTenant) {
    tenantInput.setSelectedValues(paramTenant);
} else {
    promises.push(
        tenantInput.loadData().then(() => {
            if (selectedTenant && tenantInput.suggestions.includes(selectedTenant)) {
                tenantInput.setSelectedValues(selectedTenant);
            } else if (tenantInput.suggestions.length > 0) {
                tenantInput.setSelectedValues(tenantInput.suggestions[0]);
            }
        })
    );
}

// VAULT
// if (paramVault) {
//     vaultInput.setSelectedValues(paramVault);
// } else {
//     promises.push(
//         vaultInput.loadData().then(() => {
//             if (selectedVault && vaultInput.suggestions.includes(selectedVault)) {
//                 vaultInput.setSelectedValues(selectedVault);
//             } else if (vaultInput.suggestions.length > 0) {
//                 vaultInput.setSelectedValues(vaultInput.suggestions[0]);
//             }
//         })
//     );
// }

// HISTORY - wait for the others to be changed
Promise.all(promises).then(() => {
    if (paramHistory) {
        historyInput.setSelectedValues(paramHistory);
        command = "soar_load_context name=" + paramHistory + " index=" + indexInput.getSelectedValues()[0] + " tenant=" + tenantInput.getSelectedValues()[0]
        //  + " instance=" + vaultInput.getSelectedValues()[0]
        replayCommand(null, command, false);
    } else {
        historyInput.loadData().then(() => {
            if (selectedHistory && historyInput.suggestions.includes(selectedHistory)) {
                historyInput.setSelectedValues(selectedHistory);
            } else if (historyInput.suggestions.length > 0) {
                historyInput.setSelectedValues(historyInput.suggestions[0]);
            }
        });
    }
});

    // Update URL on changes
    indexInput.onChange(values => {updateURLParam('index', values[0] || '');onChangeUpdateHistory();});
    tenantInput.onChange(values => {updateURLParam('tenant', values[0] || '');onChangeUpdateHistory();});
    // vaultInput.onChange(values => {updateURLParam('vault', values[0] || '');onChangeUpdateHistory();});
    historyInput.onChange(values => {
        console.log("History changed to: " + values[0]);
        updateURLParam('history', values[0] || '')
        // Reload suggestions of historic on each modification
        // TODO change load_playbook if playbook selected
        command = "soar_load_context name=" + values[0] + " index=" + indexInput.getSelectedValues()[0] + " tenant=" + tenantInput.getSelectedValues()[0]
        //  + " instance=" + vaultInput.getSelectedValues()[0]
        replayCommand(null, command, false);
    });

    // Trigger the reload of the page in case of select or deselect Playbook mode
    $('#soarModeCheckbox').on('change', function () {
        const isChecked = $(this).is(':checked');
        const command = "soar_load_context name=" + isChecked +
            " index=" + indexInput.getSelectedValues()[0] +
            " tenant=" + tenantInput.getSelectedValues()[0] +
            // " instance=" + vaultInput.getSelectedValues()[0];

        replayCommand(null, command, false);
    });

    // Command on history selection
    document.getElementById("selectname")?.addEventListener("change", function () {
        const name = document.getElementById("selectname")?.value || "";
        const index = document.getElementById("selectindex")?.value || "";
        const tenant = document.getElementById("selecttenant")?.value || "";
        // const vault = document.getElementById("selectinstance")?.value || "";
        const command = `soar_load_history name=${name} index=${index} tenant=${tenant} `; //instance=${vault}
        $('#commandQuery').text(command);
        window.__displayFlag = true;
        $('#commandForm').trigger('submit');
    });

    // Submit handling
    $('#commandForm').on('submit', async function(event) {
        event.preventDefault();
        try {
            const command = $('#commandQuery').text();
            await replayCommand(null, command);
        } catch (error) {
            console.error('Error:', error);
        }
    });
});


// Refresh only historyInput when index/tenant/vault change
function onChangeUpdateHistory() {

    historyInput.setQueryParams(() => ({
        index: indexInput.getSelectedValues()[0] || "",
        tenant: tenantInput.getSelectedValues()[0] || "",
        // vault: vaultInput.getSelectedValues()[0] || ""
    }));

    historyInput.loadData().then(() => {
        console.log("historyInput.suggestions", historyInput.suggestions);
    });
}

function initSuggestions() {
    console.log("initSuggestions launched");
    const inputs = document.querySelectorAll('.command-line');
    inputs.forEach(input => {
        console.log("input suggesstions", input);
        if (input.dataset.suggestionInitialized) return; 
        input.dataset.suggestionInitialized = 'true';

        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'suggestions hidden';
        document.body.appendChild(suggestionsContainer);

        new SuggestionManager(input, suggestionsContainer, '/command_suggestions');
    });
}

function showImportPopup() {
    document.getElementById("import-popup").style.display = "flex";
}

function hideImportPopup() {
    document.getElementById("import-popup").style.display = "none";
}

function setupImportPopup() {
    const dropZone = document.getElementById("drop-zone");

    const handleFile = (file) => {
        if (!file.name.toLowerCase().endsWith(".json")) {
            alert("Only json file are authorized.");
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const parsed = JSON.parse(e.target.result);
                if (typeof parsed !== "object" || parsed === null) {
                    throw new Error("JSON File must contain objet or list of object.");
                }

                console.log(parsed);

                context = parsed;
                replayCommand(null, "soar_import_context imported=" + btoa(JSON.stringify(parsed)), false);

                hideImportPopup();
            } catch (err) {
                alert("Error : " + err.message);
            }
        };
        reader.readAsText(file);
    };

    // Avoid default behaviour
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Visual style
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.style.background = "#eef");
    });
    ["dragleave", "drop"].forEach(eventName => {
        dropZone.style.background = "white";
    });

    // Drop
    dropZone.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    // Click
    dropZone.addEventListener("click", () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "application/json";
        input.onchange = (event) => {
            const file = event.target.files[0];
            if (file) handleFile(file);
        };
        input.click();
    });
}

// Classic call to load
document.addEventListener('DOMContentLoaded', initSuggestions);
document.addEventListener("DOMContentLoaded", setupImportPopup);