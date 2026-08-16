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
document: utils
*/

let loadingStartTime;
let loadingInterval;

$(document).ready(function() {
    
        // Function to load and display checkboxes for indexes in a searchable dropdown
        $.ajax({
            url: '/search_available_index',
            method: 'GET',
            success: function(data) {
                var indexSelect = $('#indexSelect');
                data.forEach(function(item) {
                    indexSelect.append(`<option value="${item}">${item}</option>`);
                });
                indexSelect.dropdown({ allowAdditions: true, placeholder: "Select indexes" }); // Initialize dropdown with search
            }
        });
    
        // Function to load and display checkboxes for tenants in a searchable dropdown
        $.ajax({
            url: '/search_available_tenant',
            method: 'GET',
            success: function(data) {
                var tenantSelect = $('#tenantSelect');
                data.forEach(function(item) {
                    tenantSelect.append(`<option value="${item}">${item}</option>`);
                });
                tenantSelect.dropdown({ allowAdditions: true, placeholder: "Select tenants" }); // Initialize dropdown with search
            }
        });
    
        // Function to load and display checkboxes for technologies in a searchable dropdown
        $.ajax({
            url: '/search_available_technologies', // URL endpoint to get technologies
            method: 'GET',
            success: function(data) {
                var technologySelect = $('#technologySelect');
                data.forEach(function(item) {
                    technologySelect.append(`<option value="${item}">${item}</option>`);
                });
                technologySelect.dropdown({ allowAdditions: true, placeholder: "Select technologies" }); // Initialize dropdown with search
            }
        });


        // const downloadButton = document.getElementById('downloadResults');
        // if(downloadButton) {
        //     document.getElementById('downloadResults').addEventListener('click', async function () {
        //         const tableContainer = document.getElementById('tableContainer');
            
        //         if (!tableContainer) {
        //         alert('No content to export.');
        //         return;
        //         }
            
        //         // Creation of selection box to choose file format
        //         const formatSelection = document.createElement('select');
        //         const formats = ['pdf', 'png', 'jpeg', 'csv'];
            
        //         formats.forEach(format => {
        //             const option = document.createElement('option');
        //             option.value = format;
        //             option.textContent = format.toUpperCase();
        //             formatSelection.appendChild(option);
        //         });
            
        //         const dialog = document.createElement('div');
        //         dialog.style.position = 'fixed';
        //         dialog.style.left = '50%';
        //         dialog.style.top = '50%';
        //         dialog.style.transform = 'translate(-50%, -50%)';
        //         dialog.style.backgroundColor = 'white';
        //         dialog.style.padding = '20px';
        //         dialog.style.border = '1px solid #ccc';
        //         dialog.style.zIndex = '1000';
            
        //         const confirmButton = document.createElement('button');
        //         confirmButton.textContent = 'Export';
            
        //         const cancelButton = document.createElement('button');
        //         cancelButton.textContent = 'Cancel';
        //         cancelButton.style.marginLeft = '10px';
            
        //         dialog.appendChild(document.createTextNode('Choose export format: '));
        //         dialog.appendChild(formatSelection);
        //         dialog.appendChild(confirmButton);
        //         dialog.appendChild(cancelButton);
        //         document.body.appendChild(dialog);
            
        //         return new Promise((resolve) => {
        //             confirmButton.addEventListener('click', async function () {
        //                 const selectedFormat = formatSelection.value;
        //                 dialog.remove();
        //                 try {
        //                     // Get content of div in HTML
        //                 const content = tableContainer.outerHTML;
                
        //                 if (selectedFormat === 'pdf') {
        //                     const pdf = new jsPDF({
        //                     orientation: 'landscape',
        //                     unit: 'px',
        //                     format: 'letter'
        //                     });

        //                     // Add content HTML in pdf
        //                     pdf.html(content, {
        //                     callback: function (pdf) {
        //                         pdf.save('exported-content.pdf');
        //                     },
        //                     x: 10,
        //                     y: 10
        //                     });
                
        //                 } else {
        //                     // Convert content HTML in one image (PNG or JPEG)
        //                     const imageData = await html2canvas(tableContainer).then(canvas => {
        //                     return canvas.toDataURL(`image/${selectedFormat === 'jpeg' ? 'jpeg' : 'png'}`);
        //                     });
                
        //                     const link = document.createElement('a');
        //                     link.href = imageData;
        //                     link.download = `exported-content.${selectedFormat}`;
        //                     document.body.appendChild(link);
        //                     link.click();
        //                     document.body.removeChild(link);
        //                 }
        //                 } catch (error) {
        //                 console.error('Error during exportation:', error);
        //                 alert('Error during export, please try again or use another format.');
        //                 }
        //             });
                
        //             cancelButton.addEventListener('click', function () {
        //                 dialog.remove();
        //             });
                
        //         });
        //     });
        // }



        
const downloadButton = document.getElementById('downloadResults');
if (downloadButton) {
    downloadButton.addEventListener('click', async function () {

        const $tableContainer = $('#tableContainer');
        const chartCanvas = document.getElementById('myChart');

        const tableVisible = $tableContainer.is(':visible') && $tableContainer.find('table tbody tr').length > 0;
        const chartVisible = !tableVisible
            && chartCanvas
            && typeof myChart !== 'undefined'
            && myChart
            && chartCanvas.width > 0
            && chartCanvas.height > 0;

        let exportTarget = null;
        let canvasElement = null;
        let hasTable = false;

        if (tableVisible) {
            exportTarget = $tableContainer[0];
            captureTarget = document.getElementById('dataTable_wrapper');
            if (!captureTarget) {
                console.error('No DataTable_wrapper element not found in the DOM.');
            }
            else {
                exportTarget = captureTarget;
            }
            hasTable = true;
        } else if (chartVisible) {
            exportTarget = chartCanvas;
            canvasElement = chartCanvas;
        } else {
            alert('No content to export.');
            return;
        }

        // Create Modal Selection Dialog
        const dialog = document.createElement('div');
        Object.assign(dialog.style, {
            position: 'fixed',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            padding: '20px',
            border: '1px solid #ccc',
            boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
            zIndex: '1000',
            borderRadius: '8px'
        });

        const formatSelection = document.createElement('select');

        const formats = [
            { label: 'PDF', value: 'pdf' },
            { label: 'PNG', value: 'png' },
            { label: 'JPEG', value: 'jpeg' }
        ];

        // CSV only if datatable
        if (hasTable) {
            formats.push({ label: 'CSV', value: 'csv' });
            //formats.push({ label: 'CSV (Full Report)', value: 'full_csv' });
        }

        formats.forEach(f => {
            const option = document.createElement('option');
            option.value = f.value;
            option.textContent = f.label;
            formatSelection.appendChild(option);
        });

        const confirmButton = document.createElement('button');
        confirmButton.textContent = 'Export';
        confirmButton.style.padding = '10px';
        confirmButton.classList.add("styled-button");

        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancel';
        cancelButton.style.padding = '10px';
        cancelButton.classList.add("styled-button");

        dialog.appendChild(document.createTextNode('Choose export format: '));
        dialog.appendChild(formatSelection);
        dialog.appendChild(confirmButton);
        dialog.appendChild(cancelButton);
        document.body.appendChild(dialog);

        // Event Handling
        confirmButton.addEventListener('click', async function () {
            const selectedFormat = formatSelection.value;
            dialog.remove();

            try {
                if (selectedFormat === 'full_csv') {
                    alert('Full report export functionality will be implemented here.');
                    return;
                }

                // ==========================================
                // CSV EXPORT
                // ==========================================
                if (selectedFormat === 'csv') {
                    const rows = exportTarget.querySelectorAll('tbody tr, thead tr');
                    let csvLines = [];

                    rows.forEach(row => {
                        if (row.offsetParent === null && row.offsetHeight === 0) return;

                        const cols = row.querySelectorAll('th, td');
                        const rowData = Array.from(cols).map(col => {
                            let text = col.innerText || col.textContent || '';
                            text = text.replace(/"/g, '""');
                            return `"${text.trim()}"`;
                        }).join(',');

                        if (rowData.trim().length > 0) {
                            csvLines.push(rowData);
                        }
                    });

                    const uniqueCsvLines = [...new Set(csvLines)];
                    const csvContent = uniqueCsvLines.join('\r\n');

                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    const url = URL.createObjectURL(blob);
                    downloadFile(url, 'exported-content.csv');
                    return;
                }

                // ==========================================
                // IMAGE / PDF EXPORT
                // ==========================================
                let canvas;

                if (canvasElement) {
                    // Direct screenshot of canvas Chart.js, render empty for canvas
                    canvas = canvasElement;
                } else {
                    if (!captureTarget) {
                        throw new Error('Element to export not found (dataTable_wrapper).');
                    }
                    // Table : Screenshot DOM classical with html2canvas
                    canvas = await html2canvas(exportTarget, {
                        scale: 2,
                        useCORS: true,
                        logging: false,
                        allowTaint: true
                    });
                }

                if (!canvas || !canvas.width || !canvas.height) {
                    throw new Error('Error during export content.');
                }

                if (selectedFormat === 'pdf') {
                    let imgData;
                    try {
                        imgData = canvas.toDataURL('image/png');
                    } catch (e) {
                        throw new Error('Error: Impossible to read the canvas');
                    }

                    const jsPDFClass = window.jspdf ? window.jspdf.jsPDF : window.jsPDF;
                    if (!jsPDFClass) {
                        throw new Error('jsPDF library is not loaded on the page.');
                    }

                    const pdf = new jsPDFClass('landscape', 'pt', 'a4');
                    const pageWidth = pdf.internal.pageSize.getWidth();

                    const margin = 20;
                    const maxImgWidth = pageWidth - (margin * 2);
                    const ratio = maxImgWidth / canvas.width;
                    const renderWidth = maxImgWidth;
                    const renderHeight = canvas.height * ratio;

                    pdf.addImage(imgData, 'PNG', margin, margin, renderWidth, renderHeight);
                    pdf.save('exported-content.pdf');
                } else {
                    const mimeType = selectedFormat === 'jpeg' ? 'image/jpeg' : 'image/png';
                    let imageData;
                    try {
                        imageData = canvas.toDataURL(mimeType);
                    } catch (e) {
                        throw new Error('Error: Impossible to read canvas.');
                    }
                    downloadFile(imageData, `exported-content.${selectedFormat}`);
                }

            } catch (error) {
                console.error('Error during exportation:', error);
                alert('Error during export: ' + error.message);
            }
        });

        cancelButton.addEventListener('click', function () {
            dialog.remove();
        });
    });
}









        // Utility function to trigger browser file download
        function downloadFile(url, filename) {
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

});

// Function to get selected indexes, tenants, and technologies
function getSelectedValues() {
    const selectedIndexes = $('#indexSelect').dropdown('get value'); // Get selected indexes
    const selectedTenants = $('#tenantSelect').dropdown('get value'); // Get selected tenants
    const selectedTechnologies = $('#technologySelect').dropdown('get value'); // Get selected technologies

    return { selectedIndexes, selectedTenants, selectedTechnologies };
}

// Function to convert date in UTC format
function formatDateToUTC(date) {
    const utcDate = new Date(date);
    const year = utcDate.getUTCFullYear();
    const month = String(utcDate.getUTCMonth() + 1).padStart(2, '0');
    const day = String(utcDate.getUTCDate()).padStart(2, '0');
    const hours = String(utcDate.getUTCHours()).padStart(2, '0');
    const minutes = String(utcDate.getUTCMinutes()).padStart(2, '0');
    const seconds = String(utcDate.getUTCSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function renderJsonAsExpandableHtml(data) {
    if (typeof data !== 'object' || data === null) {
        return `<span>${String(data)}</span>`;
    }

    if (Array.isArray(data)) {
        return `
            <details>
                <summary style="cursor: pointer;">Details</summary>
                <ul style="padding-left: 20px; list-style-type: none;">
                    ${data.map((item, index) => `
                        <li>
                            ${typeof item === 'object' && item !== null
                                ? renderJsonAsExpandableHtml(item).replace(
                                    '<details>',
                                    `<details><summary style="cursor: pointer;">[${index}]</summary>`
                                )
                                : `<strong>[${index}]</strong>: ${renderJsonAsExpandableHtml(item)}`
                            }
                        </li>
                    `).join("")}
                </ul>
            </details>
        `;
    } else {
        return `
            <details>
                <summary style="cursor: pointer;">Details</summary>
                <ul style="padding-left: 20px; list-style-type: none;">
                    ${Object.entries(data).map(([key, value]) => `
                        <li>
                            ${typeof value === 'object' && value !== null
                                ? renderJsonAsExpandableHtml(value).replace(
                                    '<details><summary style="cursor: pointer;">Details</summary>',
                                    `<details><summary style="cursor: pointer;">${key}</summary>`
                                )
                                : `<strong>${key}</strong>: ${renderJsonAsExpandableHtml(value)}`
                            }
                        </li>
                    `).join("")}
                </ul>
            </details>
        `;
    }
}



function validateAndCorrectData(data, keys) {
    console.log("Validating and correcting data...");
    console.log("Keys:", keys);
    console.log("Data:", data);
    console.log("Data Type of first element:", typeof(data[0]));

    return data.map(row => {
        let correctedRow = {};
        keys.forEach(key => {
            let value = row.hasOwnProperty(key) ? row[key] : "";

            // If object or a table, convert in HTML 
            if (value && typeof value === 'object') {
                try {
                    value = renderJsonAsExpandableHtml(value);
                } catch (e) {
                    console.warn(`Error during field conversion "${key}":`, e);
                    value = "";
                }
            }

            // If a string content siem_linktype/url:
            if (typeof value === "string") {
                try {
                    const match = value.match(/siem_linktype\/url:(\S+)/);
                    if (match) {
                        value = siemCreateLink(match[1]); 
                    }
                } catch (e) {
                    console.warn(`Error during field conversion "${key}":`, e);
                    value = "";
                }
            }

            correctedRow[key] = value;
        });
        return correctedRow;
    });
}



function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function loadingSpinnerShow(label) {
    // Save hours loading start
    loadingStartTime = new Date();

    // Display spinner
    $('#loadingSpinner').show();
    $('#loadingSpinnerLabel').text(label);

    // Start interval to update after timeout
    loadingInterval = setInterval(() => {
        const elapsedTime = Math.floor((new Date() - loadingStartTime) / 1000); // time out in seconds
        $('#loadingSpinnerLabel').text(`${label} (${elapsedTime}s)`);
    }, 1000); // Update each seconds
}

function loadingSpinnerHide() {
    $('#loadingSpinner').hide();
    $('#loadingSpinnerLabel').text('');
    clearInterval(loadingInterval);
}

function userinterfaceclean(dataTable, graph) {
    // Destroy datatable
    destroyTable();

    // Change the current page
    $("#currentPage").val(0);
    $("#totalpages")[0].innerText = "Total Pages: 0";
    $("#totalitems")[0].innerText = "Total Items: 0";
    $("#startindex")[0].innerText = "Start Items: 0";
    $("#endindex")[0].innerText = "End Items: 0";

    // Reset the fields 
    fieldsProjected = null;

    // Reset current page size to default 10
    currentPageSize = 10;
    $('#pageSize').val(10);

    // Chart destroy
    destroyChart();

    // Hide table panel
    displayTablePanel(false);
}

function toggleFieldset(buttonId, inputId, numberId, presetId) {
    $(`#${buttonId}`).click(function() {
        const isDisabled = $(`#${inputId}`).prop('disabled');
        $(`#${inputId}, #${numberId}, #${presetId}`).prop('disabled', !isDisabled);
    });
}

function linkCalendarAndPreset(calendarId, numberId, presetId) {
    // Disable calendar if a preset is selected, selse disabled preset 
    // and the number if calendar selected
    $(`#${presetId}, #${numberId}`).on('input change', function() {
        const isPresetSelected = $(`#${presetId}`).val() !== '' && $(`#${numberId}`).val() !== '';
        $(`#${calendarId}`).prop('disabled', isPresetSelected);
    });

    $(`#${calendarId}`).on('input', function() {
        const isCalendarUsed = $(this).val() !== '';
        $(`#${presetId}, #${numberId}`).prop('disabled', isCalendarUsed);
    });
}

function formatDateToUTC(date) {
    const d = new Date(date);
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')} ` +
           `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}:${String(d.getUTCSeconds()).padStart(2, '0')}`;
}

function calculateDateFromPreset(number, preset) {
    const now = new Date();
    if (!number || isNaN(number) || !preset) return null;

    switch (preset) {
        case 'minutes': now.setMinutes(now.getMinutes() - number); break;
        case 'hours': now.setHours(now.getHours() - number); break;
        case 'days': now.setDate(now.getDate() - number); break;
        case 'weeks': now.setDate(now.getDate() - 7 * number); break;
        case 'months': now.setMonth(now.getMonth() - number); break;
        case 'quarters': now.setMonth(now.getMonth() - 3 * number); break;
        case 'years': now.setFullYear(now.getFullYear() - number); break;
    }
    return formatDateToUTC(now);
}

function getActiveDate(calendarId, numberId, presetId) {
    // If calendar is active, return date
    if (!$(`#${calendarId}`).prop('disabled') && $(`#${calendarId}`).val()) {
        return formatDateToUTC($(`#${calendarId}`).val());
    }
    // If preset and number are actives, compute date
    else if (!$(`#${numberId}`).prop('disabled') && !$(`#${presetId}`).prop('disabled')) {
        const number = parseInt($(`#${numberId}`).val(), 10);
        const preset = $(`#${presetId}`).val();
        return calculateDateFromPreset(number, preset);
    }
    return null;
}

// Function markdown simple for widget.
function simpleMarkdownToHTML(markdown) {
    if(!markdown) return "";
    return markdown
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2">$1</a>')
        .replace(/\n$/gim, '<br>');
}

function getSelectedOptionValue(selectId) {
    const selectElement = document.getElementById(selectId);
    return selectElement.value; 
}


// Check  if parameter call the report list
function checkQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has(param)) {
        return true;
    }
    return false;
}


function resetResearchTimeout() {
    fetch('/reset_research_timeout', { method: 'GET' })
        .catch(error => console.error('Error during request:', error));
}

function siemCreateLink(url) {
    if (!url) {
        return `<span style="color:red;">[Invalid SIEM link]</span>`;
    }

    const isAbsolute = /^(http|https):\/\//.test(url);
    const fullUrl = isAbsolute ? url : `${window.location.origin}/${url}`;

    return `<a href="${fullUrl}" target="_blank" 
               style="color:#0d6efd; font-weight:bold; text-decoration:none;">
               ${fullUrl}
            </a>`;
}