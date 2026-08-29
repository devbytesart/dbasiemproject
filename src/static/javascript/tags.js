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
document: tags
*/

class TagInputList {
    constructor(label, endpoint, targetId, isMultiple = true, queryParams = {}, method = 'POST', enable = false) {
        this.label = label;
        this.endpoint = endpoint;
        this.targetId = targetId;
        this.isMultiple = isMultiple;
        this.method = method;
        this.queryParams = typeof queryParams === 'function' ? queryParams : () => queryParams;
        this.tags = [];
        this.suggestions = [];
        this.inputId = `${this.targetId}_tag_input`;
        this.containerId = `${this.targetId}_tag_container`;
        this.dropdownId = `${this.targetId}_suggestions`;
        this.isEnabled = enable;
        this.default_enabled = enable;
        this.init();
    }

    async init() {
        this.createInputHTML();
        await this.loadData();
    }

    createInputHTML() {
        const container = document.getElementById(this.targetId);
        if (!container) {
            console.error(`Container with ID "${this.targetId}" not found.`);
            return;
        }

        const label = document.createElement('label');
        label.textContent = this.label;

        const wrapper = document.createElement('div');
        wrapper.id = this.containerId;
        wrapper.className = 'tag-container';
        wrapper.style = 'display:flex;flex-wrap:wrap;gap:5px;border:1px solid #ccc;padding:5px;width:100%;border-radius:5px;position:relative;';

        const input = document.createElement('input');
        input.type = 'text';
        input.id = this.inputId;
        input.placeholder = 'Add an item...';
        input.style = 'border:none;outline:none;flex:1;padding:4px;font-size:14px;background:transparent;';


        input.addEventListener('focus', () => {
             if (!this.isEnabled) return;
             this.updateSuggestions('');
        });
        input.addEventListener('input', () => {
             if (!this.isEnabled) return;
             this.updateSuggestions(input.value);
        });
        input.addEventListener('keydown', (e) => {
            if (!this.isEnabled) return;
            if (e.key === 'Enter' && input.value.trim()) {
                e.preventDefault();
                const val = input.value.trim();
                if (this.isMultiple || this.tags.length === 0) {
                    this.addTag(val);
                    input.value = '';
                    this.hideSuggestions();
                }
            }
        });
        input.addEventListener('blur', () => {
            setTimeout(() => this.hideSuggestions(), 100);
        });

        const dropdown = document.createElement('div');
        dropdown.id = this.dropdownId;
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style = 'position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #ccc;z-index:10;display:none;max-height:150px;overflow:auto;';

        wrapper.appendChild(input);
        wrapper.appendChild(dropdown);
        container.appendChild(label);
        container.appendChild(wrapper);

        this.updateVisualState();
    }

    // Enable component
    enable() {
        if (this.suggestions.length > 1 || this.default_enabled) {
            this.isEnabled = true;
        } else {
            this.isEnabled = false;
        }
        this.updateVisualState();
    }

    // Disable components
    disable() {
        if(!this.default_enabled) {
            this.isEnabled = false;
            this.updateVisualState();
        }
    }

    // Manage style
    updateVisualState() {
        const input = document.getElementById(this.inputId);
        const wrapper = document.getElementById(this.containerId);
        
        if (!input || !wrapper) return;

        if (this.isEnabled) {
            input.disabled = false;
            input.placeholder = 'Add an item...';
            wrapper.style.backgroundColor = '#fff';
            wrapper.style.cursor = 'text';
        } else {
            input.disabled = true;
            input.placeholder = '';
            wrapper.style.backgroundColor = '#f5f5f5'; 
            wrapper.style.cursor = 'not-allowed';
            this.hideSuggestions();
        }


        this.renderTags();
    }        

