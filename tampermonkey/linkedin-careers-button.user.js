// ==UserScript==
// @name         LinkedIn Careers Button Injector
// @namespace    https://github.com/rbrock44/scripts
// @version      1.2.1
// @description  Add a "${Company Name} Careers" button to job postings
// @author       Rbrock44
// @match        *://*.linkedin.com/jobs/view/*
// @match        https://www.linkedin.com/jobs/view/*
// @match        https://linkedin.com/jobs/view/*
// @match        *linkedin.com/jobs/view*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=linkedin.com
// @grant        none
// @run-at       document-end
// @license      MIT
// @supportURL   https://github.com/rbrock44/scripts/issues
// @homepageURL  https://github.com/rbrock44/scripts/tree/master/tampermonkey
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/linkedin-careers-button.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/linkedin-careers-button.user.js
// ==/UserScript==

(function () {
    'use strict';
    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 500;

    function createButton(companyName) {
        const button = document.createElement('button');
        button.textContent = `Go To careers`;
        button.style.backgroundColor = '#0073b1'; // LinkedIn blue
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '20px';
        button.style.padding = '10px 16px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.style.marginTop = '12px';
        button.style.marginLeft = '12px';
        button.style.display = 'block';

        button.addEventListener('click', () => {
            const query = encodeURIComponent(`${companyName} careers`);
            window.open(`https://www.google.com/search?q=${query}`, '_blank');
        });

        return button;
    }

    function tryInject(retriesLeft) {
        const saveButtons = document.querySelectorAll('.jobs-save-button');
        // 7th a tag
        const companyLink = document.querySelectorAll('a')[9];

        if (saveButtons.length >= 2 && companyLink && companyLink.textContent.trim()) {
            const companyName = companyLink.textContent.trim();

            // Check if button already exists
            if (document.getElementById('careers-button')) return;

            const button = createButton(companyName);
            button.id = 'careers-button';

            saveButtons[1].parentElement.appendChild(button);
            console.log('Career button injected after second save button!');
        } else if (retriesLeft > 0) {
            console.log('Retying: retries lefft: ', retriesLeft);
            setTimeout(() => tryInject(retriesLeft - 1), RETRY_INTERVAL_MS);
        }
    }

    setTimeout(() => tryInject(MAX_RETRIES), 5000);
})();
