// ==UserScript==
// @name         TCDB Price Highlighter
// @namespace    https://github.com/rbrock44/scripts
// @version      1.0.1
// @description  Highlights rows with price >= $0.98 on TCDB Prices pages
// @author       Rbrock44
// @match        https://www.tcdb.com/Prices.cfm/sid/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tcdb.com
// @grant        none
// @license      MIT
// @supportURL   https://github.com/rbrock44/scripts/issues
// @homepageURL  https://github.com/rbrock44/scripts/tree/master/tampermonkey
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/trading-card-database-highlight-over-1-dollar.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/trading-card-database-highlight-over-1-dollar.user.js
// ==/UserScript==

(function() {
    'use strict';

    // Wait for table to load
    function highlightRows() {
        // Select all table rows
        const rows = document.querySelectorAll('tr');

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 0) return; // skip rows without TDs

            const lastCell = cells[cells.length - 1];
            if (!lastCell) return;

            const text = lastCell.textContent.trim();
            // Remove $ and commas, parse float
            const numericValue = parseFloat(text.replace(/[\$,]/g, ''));

            if (!isNaN(numericValue) && numericValue >= 0.98) {
                row.style.backgroundColor = 'yellow';
            }
        });
    }

    // Run immediately
    highlightRows();

    // Also re-run after possible AJAX updates
    new MutationObserver(highlightRows).observe(document.body, { childList: true, subtree: true });

})();