    async loadData() {
        const params = this.queryParams();
        const method = this.method.toUpperCase();
        if(this.endpoint) {
            const url = new URL(this.endpoint, window.location.origin);

            if (method === 'GET') {
                Object.entries(params).forEach(([key, value]) => {
                    url.searchParams.append(key, value);
                });
            }

            try {
                const res = await fetch(url.toString(), {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: method === 'GET' ? undefined : JSON.stringify(params)
                });

                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }

                const contentType = res.headers.get("content-type") || "";
                if (!contentType.includes("application/json")) {
                    const text = await res.text();
                    throw new Error(`Non-JSON response: ${text}`);
                }

                const data = await res.json();

                if (!Array.isArray(data)) {
                    throw new Error(`Expected array, got: ${JSON.stringify(data)}`);
                }

                this.suggestions = [...new Set(data)];

                if (this.suggestions.length === 1) {
                    // Only one element -> Default tag selected and component blocked
                    this.addTag(this.suggestions[0]);
                    this.disable();
                } else if (this.suggestions.length > 1) {
                    // Several elements -> Enable component and aply url is present
                    this.applyDefaultSelection();
                    this.enable();
                } else {
                    // None element -> disable
                    this.disable();
                }

            } catch (err) {
                console.error(`Failed to fetch from ${this.endpoint}:`, err);
            }
        }
        else {
            this.suggestions = [];
        }
    }


    applyDefaultSelection() {
        const urlParams = new URLSearchParams(window.location.search);
        const keywordValue = urlParams.get(this.targetId);

        if (keywordValue) {
            // If value is in suggestions, select it. If not, add manually.
            this.addTag(keywordValue);
        } else if (this.suggestions.length > 0) {
            // Select first item by default
            this.addTag(this.suggestions[0]);
        }
    }

    updateSuggestions(query) {
        const dropdown = document.getElementById(this.dropdownId);
        dropdown.innerHTML = '';

        // If request is empty, display all suggestions not selected
        const matches = query.trim() === ''
            ? this.suggestions.filter(item => !this.tags.includes(item)).slice(0, 10)
            : this.suggestions
                .filter(item => item.toLowerCase().includes(query.toLowerCase()) && !this.tags.includes(item))
                .slice(0, 10);

        if (matches.length === 0) {
            this.hideSuggestions();
            return;
        }

        matches.forEach(match => {
            const item = document.createElement('div');
            item.textContent = match;
            item.style = 'padding:5px;cursor:pointer;';
            item.onmouseover = () => item.style.background = '#eee';
            item.onmouseout = () => item.style.background = '';
            item.onclick = () => {
                this.addTag(match);
                document.getElementById(this.inputId).value = '';
                this.hideSuggestions();
            };
            dropdown.appendChild(item);
        });

        dropdown.style.display = 'block';
    }


    hideSuggestions() {
        const dropdown = document.getElementById(this.dropdownId);
        if (dropdown) dropdown.style.display = 'none';
    }

    addTag(value) {
        if (!value || this.tags.includes(value)) return;
        if (!this.isMultiple) this.clearTags();

        this.tags.push(value);
        this.renderTags();
        this.notifyChange();
    }

    renderTags() {
        const container = document.getElementById(this.containerId);
        const input = document.getElementById(this.inputId);
        if (!container || !input) return;

        // Cleaning
        const existingTags = container.querySelectorAll('.tag');
        existingTags.forEach(tag => tag.remove());

        // 2. Rebuilt
        this.tags.forEach((tagText, index) => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = tagText;
            
            if (this.isEnabled) {
                // --- MODE ACTIF ---
                tag.style = 'background:var(--background-header-color, #007bff);color:white;padding:4px 8px;border-radius:20px;font-size:14px;display:flex;align-items:center;';
                
                // Create "x" button only if active
                const removeBtn = document.createElement('button');
                removeBtn.textContent = '×';
                removeBtn.style = 'background:none;border:none;color:white;margin-left:5px;cursor:pointer;font-weight:bold;font-size:16px;line-height:1;padding:0;';
                
                removeBtn.onclick = (e) => {
                    e.stopPropagation();
                    this.tags.splice(index, 1);
                    this.renderTags();
                    if (typeof this.notifyChange === 'function') this.notifyChange();
                };
                
                tag.appendChild(removeBtn);
            } else {
                // Block mode
                tag.style = 'background:#e0e0e0;color:#757575;padding:4px 8px;border-radius:20px;font-size:14px;display:flex;align-items:center;cursor:not-allowed;pointer-events:none;border:1px solid #ccc;';
            }

            container.insertBefore(tag, input);
        });
    }

    clearTags() {
        this.tags = [];
        this.renderTags();
    }

    getSelectedValues() {
        return [...this.tags];
    }

    setSelectedValues(values) {
        this.tags = Array.isArray(values) ? values : [values];
        this.renderTags();
        if(!this.isEnabled) {
            this.disable()
        }
    }

    setQueryParams(newParams) {
        this.queryParams = typeof newParams === 'function' ? newParams : () => newParams;
    }

    onChange(callback) {
        this._onChangeCallback = callback;
    }

    notifyChange() {
        if (typeof this._onChangeCallback === 'function') {
            this._onChangeCallback(this.getSelectedValues());
        }
    }
}












