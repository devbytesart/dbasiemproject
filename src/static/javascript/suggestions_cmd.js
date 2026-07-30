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
document: suggestion_cmd
*/

class SuggestionManager {
    constructor(inputElement, suggestionsContainer, endpoint, search_suggestions=false) {
        this.inputElement = inputElement;
        this.suggestionsContainer = suggestionsContainer;
        this.endpoint = endpoint;
        this.currentSelectionIndex = -1;
        this.search_suggestions = search_suggestions;
        this.attachEvents();
    }

    attachEvents() {
        console.log("Activation input, focus...");
        this.inputElement.addEventListener('focus', () => this.fetchSuggestions(true));
        this.inputElement.addEventListener('input', () => this.fetchSuggestions(false));
        this.inputElement.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.inputElement.addEventListener('blur', () => {
            setTimeout(() => this.clearSuggestions(), 200);
        });
    }

fetchSuggestions(showAll = false) {
    const query = this.getInputValue().trim();
    if (!showAll && query.length === 0) {
        this.clearSuggestions();
        return;
    }

    fetch(`${this.endpoint}?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data) {
                this.displaySuggestions(data.suggestions || data);
            }
        })
        .catch(err => {
            console.error("Error fetchSuggestions:", err);
        });
    }

    getInputValue() {
        if (this.inputElement instanceof HTMLInputElement || this.inputElement instanceof HTMLTextAreaElement) {
            return this.inputElement.value;
        } else {
            return this.inputElement.textContent || '';
        }
    }

    insertParameterAtEnd(param) {
        const text = this.getInputValue().trim();
        let newText = text;
        if (!text.endsWith(' ') && !text.endsWith(';') && text.length > 0) {
            newText += ' ';
        }
        if(this.search_suggestions === false)
            newText += `${param}=`;
        else
            newText += " "
        this.setInputValue(newText);
        this.placeCursorAtEnd();
    }

    setInputValue(value) {
        if (this.inputElement instanceof HTMLInputElement || this.inputElement instanceof HTMLTextAreaElement) {
            this.inputElement.value = value;
        } else {
            this.inputElement.textContent = value;
        }
    }

    replaceCommand(commandName) {
        const text = this.getInputValue().trim();
        const lastSemicolon = text.lastIndexOf(';');
        const before = lastSemicolon >= 0 ? text.slice(0, lastSemicolon + 1) + ' ' : '';
        const newText = before + commandName + ' ';
        this.setInputValue(newText);
        this.placeCursorAtEnd();
    }


    placeCursorAtEnd() {
        this.inputElement.focus();
        if (this.inputElement instanceof HTMLInputElement || this.inputElement instanceof HTMLTextAreaElement) {
            const len = this.inputElement.value.length;
            this.inputElement.setSelectionRange(len, len);
        } else {
            const range = document.createRange();
            range.selectNodeContents(this.inputElement);
            range.collapse(false);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }

    displaySuggestions(data) {
        this.suggestionsContainer.innerHTML = '';
        this.currentSelectionIndex = -1;

        const fragment = document.createDocumentFragment();
        let hasContent = false;
        let examples = [];

        if (Array.isArray(data)) {
            data.forEach(cmd => {
                if (cmd.name && cmd.description !== undefined) {
                    if("examples" in cmd) 
                        examples = cmd.examples;
                    const row = this.createCommandRow(cmd.name, cmd.description, examples);
                    row.addEventListener('click', () => {
                        this.replaceCommand(cmd.name);
                        this.clearSuggestions();
                    });
                    fragment.appendChild(row);
                    hasContent = true;
                }
            });
        } else if (data.command && Array.isArray(data.parameters)) {
            const cmd = data.command;
            if("examples" in cmd) 
                examples = cmd.examples;
            fragment.appendChild(this.createCommandRow(cmd.name, cmd.description, examples));
            hasContent = true;

            data.parameters.forEach(param => {
                fragment.appendChild(this.createParamRow(param));
            });
        }

        if (hasContent) {
            this.suggestionsContainer.appendChild(fragment);
            this.suggestionsContainer.classList.remove('hidden');
            this.positionSuggestions();
        } else {
            this.clearSuggestions(); // Cache if nothing
        }
    }

    createCommandRow(name, description, examples=[]) {
        const row = document.createElement('div');
        row.classList.add('suggestion-item', 'command-row');

        const nameEl = document.createElement('div');
        nameEl.classList.add('bold');
        nameEl.textContent = name;

        const descEl = document.createElement('div');
        descEl.innerHTML = (description || '').toString().replace(/\n/g, '<br/>');

        let descHtml = descEl.innerHTML;

        // Normalize examples (handles string, array, or undefined/null)
        const normalizedExamples = Array.isArray(examples)
            ? examples
            : (examples ? [examples] : []);

        // Render examples section ONLY if examples exist
        if (normalizedExamples.length > 0) {
            const examplesList = normalizedExamples
                .map(ex => `<code>${this.escapeHtml(ex)}</code>`)
                .join('<br/>');

            descHtml += `<div class="command-examples"><strong>Examples:</strong><br/>${examplesList}</div>`;
        }

        descEl.innerHTML = descHtml;

        row.appendChild(nameEl);
        row.appendChild(descEl);
        return row;
    }

    createParamRow(param) {
        const row = document.createElement('div');
        row.classList.add('suggestion-item', 'param-row');

        // Column name 
        const nameCol = document.createElement('div');
        nameCol.classList.add('param-name', 'bold');
        nameCol.textContent = param.name;

        // Column type + default value
        const typeCol = document.createElement('div');
        typeCol.classList.add('param-type');
        typeCol.innerHTML = `${param.type}<br/><span>${param.default ?? ''}</span>`;

        // Column description
        const descCol = document.createElement('div');
        descCol.classList.add('param-description');
        descCol.innerHTML = (param.description || '').replace(/\n/g, '<br/>');

        // Standardize example
        const rawExamples = param.examples || param.example;
        const examples = Array.isArray(rawExamples) 
            ? rawExamples 
            : (rawExamples ? [rawExamples] : []);

        // If examples, we add description
        if (examples.length > 0) {
            const examplesList = examples
                .map(ex => `<code>${this.escapeHtml(ex)}</code>`)
                .join(', ');

            descHtml += `<div class="param-examples"><strong>Ex:</strong> ${examplesList}</div>`;
        }

        // Add columns
        row.appendChild(nameCol);
        row.appendChild(typeCol);
        row.appendChild(descCol);

        // Add event click
        row.addEventListener('click', () => {
            this.insertParameterAtEnd(param.name); 
            this.clearSuggestions();                
        });

        return row;
    }

    escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    clearSuggestions() {
        this.suggestionsContainer.innerHTML = '';
        this.suggestionsContainer.classList.add('hidden');
    }

    positionSuggestions() {
        const parentRect = this.inputElement.parentElement.getBoundingClientRect();
        const inputRect = this.inputElement.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;

        this.suggestionsContainer.style.position = 'absolute';
        this.suggestionsContainer.style.top = `${inputRect.bottom + scrollTop}px`;
        this.suggestionsContainer.style.left = `${parentRect.left + window.scrollX}px`;
        this.suggestionsContainer.style.width = `${parentRect.width}px`;
        this.suggestionsContainer.classList.remove('hidden');
    }


    insertSuggestionAtCursor(suggestion) {
        const input = this.inputElement;
        const text = input.value;
        const cursorPos = input.selectionStart;

        // Before and after the cursor
        const before = text.slice(0, cursorPos);
        const after = text.slice(cursorPos);

        // Search if command written (before first space)
        const firstSpaceIndex = before.indexOf(' ');
        if (firstSpaceIndex === -1) {
            const newText = suggestion + after;
            input.value = newText;
            input.setSelectionRange(suggestion.length, suggestion.length);
            input.focus();
            this.clearSuggestions();
            return;
        }

        if(this.search_suggestions === false) {
            // Only for soar commands
            // Else, search incomplete before cursor
            // Search last pair "key=value" before cursor with regex
            // Parameter can be key=, key="val", key='val' or key=partialval (without space)
            const paramRegex = /(\w+=("[^"]*"|'[^']*'|[^\s]*)?)$/;
            const match = before.match(paramRegex);

            if (match) {
                const paramStart = before.lastIndexOf(match[0]);
                const newText = before.slice(0, paramStart) + suggestion + after;
                input.value = newText;
                const newCursor = paramStart + suggestion.length;
                input.setSelectionRange(newCursor, newCursor);
                input.focus();
                this.clearSuggestions();
                return;
            }
        }

        // Else we don't replace anything, we insert at the cursor position 
        const newText = before + suggestion + after;
        input.value = newText;
        input.setSelectionRange(cursorPos + suggestion.length, cursorPos + suggestion.length);
        input.focus();
        this.clearSuggestions();
    }




    getCursorPosition() {
        const sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) return 0;

        const range = sel.getRangeAt(0);
        const preRange = range.cloneRange();
        preRange.selectNodeContents(this.inputElement);
        preRange.setEnd(range.endContainer, range.endOffset);
        return preRange.toString().length;
    }

    placeCursorAt(pos) {
        const setPos = (el, chars) => {
            for (let node of el.childNodes) {
                if (node.nodeType === 3) { 
                    if (node.length >= chars) {
                        const range = document.createRange();
                        const sel = window.getSelection();
                        range.setStart(node, chars);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                        return -1; 
                    } else {
                        chars -= node.length;
                    }
                } else {
                    chars = setPos(node, chars);
                    if (chars < 0) return chars; 
                }
            }
            return chars;
        };
        setPos(this.inputElement, pos);
    }

    handleKeydown(e) {
        if (e.key === 'ArrowDown') {
            this.moveSelection(1);
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            this.moveSelection(-1);
            e.preventDefault();
        } else if (e.key === 'Enter') {
            if (this.selectedIndex >= 0) {
                const item = this.currentSuggestions[this.selectedIndex];
                if (item && item.name) {
                    this.insertCommandAtCursor(item.name);
                    this.clearSuggestions();
                    e.preventDefault();
                }
            }
        } else if (e.key === 'Shift') {
            // Shift only insert selected element (or nothing is none selected)
            if (this.selectedIndex >= 0) {
                const item = this.currentSuggestions[this.selectedIndex];
                if (item && item.name) {
                    this.insertCommandAtCursor(item.name);
                    this.clearSuggestions();
                    e.preventDefault();
                }
            }
        }
    }

    updateSelection(items) {
        items.forEach((item, index) => {
            item.classList.toggle('selected', index === this.currentSelectionIndex);
            if (index === this.currentSelectionIndex) {
                item.scrollIntoView({ block: 'nearest' });
            }
        });
    }
}
