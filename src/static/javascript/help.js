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
document: help
*/

$(document).ready(function() {
    // Event click icon help 
    $('#helpIcon').on('click', function() {
        // Request AJAX to flask to get help 
        $.ajax({
            url: '/query_help',
            type: 'GET',
            success: function(data) {
                // Display content of help in popup
                $('#helpContent').html(data);
                $('#helpPopup').show();
            },
            error: function() {
                alert('Error during loading help content.');
            }
        });
    });

    $('button.collapsible').off('click').on('click', function(e) {
        console.log("Collapsible button clicked");
        e.preventDefault();
        e.stopPropagation();
        $(this).next('.collapsed-content').slideToggle();
    });

    // Event to close the popup
    $('#closeHelpPopup').on('click', function() {
        console.log("Close help popup clicked");
        $('#helpPopup').hide();
    });

    // Delegate event only from inside the helpContent
    $('#helpContent')
        .off('click', 'button.collapsible')   // Delete old container
        .on('click', 'button.collapsible', function(e) {
            console.log("Collapsible button clicked");
            e.preventDefault();
            e.stopPropagation();
            $(this).next('.collapsed-content').slideToggle();
        });

    // Init highlight syntax
    $('pre code').each(function(i, block) {
        if (hljs.highlightElement) {
            hljs.highlightElement(block); // Current version 
        } else {
            hljs.highlightBlock(block);   // rétro-compatibility
        }
    });
});