class TagsSystem {
    /*
        JSON DATA FORMAT:
        [{  
            "name": "Index", 
            "id": "selectindex", // id of the html component
            "paramUrl": "index", // Key url parameter
            "url": "/search_available_tenant", 
            "params": {},
            "method": "GET", 
            "multiple": false, 
            "last": false, // if true, wait all others before loading
        }, {...} ]
    */
    constructor(json_data, callback, page_id) {
        this.urlParams = new URLSearchParams(window.location.search);
        this.tags = {};
        this.tagsConfig = json_data;
        this.callback = callback;
        this.page_id = page_id;
        this.last = null;
        this.array = false;

        json_data.forEach(tag => {
            // Create component TagInputList
            const enable = tag.enable ?? false;
            this.tags[tag.name] = new TagInputList(
                tag.name, 
                tag.url, 
                tag.id, 
                tag.multiple, 
                tag.params, 
                tag.method,
                enable
            );

            // Save if last one
            if (tag.last) {
                this.last = this.tags[tag.name];
            }

            // Get existing URL parameter
            var paramValue = this.urlParams.get(tag.paramUrl);

            if (paramValue) {
                this.tags[tag.name].setSelectedValues(paramValue);
            }
        });
    }

    getSelectedValue(name) {
        return this.tags[name].getSelectedValues()[0] || "";
    }

    getSelectedValues(name) {
        return this.tags[name].getSelectedValues() || [];
    }

    updateURLParam(key, value) {
        const url = new URL(window.location);
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        window.history.replaceState({}, '', url);
    }

    init() {
        const promises = [];

        this.tagsConfig.forEach(cfg => {
            const input = this.tags[cfg.name];
            const paramValue = this.urlParams.get(cfg.paramUrl);

            if (!cfg.last) {
                if (!paramValue) {
                    promises.push(
                        input.loadData().then(() => {
                            if (input.suggestions.length > 0) {
                                input.setSelectedValues(input.suggestions[0]);
                            }
                        })
                    );
                }
            }
        });

        // Load the "last" after others
        Promise.all(promises).then(() => {
            if (this.last) {
                const cfg = this.tagsConfig.find(c => c.last);
                const input = this.last;
                const paramValue = this.urlParams.get(cfg.paramUrl);

                if (!paramValue) {
                    input.loadData().then(() => {
                        if (input.suggestions.length > 0) {
                            input.setSelectedValues(input.suggestions[0]);
                        }
                    });
                }
            }
        });

        // Add loading listeners
        this.tagsConfig.forEach(cfg => {
            const input = this.tags[cfg.name];
            input.onChange(values => {
                this.updateURLParam(cfg.paramUrl, values[0] || '');

                if (cfg.last) {
                    // refresh
                    if (this.callback) this.callback();
                } else {
                    // Refresh the "last" based on others
                    this.onChangeUpdateLast();
                }
            });
        });
    }

    onChangeUpdateLast() {
        if (!this.last) return;

        const params = {};
        
        this.tagsConfig.forEach(cfg => {
            if (!cfg.last) {
                params[cfg.paramUrl] = this.tags[cfg.name].getSelectedValues()[0] || "";
            }
        });

        params["page_id"] = this.page_id;

        console.log("onChangeUpdateLast:");
        console.log(params);

        this.last.setQueryParams(() => ({ params }));

        this.last.loadData().then(() => {
            console.log("Input.suggestions", this.last.suggestions);
        });
    }
}
