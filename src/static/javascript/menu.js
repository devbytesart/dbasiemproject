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
document: menu
*/


document.addEventListener('DOMContentLoaded', function() {

    const root = document.documentElement;

    // Image paths
    const IMG_FIRST = '/static/media/first.png';       // <<
    const IMG_PREVIOUS = '/static/media/previous.png'; // <
    const IMG_NEXT = '/static/media/next.png';         // >
    const IMG_LAST = '/static/media/last.png';         // >>

    // Helper function to update the image source inside a button
    function updateButtonImage(btnElement, imageSrc) {
        const img = btnElement.querySelector('img');
        if (img) {
            img.src = imageSrc;
        }
    }

    // --- 1. Left Menu Management ---
    const menuBtn = document.getElementById('toggle-menu-btn');
    const leftMenu = document.getElementById('menu');
    const rightMenu = document.getElementById('menu-right');
    let isMenuCollapsed = false;

    menuBtn.addEventListener('click', () => {
        isMenuCollapsed = !isMenuCollapsed;
        
        if (isMenuCollapsed) {
            root.style.setProperty('--left-width', '50px');
            leftMenu.classList.add('collapsed'); // Hide all menu contents except the toggle button
            updateButtonImage(menuBtn, IMG_NEXT); // > (Expand)
        } else {
            root.style.setProperty('--left-width', '250px');
            leftMenu.classList.remove('collapsed'); // Show all menu contents
            updateButtonImage(menuBtn, IMG_PREVIOUS); // < (Collapse)
        }
    });


    // --- 2. Right Config Panel Management ---
    const collapseConfigBtn = document.getElementById('collapse-config-btn');
    const expandConfigBtn = document.getElementById('expand-config-btn');

    let isConfigCollapsed = false;
    let isConfigExpanded = false;

    // Collapse / Restore the right panel
    collapseConfigBtn.addEventListener('click', () => {
        isConfigCollapsed = !isConfigCollapsed;
        
        if (isConfigCollapsed) {
            root.style.setProperty('--right-width', '50px');
            updateButtonImage(collapseConfigBtn, IMG_PREVIOUS); // < (Restore to normal)
            rightMenu.classList.add('collapsed'); // Hide all menu contents except the toggle button
            expandConfigBtn.style.display = 'none'; // Hide expand button when collapsed to 0
        } else {
            root.style.setProperty('--right-width', '250px');
            updateButtonImage(collapseConfigBtn, IMG_NEXT); // > (Collapse to min)
            expandConfigBtn.style.display = 'inline-block';
            rightMenu.classList.remove('collapsed'); // Show all menu contents
            isConfigExpanded = false;
            updateButtonImage(expandConfigBtn, IMG_FIRST); // << (Expand menu)
        }
    });

    // Expand (Overlay) / Restore the right panel
    expandConfigBtn.addEventListener('click', () => {
        isConfigExpanded = !isConfigExpanded;
        
        if (isConfigExpanded) {
            // Covers the entire central area to the right of the left menu
            root.style.setProperty('--right-width', 'calc(100% - var(--left-width))');
            updateButtonImage(expandConfigBtn, IMG_LAST); // >> (Restore to normal)
            collapseConfigBtn.style.display = 'none';
        } else {
            // Reset to standard size
            root.style.setProperty('--right-width', '250px');
            updateButtonImage(expandConfigBtn, IMG_FIRST); // << (Expand to max)
            collapseConfigBtn.style.display = 'inline-block';
        }
    });

});

// document.addEventListener('DOMContentLoaded', function() {

// const root = document.documentElement;

// // --- 1. Gestion du Menu (Gauche) ---
// const menuBtn = document.getElementById('toggle-menu-btn');
// let isMenuCollapsed = false;

// menuBtn.addEventListener('click', () => {
//     isMenuCollapsed = !isMenuCollapsed;
    
//     if (isMenuCollapsed) {
//         root.style.setProperty('--left-width', '50px');
//         menuBtn.textContent = '>'; // Devient "Agrandir"
//     } else {
//         root.style.setProperty('--left-width', '250px');
//         menuBtn.textContent = '<'; // Devient "Réduire"
//     }
// });


// // --- 2. Gestion de la Config (Droite) ---
// const collapseConfigBtn = document.getElementById('collapse-config-btn');
// const expandConfigBtn = document.getElementById('expand-config-btn');

// let isConfigCollapsed = false;
// let isConfigExpanded = false;

// // Réduire / Restaurer la zone de droite
// collapseConfigBtn.addEventListener('click', () => {
//     isConfigCollapsed = !isConfigCollapsed;
    
//     if (isConfigCollapsed) {
//         root.style.setProperty('--right-width', '0px');
//         collapseConfigBtn.textContent = '<'; // Devient "Ouvrir"
//         expandConfigBtn.style.display = 'none'; // Cache le bouton d'agrandissement quand réduit à 0
//     } else {
//         root.style.setProperty('--right-width', '250px');
//         collapseConfigBtn.textContent = '>'; // Devient "Réduire"
//         expandConfigBtn.style.display = 'inline-block';
//         isConfigExpanded = false;
//         expandConfigBtn.textContent = '<<';
//     }
// });

// // Agrandir (Recouvrir) / Restaurer la zone de droite
// expandConfigBtn.addEventListener('click', () => {
//     isConfigExpanded = !isConfigExpanded;
    
//     if (isConfigExpanded) {
//         // Recouvre tout l'espace central à droite du menu
//         root.style.setProperty('--right-width', 'calc(100% - var(--left-width))');
//         expandConfigBtn.textContent = '>>'; // Devient "Restaurer"
//         collapseConfigBtn.style.display = 'none';
//     } else {
//         // Remet la taille standard
//         root.style.setProperty('--right-width', '250px');
//         expandConfigBtn.textContent = '<<'; // Devient "Agrandir au max"
//         collapseConfigBtn.style.display = 'inline-block';
//     }
// });
    


// });