// ==UserScript==
// @name         Family Recipe Author Scraper
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  scrap author names
// @author       You
// @match        http://localhost:4200/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=undefined.localhost
// @grant        none
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