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
project: siem project
DOCUMENT: dropdownlist

*/

class DropdownList {
    /**
     * @param {string} label - Label of field.
     * @param {string} endpoint - URL of API to call.
     * @param {string} targetId - ID of HTML container.
     * @param {boolean} isMultiple - Authorize multiple selection.
     * @param {Object|Function} queryParams - Object or function returning dynamics parameters.
     */
    constructor(label, endpoint, targetId, isMultiple = true, queryParams = {}) {
        this.label = label;
        this.endpoint = endpoint;
        this.targetId = targetId;
        this.isMultiple = isMultiple;
        this.queryParams = typeof queryParams === 'function' ? queryParams : () => queryParams;
        this.dropdownId = `${this.targetId}Dropdown`;
        this.init();
    }

    init() {
        this.createDropdownHTML();
        this.loadData();
    }

    createDropdownHTML() {
        const container = document.getElementById(this.targetId);
        if (!container) {
            console.error(`Container with ID "${this.targetId}" not found.`);
            return;
        }

        const labelElement = document.createElement('label');
        labelElement.textContent = this.label;

        const selectElement = document.createElement('select');
        selectElement.id = this.dropdownId;
        selectElement.className = 'ui fluid search dropdown';

        if (this.isMultiple) {
            selectElement.setAttribute('multiple', '');
        }

        container.appendChild(labelElement);
        container.appendChild(selectElement);
    }

    buildUrlWithParams() {
        const url = new URL(this.endpoint, window.location.origin);
        const dynamicParams = this.queryParams();
        Object.entries(dynamicParams).forEach(([key, value]) => {
            url.searchParams.append(key, value);
        });
        return url.toString();
    }

    loadData() {
        return new Promise((resolve, reject) => {
            const selectElement = document.getElementById(this.dropdownId);
            if (!selectElement) {
                console.error(`Dropdown with ID "${this.dropdownId}" not found.`);
                return reject();
            }

            const params = this.queryParams();
            const hasParams = params && Object.keys(params).length > 0;

            const ajaxOptions = {
                url: this.endpoint,
                method: hasParams ? 'POST' : 'GET',
                contentType: hasParams ? 'application/json' : undefined,
                data: hasParams ? JSON.stringify(params) : undefined,
                success: (data) => {
                    $(selectElement).empty();
                    const uniqueData = [...new Set(data)];
                    uniqueData.forEach((item) => {
                        if (!this.optionExists(selectElement, item)) {
                            const option = document.createElement('option');
                            option.value = item;
                            option.textContent = item;
                            selectElement.appendChild(option);
                        }
                    });

                    $(selectElement).dropdown('destroy').dropdown({
                        allowAdditions: true,
                        placeholder: `Select ${this.label.toLowerCase()}`,
                        maxSelections: this.isMultiple ? undefined : 1
                    });

                    resolve();
                },
                error: (err) => {
                    console.error(`Failed to fetch data from ${this.endpoint}:`, err);
                    reject(err);
                }
            };

            $.ajax(ajaxOptions);
        });
    }



    optionExists(selectElement, value) {
        return Array.from(selectElement.options).some(option => option.value === value);
    }

    getSelectedValues() {
        const selectElement = document.getElementById(this.dropdownId);
        if (!selectElement) {
            console.error(`Dropdown with ID "${this.dropdownId}" not found.`);
            return [];
        }
        const selectedValues = $(`#${this.dropdownId}`).dropdown('get value');
        return selectedValues ? (Array.isArray(selectedValues) ? selectedValues : [selectedValues]) : [];
    }

    setSelectedValues(values) {
        const selectElement = document.getElementById(this.dropdownId);
        if (!selectElement) {
            console.error(`Dropdown with ID "${this.dropdownId}" not found.`);
            return;
        }

        const valuesArray = Array.isArray(values) ? values : [values];

        valuesArray.forEach(value => {
            if (!this.optionExists(selectElement, value)) {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                selectElement.appendChild(option);
            }
        });

        $(`#${this.dropdownId}`).dropdown('set selected', valuesArray);
    }

    setQueryParams(newParams) {
        this.queryParams = typeof newParams === 'function' ? newParams : () => newParams;
    }
}
