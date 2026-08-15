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
document: configuration
*/

// Initialize JSON editor
let logservices = [];
let indexers = [];

var container = document.getElementById("jsoneditor");
var options = {
    mode: 'tree',
    modes: ['tree', 'view', 'form', 'code', 'text'],
    onError: function (err) {
        alert(err.toString());
    }
};
var editor = new JSONEditor(container, options);
editor.set(JSON.parse(JSON.stringify(json_data)));

// Function to populate slave coordinator options
function populateSlaveCoordinatorOptions() {
    try {
        var slaveCoordinatorSelect = document.getElementById("slave-coordinator");
        if (!slaveCoordinatorSelect) {
            throw new Error("Element with ID 'slave-coordinator' not found.");
        }
        slaveCoordinatorSelect.innerHTML = '<option value="">-- Select a Slave Coordinator --</option>'; // Clear existing options

        var slaveCoordinators = json_data.infrastructure.slavecoordinators;
        if (!Array.isArray(slaveCoordinators)) {
            throw new Error("Invalid data format: 'slavecoordinators' is not an array.");
        }

        slaveCoordinators.forEach(function (coordinator) {
            if (!coordinator.id) {
                throw new Error("Missing 'id' field in a slave coordinator object.");
            }
            var option = document.createElement("option");
            option.value = coordinator.id; // Assumes each coordinator has a unique 'id' field
            option.text = `Slave Coordinator - ${coordinator.id}`;
            slaveCoordinatorSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error populating slave coordinator options:", error);
        alert("An error occurred while populating the Slave Coordinator options. Please try again or contact support.");
    }
}

// Function to populate authenticator options
function popupaleAuthenticatorOption() {
    try {
        var authenticatorSelect = document.getElementById("authenticator");
        if (!authenticatorSelect) {
            throw new Error("Element with ID 'authenticator' not found.");
        }
        authenticatorSelect.innerHTML = '<option value="">-- Select an Authenticator --</option>'; // Clear existing options

        var authenticators = json_data.infrastructure.authenticators;
        if (!Array.isArray(authenticators)) {
            throw new Error("Invalid data format: 'authenticators' is not an array.");
        }

        authenticators.forEach(function (authenticator) {
            if (!authenticator.id) {
                throw new Error("Missing 'id' field in an authenticator object.");
            }
            var option = document.createElement("option");
            option.value = authenticator.id; // Assumes each authenticator has a unique 'id' field
            option.text = `Authenticator - ${authenticator.id}`;
            authenticatorSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error populating authenticator options:", error);
        alert("An error occurred while populating the Authenticator options. Please try again or contact support.");
    }
}


$("#element-selector-globalauthorisation").change(function() {
    var selectedElement = this.value;
    $("#form-fields").empty();  // Clear the form fields

    if (selectedElement === "users") {
        showUsersForm();
    }
    else if(selectedElement === "resources") {
        showResourcesForm();
    }
    else if(selectedElement === "roles") {
        showRolesForm();
    }
});

// Show specific form based on selected element
$("#element-selector-globalconfiguration").change(function() {
    var selectedElement = this.value;
    $("#form-fields").empty();  // Clear the form fields

    if (selectedElement === "slavecoordinators") {
        showSlaveCoordinatorForm();
    }
    else if (selectedElement === "mastercoordinators") {
        showMasterCoordinatorForm();
    }
    else if (selectedElement === "indexsearchmotors") {
        showIndexSearchMotorForm();
    }
    else if (selectedElement === "dedicatedindexsearchmotors") {
        showDedicatedIndexSearchMotorForm();
    }
    else if (selectedElement === "logcollectors") {
        showLogCollectorForm();
    }
    else if (selectedElement === "logparsers") {
        showLogParserForm();
    }
    else if (selectedElement === "logindexers") {
        showLogIndexerForm();
    }
    else if (selectedElement === "cachesystems") {
        showCacheSystemForm();
    }
    else if (selectedElement === "userinterfaces") {
        showUserInterfaceForm();
    }
    else if(selectedElement === "authenticators") {
        showAuthenticatorForm();
    }
    else if(selectedElement === "soar") {
        showSOARForm();
    }
});

                    // <div id="${key}" class="sub-dictionary">
                    //     <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
                    // </div>

function createType(type, name, defaultValue = "", isReadonly = false, path = []) {
    if (type && name) {
        let targetElement = $("#form-fields");

        const uniqueId = path.join("_") + "_" + name;
        const jsonPath = path.concat(name).join('.');

        path.forEach(key => {
            let subContainer = targetElement.find(`#${key}`);
            if (subContainer.length === 0) {
                targetElement.append(`
                    <button class="ui button collapsible">${key}</button>
                    <div id="${key}" class="ui segment collapsed-content">
                        <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
                    </div>
                `);
                subContainer = targetElement.find(`#${key}`);
            }
            targetElement = subContainer;
        });

        const readonlyAttribute = isReadonly ? "readonly" : "";
        const placeholderAttribute = `placeholder="${defaultValue}"`;

        if (type === "text") {
            targetElement.append(`
                <label for="${uniqueId}">${name.charAt(0).toUpperCase() + name.slice(1)}:</label>
                <input type="text" id="${uniqueId}" name="${uniqueId}" data-json-name="${jsonPath}" ${placeholderAttribute} ${readonlyAttribute} value="${defaultValue}">
                <br/>
            `);
        } else if (type === "number") {
            targetElement.append(`
                <label for="${uniqueId}">${name.charAt(0).toUpperCase() + name.slice(1)}:</label>
                <input type="number" id="${uniqueId}" name="${uniqueId}" data-json-name="${jsonPath}" ${placeholderAttribute} ${readonlyAttribute} value="${defaultValue}">
                <br/>
            `);
        } else if (type === "boolean") {
            targetElement.append(`
                <label for="${uniqueId}">${name.charAt(0).toUpperCase() + name.slice(1)}:</label>
                <select id="${uniqueId}" name="${uniqueId}" data-json-name="${jsonPath}" ${readonlyAttribute}>
                    <option value="false" ${defaultValue === "false" ? "selected" : ""}>False</option>
                    <option value="true" ${defaultValue === "true" ? "selected" : ""}>True</option>
                </select>
                <br/>
            `);
        } else if (type === "list") {
            targetElement.append(`
                <label for="${uniqueId}">${name.charAt(0).toUpperCase() + name.slice(1)} (comma-separated):</label>
                <input type="list" id="${uniqueId}" name="${uniqueId}" data-json-name="${jsonPath}" ${placeholderAttribute} ${readonlyAttribute} value="${defaultValue}">
                <br/>
            `);
        } else if (type === "list_object") {
            let targetElement = $("#form-fields");

            const uniqueId = path.join("_") + "_" + name;
            const containerId = uniqueId + "_container";

            // Create a container for type list_object
            targetElement.append(`
                <div id="${containerId}" class="list-object-container">
                    <h4>${name.charAt(0).toUpperCase() + name.slice(1)}</h4>
                    <button type="button" id="${uniqueId}_add">Add ${name}</button>
                    <button type="button" id="${uniqueId}_remove">Remove Last ${name}</button>
                    <div class="list-object-fields"></div>
                </div><br/>
            `);

            const fieldContainer = $(`#${containerId} .list-object-fields`);

            // List of objects added for this type
            let objectList = [];

            // Definition fields for each type
            const typeFields = {
                logservice: [
                    { name: "id", type: "text", defaultValue: "logservice1" },
                    { name: "host", type: "text", defaultValue: "logparser1" },
                    { name: "port", type: "number", defaultValue: 5100 },
                    { name: "auth_token", type: "text", defaultValue: "my_secure_token" },
                    { name: "primary", type: "boolean", defaultValue: true },
                    { name: "monitoring", type: "boolean", defaultValue: false },
                    { name: "size", type: "number", defaultValue: 500 },
                    { name: "timeout", type: "number", defaultValue: 120 }
                ],
                indexers: [
                    { name: "id", type: "text", defaultValue: "&dedicatedindexsearchmotor1" },
                ]
            };

            // Verification if type exist in the definition
            if (!typeFields[name]) {
                console.error(`Type ${name} non pris en charge.`);
                return;
            }

            // Add object of form
            $(`#${uniqueId}_add`).on("click", function () {
                const fields = typeFields[name];
                const newItem = {};
                const index = objectList.length;

                // Validation and definition of path
                const effectivePath = Array.isArray(path) ? path : [];
                // Use path or empty array

                // Generate formular HTML for each fields
                const formHtml = fields.map(field => {
                    // Verify if the field is valid
                    if (!field.name) {
                        console.error("Field name is missing for:", field);
                        return "";
                    }

                    // Build JSON path for each fields
                    const fieldPath = effectivePath.concat(index, field.name).join('.');

                    // Add default value to newly created object
                    newItem[field.name] = field.defaultValue;

                    // Generate entry of formular
                    return `
                        <label for="${uniqueId}_${field.name}_${index}">
                            ${field.name.charAt(0).toUpperCase() + field.name.slice(1)}:
                        </label>
                        <input
                            type="${field.type}"
                            id="${uniqueId}_${field.name}_${index}"
                            name="${uniqueId}_${field.name}_${index}"
                            data-json-name="${fieldPath}"
                            value="${field.defaultValue}">
                        <br/>
                    `;
                }).join("");

                // Add newly created object to the list
                objectList.push(newItem);

                // Add fields to HTML container
                fieldContainer.append(`
                    <div class="list-item" data-index="${index}">
                        <strong>Item ${index + 1}</strong><br/>
                        ${formHtml}
                        <hr/>
                    </div>
                `);
            });

            // Delete the last object added
            $(`#${uniqueId}_remove`).on("click", function () {
                if (objectList.length > 0) {
                    objectList.pop();
                    // Delete the object from the array
                    fieldContainer.find(".list-item").last().remove();
                    // Delete from DOM
                } else {
                    alert("No Element to delete !");
                }
            });
        }
    }
}


function showSlaveCoordinatorForm() {
    // Empty the formular before adding new fields
    $("#form-fields").empty();

    // Call createType for each required fields
    createType("text", "id");
    createType("text", "host");
    createType("text", "image", true, "ttdantett/siem_slavecoordinator");
    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    // Queue
    createType("number", "max_queue_size", 25, false, ["queue"]);
    createType("text", "backup_file", "data_backup.txt", false, ["queue"]);
    // BRIDGE
    createType("text", "enabled", true, false, ["bridge"]);
    // Logger
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "slavecoordinator.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);
    // STORAGE
    createType("text", "path", "/data/storage/slavecoordinator1", false, ["storage"]);
    // MASTER COORDINATOR
    createType("text", "id", "&mastercoordinator1", false, ["mastercoordinators"]);

    // Add collapsible content function to the new button
    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showLogCollectorForm() {
    $("#form-fields").empty();
    createType("text", "id", "logcollector1");
    createType("text", "type", "logcollector", true);
    createType("text", "image", "ttdantett/siem_logcollector", true);
    createType("text", "collector_type", "receiver", false);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_reverse_proxy_id", "", false, ["webrequester"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "logcollectorcoordinator.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // RECEIVER
    createType("text", "host", "logcollector1", false, ["receiver"]);
    createType("number", "port", "5500", false, ["receiver"]);
    createType("text", "protocol", "tcp", false, ["receiver"]);
    createType("number", "timeout", "10", false, ["receiver"]);
    createType("text", "certfile", "certs/server.crt", false, ["receiver","certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["receiver","certs"]);
    createType("text","delimiter", "\n", false, ["receiver"]);

    // FILE READER
    createType("text", "path", "sample.log", false, ["file_reader"]);
    createType("text", "delimiter", "\n", false, ["file_reader"]);

    // WEBHOOK
    createType("text", "host", "logcollector1", false, ["webhook"]);
    createType("number", "port", "5000", false, ["webhook"]);
    createType("text", "protocol", "tcp", false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook","certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook","certs"]);
    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);
    // QUEUE
    createType("number", "max_queue_size", 500, false, ["queue"]);
    createType("text", "backup_file", "/data/data_logcollector1_backup.txt", false, ["queue"]);
    createType("text", "stats_file", "stats.txt", false, ["queue"]);
    createType("number", "max_backup_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showSOARForm() {
    $("#form-fields").empty();
    createType("text", "id", "soar1");
    createType("text", "type", "soar", true);
    createType("text", "image", "ttdantett/siem_soar", true);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_reverse_proxy_id", "", false, ["webrequester"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "/data/storage/soar1/soar.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "soar1", false, ["webhook"]);
    createType("number", "port", "8000", false, ["webhook"]);
    createType("text", "protocol", "tcp", false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook","certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook","certs"]);

    // ENCRYPTION
    createType("text", "algorithm", "AES256", false, ["encryption"]);
    createType("text", "key_path", "/data/storage/soar1/aes/aes.key", false, ["encryption"]);
    createType("text", "iv_path", "/data/storage/soar1/aes/aes.iv", false, ["encryption"]);

    // INTEGRATION
    createType("text", "vault_path", "/data/storage/soar1/integrations/vault", false, ["integration"]);

    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // STORAGE
    createType("text", "path", "/data/storage/soar1", false, ["storage"]);
    createType("number", "max_file_size", 10737418240, false, ["storage"]);
    createType("number", "max_threads", 10, false, ["storage"]);

    // COMMANDS
    createType("text","path", "/data/storage/soar1/commands", false, ["commands"]);

    // QUEUE
    createType("number", "max_queue_size", 500, false, ["queue"]);
    createType("text", "backup_file", "/data/data_soar_backup.txt", false, ["queue"]);
    createType("text", "stats_file", "stats.txt", false, ["queue"]);
    createType("number", "max_backup_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);
    // AUTHENTICATOR
    createType("text", "id", "&authenticator1", false, ["authenticator"]);

    // INDEXSEARCHMOTOR
    createType("text", "id", "&indexsearchmotor1", false, ["indexsearchmotor"]);

    //TASK MANAGER
    createType("text", "index", "soar", false, ["task"]);
    createType("text", "tenant", "soar_tasks", false, ["task"]);
    createType("text", "technology","scheduler", false, ["task"]);
    createType("text", "credentials", "scheduler", false, ["task"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showLogParserForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "logparser1");
    createType("text", "type", "logparser", true);
    createType("text", "image", "ttdantett/siem_logparser", true);
    // createType("text", "delimiter", "(CEF:0\\|.*|CEF:1\\|.*)");
    createType("text", "tenant", "Tenant - Customer 1");

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "logparsercoordinator.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);


    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // WEBHOOK
    createType("text", "host", "logparser1", false, ["webhook"]);
    createType("number", "port", 5100, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // LOGCOLLECTOR
    createType("text", "id", "&logcollector1", false, ["logcollector"]);
    createType("number", "size", 500, false, ["logcollector"]);
    // createType("text", "host", "localhost", false, ["logcollector"]);
    // createType("number", "port", 5000, false, ["logcollector"]);
    // createType("text", "protocol", "tcp", false, ["logcollector"]);
    createType("text", "auth_token", "my_secure_token", false, ["logcollector"]);

    // QUEUE
    createType("number", "max_queue_size", 8192, false, ["queue"]);
    createType("text", "backup_file", "/data/data_backup_parser.txt", false, ["queue"]);
    createType("text", "stats_file", "/data/stats_parser.txt", false, ["queue"]);
    createType("number", "max_backup_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);

    // PLUGINS
    createType("text", "parser_folder", "LPPlugins.parser", false, ["plugins"]);
    createType("text", "prefilter_folder", "LPPlugins.prefiltering", false, ["plugins"]);
    createType("text", "postfilter_folder", "LPPlugins.postfiltering", false, ["plugins"]);
    createType("text", "categorizer_folder", "LPPlugins.categorisation", false, ["plugins"]);
    createType("text", "anonymizer_folder", "LPPlugins.anonymization", false, ["plugins"]);
    createType("text", "agregator_folder", "LPPlugins.agregation", false, ["plugins"]);
    // createType("text", "mapper_folder", "LPPlugins.mapping", false, ["plugins"]);

    // PARSER
    createType("text", "type", "regex", false, ["parser"]);
    createType("text", "name", "Multiple", false, ["parser"]);
    createType("text", "technology", "Multiple", false, ["parser"]);
    createType("text", "version", "1.0", false, ["parser"]);

    // MAPPER
    // createType("text", "name", "SimpleMapping", false, ["mapper"]);

    // AGREGATOR
    createType("text", "name", "SimpleAgregation", false, ["agregator"]);

    // PREFILTER
    createType("text", "name", "SimplePreFilter", false, ["prefilter"]);
    createType("text", "filter", "CEF:0|Elastic|Vaporware", false, ["prefilter"]);
    createType("boolean", "out", false, false, ["prefilter"]);

    // POSTFILTER
    createType("text", "name", "SimplePostFilter", false, ["postfilter"]);
    createType("text", "filter", {}, false, ["postfilter"]);
    createType("boolean", "out", false, false, ["postfilter"]);

    // CATEGORIZER
    createType("text", "name", "SimpleCategorisation", false, ["categorizer"]);

    // ANONYMIZER
    createType("text", "name", "SimpleAnonymization", false, ["anonymizer"]);
    createType("text", "fields", "duser,suser", false, ["anonymizer"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });

}


function showLogIndexerForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "logindexer1");
    createType("text", "type", "logindexer", true);
    createType("text", "image", "ttdantett/siem_logindexer", true);
    // READ WRITE POLICY
    createType("boolean", "write", false, false,["read_write"]);
    // createType("boolean", "primary", true, false);

    // createType("boolean", "primary", true, false);
    // createType("boolean", "monitoring", false, false);

    // LIFECYCLE POLICY
    createType("number", "frequency", 300, false, ["lifecycle"]);
        // Encryption
    createType("number", "delay", -1, false, ["encryption"]);
    createType("text", "algorithm", "AES256", false, ["encryption"]);
    createType("text", "key_path", "/data/keys/encryption_keys", false, ["encryption"]);
    createType("text", "iv_path", "/data/keys/encryption_iv", false, ["encryption"]);
        // Compression
    createType("number", "delay", -1, false, ["compression"]);
    createType("text", "algorithm", "TAR", false, ["compression"]);
        // Deletion
    createType("number", "delay", -1, false, ["deletion"]);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // STORAGE
    createType("text", "path", "/data/storage/logindexer1", false, ["storage"]);
    createType("number", "max_file_size", 10737418240, false, ["storage"]);
    createType("number", "index_size", 10737418240, false, ["storage"]);
    createType("text", "index_name", "index_name_1", false, ["storage"]);
    createType("number", "index_saving_frequency", 15, false, ["storage"]);
    createType("number", "max_threads", 10, false, ["storage"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "logindexercoordinator.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "logindexer1", false, ["webhook"]);
    createType("number", "port", 5200, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // // LOGPARSER
    // createType("text", "id", "&logparser1", false, ["logparser"]);
    // createType("number", "size", 500, false, ["logparser"]);
    // createType("text", "auth_token", "my_secure_token", false, ["logparser"]);

    // QUEUE
    createType("number", "max_queue_size", 8192, false, ["queue"]);
    createType("text", "backup_file", "/data/data_backup_indexers_1.txt", false, ["queue"]);
    createType("text", "stats_file", "/data/stats_indexers_1.txt", false, ["queue"]);
    createType("number", "max_backup_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);

    // // LOGSERVICES
    createType("list_object", "logservice", "logparser1", false, ["logservices"]);

    // TODO manage for primary and monitoring and others configurations

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });

}


function showIndexSearchMotorForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "indexsearchmotor1");
    createType("text", "type", "indexsearchmotor", true);
    createType("text", "image", "ttdantett/siem_indexsearchmotor", true);
    createType("number", "max_threads", 16);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);


    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "indexsearchmotor.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "indexsearchmotor1", false, ["webhook"]);
    createType("number", "port", 5011, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // INDEXERS
    createType("list_object", "indexers", "dedicatedindexsearchmotor1", false, ["indexers"]);

    // AUTHENTICATOR
    createType("text", "id", "&authenticator1", false, ["authenticator"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showAuthenticatorForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "authenticator1");
    createType("text", "type", "authenticator", true);
    createType("text", "image", "ttdantett/siem_authenticator", true);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // STORAGE
    createType("text", "path", "/data/storage/authenticator1", false, ["storage"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "authenticator.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "authenticator1", false, ["webhook"]);
    createType("number", "port", 7000, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // SLAVECOORDINATOR
    createType("text", "id", "", false, ["slavecoordinator"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showDedicatedIndexSearchMotorForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "dedicatedindexsearchmotor1");
    createType("text", "type", "dedicatedindexsearchmotor", true);
    createType("text", "image", "ttdantett/siem_dedicatedindexsearchmotor", true);
    createType("boolean", "primary", true, false);
    createType("text", "group", "dedicatedindexsearchmotor1", false);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // STORAGE
    createType("text", "path", "/data/storage/logindexer1", false, ["storage"]);
    createType("number", "max_file_size", 25000, false, ["storage"]);
    createType("number", "index_size", 8192, false, ["storage"]);
    createType("text", "index_name", "index_name_1", false, ["storage"]);
    createType("number", "index_saving_frequency", 10, false, ["storage"]);
    createType("number", "max_threads", 10, false, ["storage"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "dedicatedindexsearchmotor.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "dedicatedindexsearchmotor1", false, ["webhook"]);
    createType("number", "port", 5300, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // QUEUE
    createType("number", "max_queue_size", 8192, false, ["queue"]);
    createType("text", "backup_file", "/data/data_backup_dedicatedindexers_1.txt", false, ["queue"]);
    createType("text", "stats_file", "/data/stats_dedicatedindexers_1.txt", false, ["queue"]);
    createType("number", "max_backup_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);


    // CACHE
    createType("text", "id", "&cachesystem1", false, ["cache"]);
    // createType("text", "host", "127.0.0.1", false, ["cache"]);
    // createType("number", "port", 5020, false, ["cache"]);
    createType("text", "auth_token", "my_secure_token", false, ["cache"]);
    // createType("text", "certfile", "certs/server.crt", false, ["cache", "certs"]);
    // createType("text", "keyfile", "certs/server.key", false, ["cache", "certs"]);

    // AUTHENTICATOR
    createType("text", "id", "&authenticator1", false, ["authenticator"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}


function showUserInterfaceForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "userinterface1");
    createType("text", "type", "userinterface", true);
    createType("text", "image", true, "ttdantett/siem_userinterface");

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // QUEUE
    createType("number", "max_queue_size", 8192, false, ["queue"]);
    createType("text", "backup_file", "/data/data_backup_userinterface_1.txt", false, ["queue"]);
    createType("number", "backup_max_file", 50, false, ["queue"]);
    createType("number", "max_backup_file_size", 1073741824, false, ["queue"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "userinterface.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBSERVER
    createType("text", "host", "userinterface1", false, ["webserver"]);
    createType("number", "port", 443, false, ["webserver"]);
    createType("text", "auth_token", "my_secure_token", false, ["webserver"]);
    createType("text", "certfile", "certs/server.crt", false, ["webserver", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webserver", "certs"]);

    // WEBHOOK
    createType("text", "host", "dedicatedindexsearchmotor1", false, ["webhook"]);
    createType("number", "port", 5300, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // REPORTING INDEX
    //createType("text", "index", "soar", false, ["reporting"]);

    // INDEXSEARCHMOTORS (first element of the list)
    createType("text", "id", "&indexsearchmotor1", false, ["indexsearchmotor"]);
    // createType("text", "host", "0.0.0.0", false, ["indexsearchmotors", "0"]);
    // createType("number", "port", 5600, false, ["indexsearchmotors", "0"]);
    // createType("text", "auth_token", "my_secure_token", false, ["indexsearchmotor"]);

    // AUTHENTICATOR(First element of the list)
    createType("text", "id", "&authenticator1", false, ["authenticator"]);
    // createType("text", "host", "0.0.0.0", false, ["mastercoordinators", "0"]);
    // createType("number", "port", 6000, false, ["mastercoordinators", "0"]);
    // createType("text", "auth_token", "my_secure_token", false, ["slavecoordinator"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}


function showCacheSystemForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "cachesystem1");
    createType("text", "type", "cachesystem", true);
    createType("text", "image", "ttdantett/siem_cachesystem", true);

    // WEBREQUESTER
    createType("number", "timeout", 120, false, ["webrequester"]);
    createType("text", "proxy", "", false, ["webrequester"]);
    createType("text", "slave_id", "", false, ["webrequester", "slave_reverse"]);

    // VOLUMES
    createType("text", "bind", "/data/", false, ["volumes", "dockervolume1"]);
    createType("text", "mode", "rw", false, ["volumes", "dockervolume1"]);

    // STORAGE
    createType("text", "path", "/data/storage/cache", false, ["storage"]);
    createType("number", "max_file_size", 25000, false, ["storage"]);
    createType("text", "index_name", "index_name_1", false, ["storage"]);
    createType("number", "index_saving_frequency", 10, false, ["storage"]);
    createType("number", "max_threads", 10, false, ["storage"]);
    createType("number", "max_cache_items", 1000, false, ["storage"]);

    // LOGGER
    createType("text", "log_level", "info", false, ["logger"]);
    createType("text", "log_path", "cachesystem.log", false, ["logger"]);
    createType("number", "max_queue_size", 8192, false, ["logger"]);
    createType("number", "max_file", 50, false, ["logger"]);
    createType("number", "max_file_size", 1073741824, false, ["logger"]);
    createType("boolean", "enable_print", true, false, ["logger"]);
    createType("boolean", "enable_queue", true, false, ["logger"]);
    createType("boolean", "enable_file", true, false, ["logger"]);

    // WEBHOOK
    createType("text", "host", "cachesystem1", false, ["webhook"]);
    createType("number", "port", 5400, false, ["webhook"]);
    createType("text", "auth_token", "my_secure_token", false, ["webhook"]);
    createType("text", "certfile", "certs/server.crt", false, ["webhook", "certs"]);
    createType("text", "keyfile", "certs/server.key", false, ["webhook", "certs"]);

    // AUTHENTICATOR
    createType("text", "id", "&authenticator1", false, ["authenticator"]);

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}


// PRIVILEGES PART

function showUsersForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "user1");
    createType("text", "type", "user", true);
    createType("text", "name", "user1");
    // createType("text", "password", "Comple-xPas^s495");
    // createType("text", "email", "user1@example.com");
    // createType("boolean", "disabled", false);
    // createType("text", "authentication_type", "local");

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showResourcesForm() {
    $("#form-fields").empty();

    // Racine
    createType("text", "id", "resource1");
    createType("text", "name", "resource1");
    createType("text", "description", "resource1 comment");

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });
}

function showRolesForm() {
    $("#form-fields").empty();

    createType("text", "id", "role1");
    createType("text", "name", "role1");

    $('button.collapsible').on('click', function() {
        $(this).next('.collapsed-content').slideToggle();
    });

}

document.getElementById("add-element-button").onclick = function () {
    // Main variables with extended scope
    let selectedId = null; // can be used selectedAuthenticatorId or  selectedCoordinatorId
    let selectedElement = null;

    // Detect option selected
    const selectedOption = $('#configuration-path').val();

    if (selectedOption === "globalconfiguration") {
        // Global confiugration
        selectedElement = $("#element-selector-globalconfiguration").val();
        selectedId = $("#slave-coordinator").val();

        if (!selectedId || !selectedElement) {
            alert("Please fill all required fields and select a Slave Coordinator.");
            return;
        }
    }
    else if (selectedOption === "globalauthorisation") {
        // Authorization global
        console.log("In change global authorisation");
        selectedElement = $("#element-selector-globalauthorisation").val();
        selectedId = $("#authenticator").val();

        console.log("selectedElement:", selectedElement);
        console.log("selectedId (Authenticator):", selectedId);

        if (!selectedId || !selectedElement) {
            alert("Please fill all required fields and select an authenticator.");
            return;
        }
    }

    // Create dynamically object "newElement" from form fields
    const newElement = {};
    $("#form-fields :input").each(function () {
        try {
            const fieldPath = $(this).data("json-name") || $(this).attr("name");
            const fieldType = $(this).attr("type") || $(this).prop("tagName").toLowerCase();
            const defaultValue = $(this).attr("placeholder");
            let fieldValue = $(this).val();

            // Use default value if empty field
            if (fieldValue === "" && defaultValue !== undefined) {
                fieldValue = defaultValue;
            }

            // Build embedded object
            const pathParts = fieldPath.split('.');
            let currentLevel = newElement;

            for (let i = 0; i < pathParts.length - 1; i++) {
                const part = pathParts[i];
                if (!currentLevel[part]) {
                    currentLevel[part] = isNaN(parseInt(pathParts[i + 1])) ? {} : [];
                }
                currentLevel = currentLevel[part];
            }

            const finalKey = pathParts[pathParts.length - 1];
            if (fieldType === "checkbox" || fieldType === "radio") {
                currentLevel[finalKey] = $(this).is(":checked");
            } else if (fieldType === "number") {
                currentLevel[finalKey] = parseInt(fieldValue);
            } else if (fieldType === "boolean") {
                currentLevel[finalKey] = ["true", "1", "yes"].includes(fieldValue.toString().trim().toLowerCase());
            } else if (fieldType === "list") {
                currentLevel[finalKey] = fieldValue.split(",").map(item => item.trim()).filter(item => item);
            } else {
                currentLevel[finalKey] = fieldValue;
            }
        } catch (error) {
            console.error("Error processing form fields:", error);
        }
    });

    // Add JSON function to configuration depending on option selected
    if (selectedOption === "globalconfiguration") {
        const slaveCoordinators = json_data.infrastructure.slavecoordinators;
        const coordinator = slaveCoordinators.find(sc => sc.id === selectedId);

        if (!coordinator) {
            alert("Slave coordinator does not exist. Please create it first.");
            return;
        }

        // Add new element in sub-infrastructure
        coordinator["sub-infrastructure"] = coordinator["sub-infrastructure"] || {};
        coordinator["sub-infrastructure"][selectedElement] = coordinator["sub-infrastructure"][selectedElement] || [];
        coordinator["sub-infrastructure"][selectedElement].push(newElement);
    }
    else if (selectedOption === "globalauthorisation") {
        const authenticators = json_data.infrastructure.authenticators;
        const authenticator = authenticators.find(auth => auth.id === selectedId);

        if (!authenticator) {
            alert("Authenticator does not exist. Please create it first.");
            return;
        }

        // Add new element to authenticator
        authenticator[selectedElement] = authenticator[selectedElement] || [];
        authenticator[selectedElement].push(newElement);
    }

    // Update JSON editor
    editor.set(json_data);
    alert("Element added successfully!");
};



// Save JSON data on button click
document.getElementById("save-button").onclick = function () {
    var updated_json = editor.get();

    // var selectedOption = document.getElementById("configuration-path").value;
    // updated_json.optionselected = selectedOption;

    $.ajax({
        url: "",
        type: "POST",
        data: JSON.stringify(updated_json),
        contentType: "application/json",
        success: function (response) {
            alert("JSON data saved successfully!");
            location.reload();
        },
        error: function () {
            alert("An error occurred while saving JSON data.");
        }
    });
};

$(document).ready(function() {
    var selectedOption = $('#configuration-path').val();

    //Depending on the selected option activate the right fields
    // Call function to populate options on page load
    if (selectedOption === "globalconfiguration") {
        $("#slave-selector")[0].style.display = "block";
        $("#authenticator")[0].style.display = "none";
        populateSlaveCoordinatorOptions();
        $("#group-element-selector-globalconfiguration")[0].style.display = "block";
        $("#group-element-selector-globalauthorisation")[0].style.display = "none";
    }
    else if (selectedOption === "globalauthorisation") {
        $("#slave-selector")[0].style.display = "none";
        $("#authenticator")[0].style.display = "block";
        popupaleAuthenticatorOption();
        $("#group-element-selector-globalauthorisation")[0].style.display = "block";
        $("#group-element-selector-globalconfiguration")[0].style.display = "none";
        // TODO : Add the right fields
    }
    else {
        $("#slave-selector")[0].style.display = "none";
        $("#authenticator")[0].style.display = "none";
        $("#group-element-selector-globalauthorisation")[0].style.display = "none";
        $("#group-element-selector-globalconfiguration")[0].style.display = "none";
    }
    // Detect option selected modification
    $('#configuration-path').change(function() {
        selectedOption = $(this).val();

        // Reload page with option selected parameter
        window.location.href = `/configuration?option=${selectedOption}`;
    });
});

