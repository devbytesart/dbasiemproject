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
document: soarcard
*/

class SOARCard {
    constructor(entry, result_only=false) {
        this.entry = entry;
        this.originalId = entry.id;
        this.dragOverCount = 0;
        this.cardElement = this.createCard(result_only);
        this.cardElement.__instance = this;
    }

    getAnswerBackground() {
        switch (this.entry.status) {
            case 'success': return 'var(--answer-color-success)';
            case 'failed': return 'var(--answer-color-failure)';
            case 'pending': return 'var(--answer-color-in-progress)';
            default: return 'var(--answer-bg)';
        }
    }

    createParamsBlock() {
        const wrapper = document.createElement('div');
        wrapper.className = 'params-block';
        wrapper.style.marginTop = '8px';

        const button = document.createElement('button');
        button.className = 'ui button collapsible';
        button.textContent = 'Parameters';
        button.style.marginBottom = '8px';

        const collapsible = document.createElement('div');
        collapsible.className = 'ui segment collapsed-content';
        collapsible.style.display = 'none';

        for (const [key, value] of Object.entries(this.entry.params || {})) {
            const row = document.createElement('div');
            row.style.display = 'flex';
            row.style.alignItems = 'center';
            row.style.marginBottom = '6px';
            row.style.gap = '6px';

            const label = document.createElement('label');
            label.textContent = key;
            label.style.width = '120px';

            const input = document.createElement('input');
            input.type = 'text';
            input.value = value;
            input.disabled = true;
            input.className = 'param-input';
            input.dataset.key = key;
            input.style.flex = '1';

            const editBtn = document.createElement('button');
            editBtn.title = 'Edit value';
            editBtn.textContent = '✏️';
            editBtn.onclick = () => {
                input.disabled = !input.disabled;
                if (!input.disabled) input.focus();
            };

            row.appendChild(label);
            row.appendChild(input);
            row.appendChild(editBtn);
            collapsible.appendChild(row);
        }

        wrapper.appendChild(button);
        wrapper.appendChild(collapsible);

        button.addEventListener('click', () => {
            $(collapsible).slideToggle();
        });

        return wrapper;
    }


    createAnswerBlock(result_only = false) {
        console.log("CreateAnswerblock");
        console.log(this);
        console.log(this.entry.params.instance);
        const wrapper = document.createElement('div');
        wrapper.className = 'answer-block';

        // Create the bloc of content for the answer
        const answerContent = document.createElement('div');
        const uniqueAnswerId = `answer-${this.entry.id || Math.random().toString(36).substr(2, 8)}`;
        answerContent.id = uniqueAnswerId;
        answerContent.style.whiteSpace = 'normal';

        if (result_only) {
            // Minimal mode: only result
            wrapper.style.all = 'unset'; // Reset applied style
            wrapper.appendChild(answerContent);
        } else {
            // Full mode with background, button and copy
            const bgColor = this.getAnswerBackground();
            wrapper.style.backgroundColor = bgColor;
            wrapper.style.padding = '10px';
            wrapper.style.borderRadius = '6px';
            wrapper.style.marginTop = '8px';
            wrapper.style.position = 'relative';

            const button = document.createElement('button');
            button.className = 'ui button collapsible';
            button.textContent = 'Answer';
            button.style.marginBottom = '8px';

            const collapsible = document.createElement('div');
            collapsible.className = 'ui segment collapsed-content';
            collapsible.style.display = 'block';
            collapsible.appendChild(answerContent);

            const copyBtn = document.createElement('button');
            copyBtn.textContent = '📋';
            copyBtn.title = 'Copy answer';
            copyBtn.style.position = 'absolute';
            copyBtn.style.top = '10px';
            copyBtn.style.right = '10px';
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(answerContent.textContent);
            };

            wrapper.appendChild(button);
            wrapper.appendChild(collapsible);
            wrapper.appendChild(copyBtn);

            button.addEventListener('click', () => {
                $(collapsible).slideToggle();
            });
        }

        // Interpret and display the content of the answer
        new ResultInterpreter(
            this.entry.answer,
            uniqueAnswerId,
            this.flaskEndpoint || null,
            this.pageId || null,
            this.entry.params.instance || null
        );

