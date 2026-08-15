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
document: suggestion
*/

document.addEventListener('DOMContentLoaded', function() {
    const searchQuery = document.getElementById('searchQuery') || document.getElementById('commandQuery');
    const suggestionsContainer = document.getElementById('suggestions');

    if (!searchQuery) {
        console.warn('None field found with  "searchQuery" or "commandQuery".');
        return;
    }

    // Determine URL in function of current element
    const endpoint = searchQuery.id === 'searchQuery' ? '/get_suggestions' : '/command_suggestions';

    // Function to display suggestions
    function displaySuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            console.log("suggestion:" + suggestion);
            const suggestionItem = document.createElement('div');
            suggestionItem.classList.add('suggestion-item');
            suggestionItem.textContent = suggestion;
            suggestionsContainer.appendChild(suggestionItem);

            // Add color red if parameter is required
            if (suggestion.required) {
                suggestionItem.innerHTML = `<span style="color: red;">${suggestion.name}*</span> - ${suggestion.description}`;
            } else {
                suggestionItem.textContent = `${suggestion.name} - ${suggestion.description}`;
            }

            // Add event on click to complete the suggestion
            suggestionItem.addEventListener('click', () => {
                searchQuery.textContent = suggestion; // Replace the text by the selection
                suggestionsContainer.innerHTML = ''; // Empty suggestion
            });
        });
    }

    // Add event listener when user is writting on the search bar
    searchQuery.addEventListener('input', function() {
        const query = searchQuery.textContent.trim();

        if (query.length > 0) {
            fetch(`${endpoint}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.suggestions) {
                        displaySuggestions(data.suggestions);
                    }
                });
        } else {
            suggestionsContainer.innerHTML = ''; // Empty suggestion if empty
        }
    });

    // Manage focus : hide suggestions when search bar lost focus
    searchQuery.addEventListener('blur', function() {
        setTimeout(() => {
            suggestionsContainer.innerHTML = ''; 
            
            // Wait before hiding to avoid conflicts with click on suggestions 
        }, 200);
    });
});
