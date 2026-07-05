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
document: datetime picker
*/

class DateTimePicker extends HTMLElement {
    static get observedAttributes() {
        // Observe changes on attributes "name" and "id"
        return ['name', 'id'];
    }

    constructor() {
        super();

        // Creation of shadow DOM
        // Création du Shadow DOM
        this.attachShadow({ mode: 'open' });

        // Initial template HTML
        this.shadowRoot.innerHTML = `
            <link rel="stylesheet" href="static/css/datetimepicker.css">
            <div class="date-time-picker">
                <div class="header">
                    <h3 id="title"></h3>
                    <button id="toggle" aria-label="Toggle picker">
                        <i>&#128275;</i>
                    </button>
                </div>

                <input type="datetime-local" id="datetime-input">

                <div class="number-preset">
                    <input type="number" id="number-input" placeholder="Enter number" min="0">
                    <select id="preset-select">
                        <option value="">Choose Preset</option>
                        <option value="minutes">Minutes</option>
                        <option value="hours">Hours</option>
                        <option value="days">Days</option>
                        <option value="weeks">Weeks</option>
                        <option value="months">Months</option>
                        <option value="quarters">Quarters</option>
                        <option value="years">Years</option>
                    </select>
                </div>
            </div>
        `;

        // Store elements to manipulate future
        this.titleElement = this.shadowRoot.querySelector('#title');
        this.dateInput = this.shadowRoot.querySelector('#datetime-input');
        this.numberInput = this.shadowRoot.querySelector('#number-input');
        this.presetSelect = this.shadowRoot.querySelector('#preset-select');
        this.toggleButton = this.shadowRoot.querySelector('#toggle');
    }

    connectedCallback() {
        // Initialisation of title and id
        this.updateAttributes();

        // Add listeners
        this.toggleButton.addEventListener('click', () => this.togglePicker());
        this.dateInput.addEventListener('input', () => this.updateResult());
        this.numberInput.addEventListener('input', () => this.updateResult());
        this.presetSelect.addEventListener('change', () => this.updateResult());
    }

    disconnectedCallback() {
        // Delete listener to avoid memory leak
        this.toggleButton.removeEventListener('click', this.togglePicker);
        this.dateInput.removeEventListener('input', this.updateResult);
        this.numberInput.removeEventListener('input', this.updateResult);
        this.presetSelect.removeEventListener('change', this.updateResult);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        // If an attribute changes, update dynamically
        this.updateAttributes();
    }

    updateAttributes() {
        // Update title and ids dynamically
        const name = this.getAttribute('name') || 'DateTime Picker';
        const id = this.getAttribute('id') || 'dateTime';

        // Update title
        this.titleElement.textContent = name;

        // Update ids (if required for others interactions)
        this.dateInput.id = `${id}_datetime-input`;
        this.numberInput.id = `${id}_number-input`;
        this.presetSelect.id = `${id}_preset-select`;
        this.toggleButton.id = `${id}_toggle`;
    }

    togglePicker() {
        // Disable/ enable all fields
        const isDisabled = this.dateInput.disabled;

        this.dateInput.disabled = !isDisabled;
        this.numberInput.disabled = !isDisabled;
        this.presetSelect.disabled = !isDisabled;

        // Change button icon
        this.toggleButton.innerHTML = isDisabled
            ? `<i>&#128275;</i>` // Icon locker open
            : `<i>&#128274;</i>`; // Icon locker close
    }

    updateResult() {
        // Log or manipualte selected date
        // Log ou manipulation de la date sélectionnée
        console.log(`Selected Date:`, this.getActiveDate());
    }

    getActiveDate() {
        // If calendar is actif, return date
        if (!this.dateInput.disabled && this.dateInput.value) {
            return formatDateToUTC(new Date(this.dateInput.value));
        }

        // If preset and number are actives, compute the relative date
        const number = parseInt(this.numberInput.value, 10);
        const preset = this.presetSelect.value;

        if (!isNaN(number) && preset) {
            const now = new Date();
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

        return null;
    }
}

// Declaration component
customElements.define('date-time-picker', DateTimePicker);