        return wrapper;
    }



    createCard(result_only = false) {
        const card = document.createElement('div');
        card.classList.add('result-card');
        card.setAttribute('draggable', 'true');
        card.setAttribute('data-id', this.entry.id);

        if (!result_only) {
            const cardId = `cmd-id-${this.entry.id}`;

            card.innerHTML = `
                <div class="result-header">
                    <div><strong>ID:</strong>
                        <input type="number" id="${cardId}" value="${this.entry.id}" style="width:30px;"/>
                    </div>
                    <div><strong>Author:</strong> ${this.entry.author}</div>
                    <div><strong>Date:</strong> ${this.entry.date}</div>
                </div>
                <div class="result-body">
                    <div class="command-block">
                        <strong>Command:</strong>
                        <input contenteditable="true" class="command-line" type="text" id="cmd-input-${this.entry.id}" value="${this.escapeHTML(this.normalizeArrayStrings(this.entry.command))}" disabled style="width: 60%;">
                        <div class="command-buttons" style="display: inline-flex; gap: 8px; margin-left: 10px;">
                            <button onclick="copyToClipboard('cmd-input-${this.entry.id}')" title="Copy Command">📋</button>
                            <button onclick="this.closest('.result-card').__instance.editCommand()" title="Edit">✏️</button>
                            <button onclick="this.closest('.result-card').__instance.replayCommandFromCard()" title="Play Edited">▶️</button>
                            <button onclick="replayCommand(${this.entry.id})" title="Replay">🔁</button>
                            <button onclick="eraseContext(${this.entry.id})" title="Erase">🗑️</button>
                        </div>
                    </div>
                </div>
            `;

            const idInput = card.querySelector(`#${cardId}`);
            idInput.addEventListener('change', () => {
                const newId = parseInt(idInput.value, 10);
                if (!isNaN(newId) && newId !== this.originalId) {
                    replayCommand(null, `soar_set_id id=${this.originalId} new_id=${newId}`, false);
                    this.entry.id = newId;
                    this.originalId = newId;
                    card.setAttribute('data-id', newId);
                }
            });

            const body = card.querySelector('.result-body');
            body.appendChild(this.createParamsBlock());
            body.appendChild(this.createAnswerBlock());
        }
        else {
            // Mode "result only"
            const body = document.createElement('div');
            body.classList.add('result-body');
            body.appendChild(this.createAnswerBlock(result_only));
            card.appendChild(body);
        }

        this.attachDragEvents(card);
        //try launch initSuggestions.
        try {
            if(!result_only) {
                initSuggestions();
            }
        }
        catch (error) {
            console.error("Error initializing suggestions:", error);
        }
        return card;
    }

    escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    unescapeHTML(str) {
        return str
            .replace(/&quot;/g, '"')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');
    }

    editCommand() {
        const input = document.getElementById(`cmd-input-${this.entry.id}`);
        if (!input) return;

        input.disabled = !input.disabled;

        if (!input.disabled) {
            input.focus();

            // Create container if does not exists
            let suggestionsContainer = document.querySelector(`#suggestions-${this.entry.id}`);
            if (!suggestionsContainer) {
                suggestionsContainer = document.createElement('div');
                suggestionsContainer.className = 'suggestions hidden';
                suggestionsContainer.id = `suggestions-${this.entry.id}`;
                document.body.appendChild(suggestionsContainer);
            }

            // Clean the previous manager if exists
            if (input._suggestionManager) {
                input._suggestionManager.clearSuggestions();
            }

            // Attach a new one (redo listener)
            input._suggestionManager = new SuggestionManager(input, suggestionsContainer, '/command_suggestions');

            // Force the first researches if already text
            input.dispatchEvent(new Event('input'));

        } else {
            // If disabled, treat the command 
            const cmdString = this.unescapeHTML(this.normalizeArrayStrings(input.value.trim()));

            const [name, ...rest] = cmdString.split(' ');

            const params = {};
            const paramRegex = /(\w+)=(".*?"|'.*?')/g;
            let match;
            while ((match = paramRegex.exec(cmdString)) !== null) {
                const [, key, value] = match;
                params[key] = value;
            }

            this.entry.name = name;
            this.entry.command = cmdString;
            this.entry.params = params;

            // Update the display 
            const body = this.cardElement.querySelector('.result-body');
            const oldParamsBlock = body.querySelector('.params-block');
            if (oldParamsBlock) oldParamsBlock.remove();
            body.insertBefore(this.createParamsBlock(), this.cardElement.querySelector('.answer-block'));

            // Delete suggestions
            if (input._suggestionManager) {
                input._suggestionManager.clearSuggestions();
            }
        }
    }


    normalizeArrayStrings(text) {
        return text.replace(/\['.*?'\]/g, match => {
            try {
                // Converts single quotes to double for json parsing 
                const arr = JSON.parse(match.replace(/'/g, '"'));
                if (Array.isArray(arr)) {
                    return arr.join(', ');
                }
            } catch (e) {
                // If problem, do not touch
            }
            return match;
        });
    }

    replayCommandFromCard() {
        const card = this.cardElement;
        const paramInputs = card.querySelectorAll('input.param-input');
        const paramList = [];

        paramInputs.forEach(input => {
            const key = input.dataset.key;
            const value = input.value.trim();
            if (key && value !== '') {
                paramList.push(`${key}=${value}`);
            }
        });

        const fullCommand = `${this.entry.name} ${paramList.join(' ')}`;
        replayCommand(this.entry.id, fullCommand);
    }

    attachDragEvents(card) {
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', this.entry.id);
            card.classList.add('dragging-source');
        });

        card.addEventListener('dragend', () => {
            document.querySelectorAll('.result-card').forEach(c => {
                c.classList.remove('dragging-source', 'drag-target');
            });
        });

        card.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (!card.classList.contains('dragging-source')) {
                card.classList.add('drag-target');
            }
        });

        card.addEventListener('dragenter', () => {
            this.dragOverCount++;
        });

        card.addEventListener('dragleave', () => {
            this.dragOverCount--;
            if (this.dragOverCount <= 0) {
                card.classList.remove('drag-target');
            }
        });

        card.addEventListener('drop', (e) => {
            e.preventDefault();
            const originId = e.dataTransfer.getData('text/plain');
            const finalId = this.entry.id;

            document.querySelectorAll('.result-card').forEach(c => {
                c.classList.remove('dragging-source', 'drag-target');
            });

            if (originId !== finalId.toString()) {
                swap_ids(originId, finalId);
            }
        });
    }

    render() {
        return this.cardElement;
    }
}

