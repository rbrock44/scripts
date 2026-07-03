// ==UserScript==
// @name         Family Recipe Author Scraper
// @namespace    https://github.com/rbrock44/scripts
// @version      0.1.1
// @description  scrap author names
// @author       Rbrock44
// @match        http://localhost:4200/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=undefined.localhost
// @grant        none
// @license      MIT
// @supportURL   https://github.com/rbrock44/scripts/issues
// @homepageURL  https://github.com/rbrock44/scripts/tree/master/tampermonkey
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/family-recipe-author-scraper.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/family-recipe-author-scraper.user.js
// ==/UserScript==

(function() {
    'use strict';
    var button = document. createElement("button");
    button.innerHTML = 'Authors';

    var body = document.querySelector("h1");
    body.appendChild(button);

    button.addEventListener ("click", function() {
        const rows = document.querySelectorAll('.mat-row');
        const authors = new Set();

        rows.forEach(row => {
        const cell = row.querySelector('mat-cell.mat-column-author').innerHTML;
           authors.add(cell);
        });

        const msg = new Array(...authors).sort().join('\n');

        console.log(msg);
    });
    // Your code here...
})();